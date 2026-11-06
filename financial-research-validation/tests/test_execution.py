import json
from decimal import Decimal

import pytest

from research_sample.execution import ExecutionCase, State


def opened():
    case = ExecutionCase("demo", "10")
    case.begin_submit()
    case.acknowledge()
    return case


def match(case, state="FILLED", qty="10", **kw):
    return case.reconcile(remote_state=state, remote_position=qty, remote_filled=qty,
                          stop_confirmed=True, stop_quantity=qty, **kw)


def test_successful_order_matches_fills_position_and_protection():
    case = opened()
    case.record_fill("f1", "3", "20", ".30")
    case.record_fill("f2", "7", "21", ".70")
    assert match(case) and case.new_entries_allowed
    assert case.entry_cost == Decimal("208")


def test_timeout_is_not_a_rejection_and_cannot_be_resubmitted():
    case = ExecutionCase("demo", "10")
    case.begin_submit()
    case.timeout()
    with pytest.raises(ValueError):
        case.begin_submit()
    case.record_fill("f1", "10", "20")
    assert case.state == State.UNKNOWN and not case.new_entries_allowed
    assert match(case) and case.state == State.FILLED


def test_duplicate_response_is_idempotent_even_after_later_partial_fill():
    case = ExecutionCase("demo", "10")
    case.begin_submit()
    case.timeout()
    assert case.acknowledge("r1", "remote-1")
    case.record_fill("f1", "3", "20")
    assert not case.acknowledge("r1", "remote-1")
    assert case.state == State.PARTIAL and case.filled == 3


def test_conflicting_response_identity_quarantines_the_case():
    case = opened()
    with pytest.raises(ValueError, match="Response identity"):
        case.acknowledge("ack", "another-order")
    assert "response_identity_conflict" in case.halts


def test_response_identity_survives_restart_without_resetting_state():
    case = opened()
    case.record_fill("f1", "3", "20")
    case = ExecutionCase.restore(json.loads(json.dumps(case.snapshot())))
    assert not case.acknowledge() and case.state == State.PARTIAL


def test_acquisition_cost_distinguishes_principal_from_execution_fees():
    case = opened()
    case.record_fill("f1", "3", "20", ".30")
    case.record_fill("f2", "7", "21", ".70")
    assert case.principal == 207 and case.fees == 1 and case.total_acquisition_cost == 208


def test_an_invalid_new_observation_closes_a_previously_clear_local_gate():
    case = opened()
    case.record_fill("f1", "10", "20")
    assert match(case) and case.new_entries_allowed
    with pytest.raises(ValueError):
        case.reconcile(remote_state="FILLED", remote_position="NaN", remote_filled="10")
    assert not case.new_entries_allowed and "invalid_observation" in case.gate_reasons
    assert match(case) and case.new_entries_allowed


def test_a_string_is_not_an_explicit_protective_stop_confirmation():
    case = opened()
    case.record_fill("f1", "10", "20")
    assert match(case) and case.new_entries_allowed
    with pytest.raises(ValueError):
        case.reconcile(remote_state="FILLED", remote_position="10", remote_filled="10",
                       stop_confirmed="false", stop_quantity="10")
    assert not case.new_entries_allowed and "invalid_observation" in case.gate_reasons


def test_sequential_demo_explains_resolved_and_quarantined_gates():
    from execution_demo import run
    result = run()
    assert result["resolved_case"]["case_entry_gate_clear"]
    assert not result["quarantined_case"]["case_entry_gate_clear"]
    events = result["resolved_case"]["events"]
    assert all("case_entry_gate_clear" in event and "gate_reasons" in event for event in events)
    assert {"response_uncertain", "duplicate_response_ignored", "duplicate_fill_ignored"} <= {
        event["event"] for event in events}


def test_identical_fill_is_idempotent_and_conflicting_fill_blocks():
    case = opened()
    case.record_fill("f1", "3", "20")
    assert not case.record_fill("f1", "3", "20")
    with pytest.raises(ValueError):
        case.record_fill("f1", "4", "20")
    assert case.filled == 3 and "fill_identity_conflict" in case.halts
    assert not match(case, "CANCELLED", "3")


def test_partial_fill_then_cancel_retains_the_filled_position():
    case = opened()
    case.record_fill("f1", "3", "20")
    assert match(case, "CANCELLED", "3")
    assert case.filled == 3 and case.new_entries_allowed


def test_late_fill_during_cancellation_requires_updated_protection():
    case = opened()
    case.record_fill("f1", "3", "20")
    assert match(case, "CANCELLED", "3")
    case.record_fill("f2", "7", "20")
    assert not case.new_entries_allowed
    assert not case.reconcile(remote_state="FILLED", remote_position="10", remote_filled="10",
                              stop_confirmed=True, stop_quantity="3")
    assert match(case)


def test_rejection_keeps_a_persistent_entry_block():
    case = opened()
    assert not match(case, "REJECTED", "0")
    assert "order_rejected" in case.halts and not case.new_entries_allowed


@pytest.mark.parametrize("confirmed,covered", [(False, "10"), (True, "3"), (True, "11")])
def test_missing_under_or_over_sized_stop_blocks_entries(confirmed, covered):
    case = opened()
    case.record_fill("f1", "10", "20")
    assert not case.reconcile(remote_state="FILLED", remote_position="10", remote_filled="10",
                              stop_confirmed=confirmed, stop_quantity=covered)
    assert "protection_unconfirmed" in case.halts and not case.new_entries_allowed
    assert match(case)  # A later verified snapshot resolves the protection issue.


def test_position_and_fill_mismatch_are_separate_checks():
    case = opened()
    case.record_fill("f1", "3", "20")
    assert not case.reconcile(remote_state="OPEN", remote_position="4", remote_filled="5")
    assert {"position_mismatch", "fill_ledger_mismatch"} <= case.halts


def test_open_order_keeps_entry_reservation_even_after_matching_snapshot():
    case = opened()
    assert match(case, "OPEN", "0")
    assert not case.new_entries_allowed


def test_overfill_is_rejected_without_mutating_quantity():
    case = opened()
    with pytest.raises(ValueError):
        case.record_fill("f1", "11", "20")
    assert case.filled == 0 and "invalid_fill" in case.halts


def test_wrong_terminal_state_and_unresolved_response_remain_blocked():
    case = opened()
    case.record_fill("f1", "3", "20")
    assert not match(case, "FILLED", "3")
    assert "order_state_mismatch" in case.halts
    assert not match(case, "UNKNOWN", "3")


def test_restart_preserves_uncertainty_and_fill_idempotency():
    case = opened()
    case.record_fill("f1", "3", "20")
    restored = ExecutionCase.restore(json.loads(json.dumps(case.snapshot())))
    assert not restored.new_entries_allowed
    assert not restored.record_fill("f1", "3", "20")
    assert match(restored, "CANCELLED", "3")


def test_restart_requires_a_new_reconciliation_even_if_previous_snapshot_was_clear():
    case = opened()
    case.record_fill("f1", "10", "20")
    assert match(case) and case.new_entries_allowed
    restored = ExecutionCase.restore(json.loads(json.dumps(case.snapshot())))
    assert not restored.new_entries_allowed
    assert match(restored) and restored.new_entries_allowed


@pytest.mark.parametrize("qty", ["0", "-1", "NaN", "Infinity"])
def test_invalid_order_quantity_rejected(qty):
    with pytest.raises(ValueError):
        ExecutionCase("demo", qty)

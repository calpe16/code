"""Sequential single-order incident exercise, with an explicit local entry gate."""
import json

from research_sample.execution import ExecutionCase


def run():
    case = ExecutionCase("DEMO-ORDER", "10")
    case.begin_submit()
    case.timeout()
    case = ExecutionCase.restore(json.loads(json.dumps(case.snapshot())))
    case.acknowledge("RESPONSE-1", "SIMULATED-ORDER")
    case.acknowledge("RESPONSE-1", "SIMULATED-ORDER")
    case.record_fill("FILL-1", "3", "20", ".30")
    case.record_fill("FILL-1", "3", "20", ".30")
    case.reconcile(remote_state="OPEN", remote_position="4", remote_filled="3",
                   stop_confirmed=True, stop_quantity="1")
    assert "position_mismatch" in case.halts and not case.new_entries_allowed
    case.reconcile(remote_state="OPEN", remote_position="3", remote_filled="3",
                   stop_confirmed=True, stop_quantity="3")
    assert not case.new_entries_allowed  # The remaining open order still reserves the case.
    case.reconcile(remote_state="CANCELLED", remote_position="3", remote_filled="3",
                   stop_confirmed=True, stop_quantity="3")
    assert case.new_entries_allowed
    case.record_fill("FILL-2", "7", "21", ".70")  # A fill raced with cancellation.
    case.reconcile(remote_state="FILLED", remote_position="10", remote_filled="10",
                   stop_confirmed=True, stop_quantity="3")
    assert "protection_unconfirmed" in case.halts
    case.reconcile(remote_state="FILLED", remote_position="10", remote_filled="10",
                   stop_confirmed=True, stop_quantity="10")
    assert case.new_entries_allowed and case.total_acquisition_cost == 208
    quarantined = ExecutionCase("CONFLICT-CASE", "10")
    quarantined.begin_submit()
    quarantined.acknowledge()
    quarantined.record_fill("FILL-CONFLICT", "3", "20")
    try:
        quarantined.record_fill("FILL-CONFLICT", "4", "20")
    except ValueError:
        pass
    quarantined.reconcile(remote_state="CANCELLED", remote_position="3", remote_filled="3",
                           stop_confirmed=True, stop_quantity="3")
    assert not quarantined.new_entries_allowed
    assert "fill_identity_conflict" in quarantined.gate_reasons
    return {"data": "Synthetic demo data", "scope": "Single-order case gate, not portfolio exposure approval",
            "resolved_case": {"state": str(case.state), "position": str(case.filled),
                              "principal_eur": str(case.principal), "fees_eur": str(case.fees),
                              "total_acquisition_cost_eur": str(case.total_acquisition_cost),
                              "case_entry_gate_clear": case.new_entries_allowed, "events": case.audit},
            "quarantined_case": {"case_entry_gate_clear": quarantined.new_entries_allowed,
                                  "reasons": sorted(quarantined.gate_reasons), "events": quarantined.audit}}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

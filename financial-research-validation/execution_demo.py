"""Run a simulated timeout, restart, partial fills and protection checks."""
import json

from research_sample.execution import ExecutionCase


def run():
    order = ExecutionCase("DEMO-ORDER", "10")
    order.begin_submit()
    order.timeout()
    assert not order.new_entries_allowed
    order = ExecutionCase.restore(json.loads(json.dumps(order.snapshot())))
    order.record_fill("DEMO-FILL-1", "3", "20", ".30")
    order.record_fill("DEMO-FILL-1", "3", "20", ".30")
    order.reconcile(remote_state="OPEN", remote_position="3", remote_filled="3")
    unprotected = sorted(order.halts)
    assert "protection_unconfirmed" in unprotected
    order.record_fill("DEMO-FILL-2", "7", "21", ".70")
    matched = order.reconcile(remote_state="FILLED", remote_position="10", remote_filled="10",
                              stop_confirmed=True, stop_quantity="10")
    assert matched and order.new_entries_allowed and order.entry_cost == 208
    return {"data": "Synthetic demo data", "unprotected_halts": unprotected,
            "final_state": str(order.state), "position": str(order.filled),
            "entry_cost": str(order.entry_cost), "new_entries_allowed": order.new_entries_allowed,
            "audit": order.audit}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))

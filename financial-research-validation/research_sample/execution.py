"""Offline order lifecycle model based on the project's OMS control flow.

One long entry in a fictional instrument. All inputs are supplied by the caller.
Copyright 2026 Martin Calpe Blasco. All rights reserved.
"""
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from enum import StrEnum


class State(StrEnum):
    CREATED = "CREATED"
    SENDING = "SENDING"
    UNKNOWN = "UNKNOWN"
    OPEN = "OPEN"
    PARTIAL = "PARTIAL"
    FILLED = "FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


def amount(value, *, positive=False):
    result = Decimal(str(value))
    if not result.is_finite() or result < 0 or (positive and result == 0):
        raise ValueError("Finite nonnegative amounts required; quantity and price must be positive")
    return result


@dataclass(frozen=True)
class Fill:
    id: str
    quantity: Decimal
    price: Decimal
    fee: Decimal


@dataclass
class ExecutionCase:
    client_id: str
    quantity: Decimal
    state: State = State.CREATED
    fills: dict[str, Fill] = field(default_factory=dict)
    persistent_halts: set[str] = field(default_factory=set)
    reconciliation_issues: set[str] = field(default_factory=set)
    reconciled: bool = True
    audit: list[dict] = field(default_factory=list)
    responses: dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        if not self.client_id:
            raise ValueError("Persisted client order identity required")
        self.quantity = amount(self.quantity, positive=True)

    @property
    def filled(self):
        return sum((fill.quantity for fill in self.fills.values()), Decimal(0))

    @property
    def principal(self):
        return sum((fill.quantity * fill.price for fill in self.fills.values()), Decimal(0))

    @property
    def fees(self):
        return sum((fill.fee for fill in self.fills.values()), Decimal(0))

    @property
    def total_acquisition_cost(self):
        return self.principal + self.fees

    @property
    def entry_cost(self):
        """Compatibility alias for total acquisition cost, including principal."""
        return self.total_acquisition_cost

    @property
    def halts(self):
        result = self.persistent_halts | self.reconciliation_issues
        if self.state in {State.SENDING, State.UNKNOWN}:
            result = result | {"order_response_unresolved"}
        return result

    @property
    def new_entries_allowed(self):
        """Local gate for this one-order case, not a portfolio exposure approval."""
        return not self.gate_reasons

    @property
    def gate_reasons(self):
        reasons = self.halts.copy()
        if not self.reconciled:
            reasons.add("fresh_reconciliation_required")
        if self.state in {State.OPEN, State.PARTIAL}:
            reasons.add("open_order_reservation")
        return reasons

    def _event(self, event, **details):
        self.audit.append({"event": event, "state": str(self.state),
                           "case_entry_gate_clear": self.new_entries_allowed,
                           "gate_reasons": sorted(self.gate_reasons), **details})

    def begin_submit(self):
        if self.state != State.CREATED or not self.new_entries_allowed:
            raise ValueError("Submission requires a new persisted intent and a clear gate")
        self.state = State.SENDING
        self.reconciled = False
        self._event("submission_started", client_id=self.client_id)

    def acknowledge(self, response_id="ack", remote_order_id="SIMULATED"):
        if not response_id or not remote_order_id:
            raise ValueError("Response and remote order identities required")
        if response_id in self.responses:
            if self.responses[response_id] != remote_order_id:
                self.persistent_halts.add("response_identity_conflict")
                self.reconciled = False
                self._event("response_identity_conflict", response_id=response_id)
                raise ValueError("Response identity reused for another order")
            self._event("duplicate_response_ignored", response_id=response_id)
            return False
        if self.state not in {State.SENDING, State.UNKNOWN}:
            raise ValueError("Only an in-flight submission can be acknowledged")
        self.responses[response_id] = remote_order_id
        self.state = State.OPEN
        self._event("submission_acknowledged")
        return True

    def timeout(self):
        if self.state != State.SENDING:
            raise ValueError("Timeout requires an in-flight submission")
        self.state = State.UNKNOWN
        self._event("response_uncertain", action="Query the existing identity before retrying")

    def record_fill(self, fill_id, quantity, price, fee="0"):
        if not fill_id:
            raise ValueError("Fill identity required")
        fill = Fill(fill_id, amount(quantity, positive=True), amount(price, positive=True), amount(fee))
        old = self.fills.get(fill_id)
        if old is not None:
            if old != fill:
                self.persistent_halts.add("fill_identity_conflict")
                self.reconciled = False
                raise ValueError("Fill identity reused with different economics")
            self._event("duplicate_fill_ignored", fill_id=fill_id)
            return False
        if self.state in {State.CREATED, State.REJECTED} or self.filled + fill.quantity > self.quantity:
            self.persistent_halts.add("invalid_fill")
            self.reconciled = False
            raise ValueError("Fill contradicts the persisted order")
        self.fills[fill_id] = fill
        self.reconciled = False
        # Fill observations do not resolve an uncertain broker order response.
        if self.state not in {State.UNKNOWN, State.SENDING, State.CANCELLED}:
            self.state = State.FILLED if self.filled == self.quantity else State.PARTIAL
        self._event("fill_recorded", fill_id=fill_id, filled=str(self.filled))
        return True

    def reconcile(self, *, remote_state, remote_position, remote_filled,
                  stop_confirmed=False, stop_quantity="0"):
        self.reconciled = False
        try:
            if not isinstance(stop_confirmed, bool):
                raise ValueError("Protective-stop confirmation must be a boolean")
            remote = State(remote_state)
            position = amount(remote_position)
            cumulative = amount(remote_filled)
            protected = amount(stop_quantity)
        except (ValueError, ArithmeticError) as error:
            self.reconciliation_issues = {"invalid_observation"}
            self._event("invalid_observation")
            raise ValueError("Complete finite reconciliation observations required") from error
        if self.state == State.CREATED:
            raise ValueError("An unsent intent has no broker state to reconcile")
        if remote == State.REJECTED:
            self.persistent_halts.add("order_rejected")
        issues = set()
        if remote not in {State.OPEN, State.PARTIAL, State.FILLED, State.CANCELLED, State.REJECTED}:
            issues.add("order_response_unresolved")
        if position != self.filled:
            issues.add("position_mismatch")
        if cumulative != self.filled:
            issues.add("fill_ledger_mismatch")
        if ((remote == State.FILLED and cumulative != self.quantity)
                or (remote == State.REJECTED and cumulative != 0)
                or (remote in {State.OPEN, State.PARTIAL} and cumulative >= self.quantity)):
            issues.add("order_state_mismatch")
        if position > 0 and (not stop_confirmed or protected != position):
            issues.add("protection_unconfirmed")
        if position == 0 and protected != 0:
            issues.add("unexpected_protection")
        self.reconciliation_issues = issues
        self.reconciled = not issues
        if "order_response_unresolved" not in issues and "order_state_mismatch" not in issues:
            self.state = State.PARTIAL if remote == State.OPEN and cumulative > 0 else remote
        self._event("reconciliation", issues=sorted(issues), position=str(position), stop_quantity=str(protected))
        return self.reconciled and not self.persistent_halts

    def snapshot(self):
        return {"client_id": self.client_id, "quantity": str(self.quantity), "state": str(self.state),
                "fills": [{k: str(v) for k, v in asdict(fill).items()} for fill in self.fills.values()],
                "persistent_halts": sorted(self.persistent_halts), "issues": sorted(self.reconciliation_issues),
                "reconciled": self.reconciled, "audit": self.audit, "responses": self.responses.copy()}

    @classmethod
    def restore(cls, data):
        case = cls(data["client_id"], data["quantity"], state=State(data["state"]))
        for fill in data["fills"]:
            if fill["id"] in case.fills:
                raise ValueError("Duplicate fill in snapshot")
            case.fills[fill["id"]] = Fill(fill["id"], amount(fill["quantity"], positive=True),
                                          amount(fill["price"], positive=True), amount(fill["fee"]))
        if case.filled > case.quantity:
            raise ValueError("Snapshot overfills its order")
        case.persistent_halts = set(data["persistent_halts"])
        case.reconciliation_issues = set(data["issues"])
        # Restoring a ledger is not a fresh observation of a remote account.
        case.reconciled = False
        case.audit = list(data["audit"])
        case.responses = dict(data.get("responses", {}))
        case._event("checkpoint_restored")
        return case

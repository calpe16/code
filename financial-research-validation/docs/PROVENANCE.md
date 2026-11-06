# Source provenance

| Source in the private project | Portfolio component | Revision |
|---|---|---|
| `src/trading/metrics.py` | `completed_trades`, `daily_returns` | Adapted to validate input, support explicit entry identities and expose missing-day/anchor policies. |
| `src/trading/oms.py` | Order-state and reconciliation design | New standalone model in `research_sample/execution.py`; retains uncertainty, fill identity, position checks and protection gates as explicit examples. |
| `src/trading/runtime.py`, `src/trading/storage.py` | Restart and audit workflow | Replaced by local JSON snapshots and an event list for the demo. |

The execution module is newly implemented for this portfolio, not a literal engine extraction. It has one fictional long order and caller-supplied observations. It contains no strategy signals, current risk parameters or account connector. `validation.py`, tests and fixtures are also portfolio helpers.

The five dashboard captures use the actual Streamlit dashboard with an isolated fictional SQLite ledger and reports. A visible fixture label was added to a task-local copy of the dashboard; the original application was left unchanged. The cover arranges cropped real dashboard panels, the lifecycle diagram explains the new model, and the numerical chart plots the fixed synthetic example.

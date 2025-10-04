## 2025-10-04 - Add unit tests for core domain graph/index

### Completed Phases

- [x] Explore: Located core domain modules and existing tests
- [x] Plan: Identify normal-path scenarios to cover in graph
- [x] Implement: Added unit tests for TraceGraph (hierarchy, screen/report, CRUD, reverse CRUD); reviewed existing index tests
- [x] Commit: Local checks passed (pytest run)

### Implementation Details

#### Tests Added

1. `tests/unit/tracability/test_graph.py`
   - Hierarchy traversal `SUBSYSTEM -> BUSINESS -> FUNCTION -> PROGRAM`
   - Program to Screen linkage
   - Program to Table CRUD forward with CRUD aggregation
   - Reverse traversal from TABLE to PROGRAM allowing CRUD, and onward to SCREEN

#### Existing Tests Reviewed

- `tests/unit/tracability/test_index.py` already covers id lookup, rename, alias, and auto resolution.

#### Quality Verification

- [x] Tests passed: `uv run pytest -q`
- [x] Environment prepared via `uv sync --extra dev`

### Next Tasks

- Consider adding negative-path tests and complex graph cases (cycles, depth limits)

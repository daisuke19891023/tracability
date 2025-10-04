## 2025-10-04 - Add unit tests for application service

### Completed Phases

- [x] Explore: Located application service and loader/formatter dependencies
- [x] Plan: Define tests for from_files and query delegation/formatting
- [x] Implement: Added unit tests for TraceabilityService (loader invocation, level parsing, delegation to TraceGraph.trace, relations defaulting, formatting passthrough)
- [x] Commit: All tests passed locally

### Implementation Details

#### Tests Added

1. `tests/unit/tracability/test_service.py`
   - Validates `TraceabilityService.from_files` calls loader with correct args and LoadOptions
   - Ensures `TraceabilityService.query` parses levels, applies defaults, and delegates to graph/formatter

#### Existing Tests Reviewed

- Existing tracability unit tests (`test_graph.py`, `test_index.py`, etc.) remain green

#### Quality Verification

- [x] Lint/typing/tests passed: `uv run pytest -q` (156 passed, 3 skipped)
- [x] Dependencies installed via constraints

### Next Tasks

- Consider adding error-path tests (unknown level, no results) and path-included formatting checks

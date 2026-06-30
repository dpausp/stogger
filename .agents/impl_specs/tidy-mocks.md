# Tidy: Mock Hardening

## Changes

Add `spec=DummyJournalLogger` to 4 bare `MagicMock()` calls:

### 1. test_systemd_integration.py:73
- **Current:** `mock_module.get_journal_logger_factory = MagicMock()`
- **Target:** `mock_module.get_journal_logger_factory = MagicMock(spec=Callable)`
- **Note:** This is a factory function — must be callable. Import `Callable` from `collections.abc`.

### 2. test_systemd_integration.py:112
- **Current:** `return MagicMock()`
- **Target:** `return MagicMock(spec=DummyJournalLogger)`
- **Import needed:** `from stogger.systemd import DummyJournalLogger`

### 3. test_postgres_integration.py:48
- **Current:** `mock_logger_instance = MagicMock()`
- **Target:** `mock_logger_instance = MagicMock(spec=DummyJournalLogger)`
- **Import needed:** `from stogger.systemd import DummyJournalLogger`

### 4. test_postgres_integration.py:131
- **Current:** `mock_module.get_postgres_logger_factory = MagicMock()`
- **Target:** `mock_module.get_postgres_logger_factory = MagicMock(spec=Callable)`
- **Note:** This is a factory function — must be callable. Import `Callable` from `collections.abc`.

## Constraints
- NEVER change test semantics
- If spec breaks test, fall back to `# typed mock not possible: [reason]`
- ALL quality gates must pass after changes

# Breaking Changes

This document lists the breaking changes introduced in this cleanup of legacy code.

## 1. Removal of `init_logging_legacy`

The `init_logging_legacy` function has been removed. This function was maintained for backward compatibility with older versions but is no longer needed.

### Migration Path

If you were using the legacy function directly, you need to update your code to use `init_logging` with the new signature:

```python
# Old way (no longer supported)
init_logging_legacy(verbose=True, syslog_identifier="my-app")

# New way
init_logging(verbose=True, syslog_identifier="my-app")
```

The new `init_logging` function supports both positional and keyword arguments.

## 2. Removal of hacky cgroup code in systemd integration

The hacky code that was reading `/proc/self/cgroup` to detect systemd environment has been removed. The implementation now relies on standard systemd environment variables.

## 3. Removal of unused `translations_file` parameter

The `translations_file` parameter in `migrate_directory` function from `assistant.py` was unused and has been removed.

### Migration Path

If you were passing this parameter, you can safely remove it:

```python
# Old way (parameter ignored)
migrate_directory(input_dir, output_dir, translations_file="some_file")

# New way
migrate_directory(input_dir, output_dir)
```

## 4. Cleanup of TODO/FIXME patterns in log reviewer

Some TODO/FIXME patterns that were being detected by the log reviewer were removed as they were not meaningful.

## 5. Removal of TODO from generated code

The TODO comment in the generated code in `advanced_assistant.py` has been removed.
"""Size-based file rotation for stogger's PrintLoggerFactory pipeline.

``RotatingFileWriter`` is a file-like drop-in: ``write()``, ``flush()``,
``close()``. It rotates when an incoming write would push file size strictly
above ``max_bytes``, following the same naming convention as
``logging.handlers.RotatingFileHandler`` (``base.log``, ``base.log.1``,
``base.log.2``, ...).

Scope: size-only rotation. Timed rotation, compression, and multi-process
file locking are deliberately out of scope.

Recursion safety: no ``log.*()`` calls anywhere in this module. ``write()``
runs inside the structlog render → print → file.write hot path; logging
during rollover would recurse back through the pipeline.
"""

from pathlib import Path
from typing import IO


class RotatingFileWriter:
    """File-like writer that rotates on size overflow.

    Writes are forwarded to the underlying file. When a write would push the
    file size strictly above ``max_bytes``, the current file is closed and
    renamed to ``base.log.1``, prior backups shift down (``.1 → .2``,
    ``.2 → .3``, ...), and any file beyond ``backup_count`` is overwritten.
    A fresh ``base.log`` is opened and the triggering write lands there.

    A file holding exactly ``max_bytes`` is valid — rotation only fires when
    the next write would exceed it. This avoids spurious rotation on the
    first write of exactly ``max_bytes`` length.

    Attributes:
        filename: Base log file path (e.g. ``/var/log/app.log``).
        max_bytes: Rotation threshold. Writer rotates when the next write
            would push file size strictly above this value.
        backup_count: Maximum number of backup files (``base.log.1`` through
            ``base.log.N``) to keep. Zero disables rotation entirely.

    """

    def __init__(self, filename: Path, max_bytes: int, backup_count: int) -> None:
        if max_bytes <= 0:
            msg = f"max_bytes must be positive, got {max_bytes}"
            raise ValueError(msg)
        if backup_count < 0:
            msg = f"backup_count must be non-negative, got {backup_count}"
            raise ValueError(msg)

        self._filename = Path(filename)
        self._max_bytes = max_bytes
        self._backup_count = backup_count
        self._file: IO[str] = self._filename.open("a", encoding="utf-8")

    def write(self, msg: str) -> int:
        """Write ``msg`` to file, triggering rollover if size would be exceeded."""
        if self._backup_count > 0 and self._should_rollover(len(msg)):
            self._rollover()
        return self._file.write(msg)

    def flush(self) -> None:
        """Flush underlying file buffer."""
        self._file.flush()

    def close(self) -> None:
        """Close the underlying file. Idempotent."""
        if not self._file.closed:
            self._file.close()

    def _should_rollover(self, incoming_bytes: int) -> bool:
        """True if appending ``incoming_bytes`` would push file strictly above ``max_bytes``."""
        return self._file.tell() + incoming_bytes > self._max_bytes

    def _rollover(self) -> None:
        """Close current, rotate files, open fresh current.

        ``Path.replace`` is used for atomic rename-and-overwrite semantics
        on both POSIX and Windows.

        Caller contract: ``write()`` only calls ``_rollover`` when
        ``backup_count > 0``, so ``_shift_existing_backups`` is always safe
        (its ``range`` would produce invalid indices otherwise).
        """
        self._file.close()
        self._shift_existing_backups()
        self._filename.replace(self._backup_path(1))
        self._file = self._filename.open("a", encoding="utf-8")

    def _shift_existing_backups(self) -> None:
        """Shift backups: ``.N → .(N+1)`` for N from ``backup_count-1`` down to 1.

        Files beyond ``backup_count`` get overwritten by the shift — that's the cap.
        """
        for i in range(self._backup_count - 1, 0, -1):
            src = self._backup_path(i)
            if src.exists():
                src.replace(self._backup_path(i + 1))

    def _backup_path(self, index: int) -> Path:
        """Path for the Nth backup: ``base.log.N``."""
        return self._filename.with_name(f"{self._filename.name}.{index}")

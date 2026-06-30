"""Tests for RotatingFileWriter — size-based file rotation for stogger.

The writer is a drop-in file-like replacement for ``PrintLoggerFactory``: it
exposes ``write()``, ``flush()``, and ``close()`` and rotates on size overflow.
Follows the same naming convention as ``logging.handlers.RotatingFileHandler``
(``base.log``, ``base.log.1``, ``base.log.2``, ...).

Rotation semantics: rollover fires when the incoming write would push file
size **strictly above** max_bytes. A file holding exactly max_bytes is still
valid — the next write rotates. This avoids spurious rotation on the first
write of exactly max_bytes length.
"""

import pytest

from stogger.rotation import RotatingFileWriter


class TestRotatingFileWriterBasics:
    """Basic file-like contract: write, flush, close."""

    def test_write_creates_file_with_content(self, tmp_path):
        """First write creates the file with the written content."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=1000, backup_count=3)

        writer.write("hello\n")
        writer.flush()

        assert path.exists()
        assert path.read_text() == "hello\n"

    def test_multiple_writes_append(self, tmp_path):
        """Successive writes append, do not overwrite."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=1000, backup_count=3)

        writer.write("line one\n")
        writer.write("line two\n")
        writer.flush()

        content = path.read_text()
        assert "line one\n" in content
        assert "line two\n" in content

    def test_close_releases_file_handle(self, tmp_path):
        """close() closes the underlying file descriptor."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=100, backup_count=3)

        writer.write("test\n")
        writer.close()

        assert writer._file.closed

    def test_close_is_idempotent(self, tmp_path):
        """close() can be called twice without raising."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=100, backup_count=3)

        writer.close()
        writer.close()  # should not raise


class TestRotatingFileWriterRotation:
    """Size-based rotation behavior."""

    def test_file_can_reach_exactly_max_bytes(self, tmp_path):
        """A file holding exactly max_bytes is valid — no rotation triggered."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=10, backup_count=3)

        writer.write("0123456789")  # exactly 10 bytes
        writer.flush()

        assert path.read_text() == "0123456789"
        assert not (tmp_path / "app.log.1").exists()

    def test_rotation_triggers_when_next_write_exceeds_max_bytes(self, tmp_path):
        """Write that crosses max_bytes triggers rotation: current → .1, fresh file opened."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=10, backup_count=3)

        writer.write("0123456789")  # exactly 10 — no rotation
        writer.write("X")  # would push to 11 — rotation
        writer.flush()

        rotated = tmp_path / "app.log.1"
        assert rotated.exists()
        assert rotated.read_text() == "0123456789"
        # Fresh current file holds the triggering write
        assert path.read_text() == "X"

    def test_multiple_rotations_shift_backups(self, tmp_path):
        """Each rotation shifts existing backups: .1 → .2, current → .1."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=5, backup_count=3)

        # Write batches that each fill then trigger rotation on the next
        writer.write("aaa")  # 3 bytes, file = "aaa", no rotation
        writer.write("bb")  # would push to 5, still no rotation (5 is valid)
        # Next write: 5 + 3 = 8 > 5 → rotation
        writer.write("ccc")  # .1 = "aaabb", current = "ccc"
        writer.write("ddd")  # 3+3=6>5 → rotation: .2="aaabb", .1="ccc", current="ddd"
        writer.write("eee")  # rotation: .3="aaabb", .2="ccc", .1="ddd", current="eee"
        writer.flush()

        assert path.read_text() == "eee"
        assert (tmp_path / "app.log.1").read_text() == "ddd"
        assert (tmp_path / "app.log.2").read_text() == "ccc"
        assert (tmp_path / "app.log.3").read_text() == "aaabb"

    def test_backup_count_drops_oldest(self, tmp_path):
        """With backup_count=2, the oldest backup is deleted on next rotation."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=5, backup_count=2)

        writer.write("aaa")
        writer.write("bb")  # file = "aaabb", no rotation
        writer.write("ccc")  # rotation: .1="aaabb", current="ccc"
        writer.write("ddd")  # rotation: .2="aaabb", .1="ccc", current="ddd"
        writer.write("eee")  # rotation: .2="ccc", .1="ddd" (aaabb dropped), current="eee"
        writer.flush()

        assert path.read_text() == "eee"
        assert (tmp_path / "app.log.1").read_text() == "ddd"
        assert (tmp_path / "app.log.2").read_text() == "ccc"
        assert not (tmp_path / "app.log.3").exists()

    def test_no_rotation_when_under_limit(self, tmp_path):
        """Writes that stay under max_bytes do not trigger rotation."""
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=100, backup_count=3)

        for i in range(10):
            writer.write(f"line {i}\n")
        writer.flush()

        total_size = path.stat().st_size
        assert total_size < 100
        assert not (tmp_path / "app.log.1").exists()

    def test_zero_backup_count_disables_rotation(self, tmp_path):
        """backup_count=0 means rollover branch is skipped — file grows unbounded.

        Documented contract: writer accepts backup_count=0 (useful when caller
        wants a single bounded-by-max_bytes slot but no backups). The write()
        guard skips both rollover check and rollover call.
        """
        path = tmp_path / "app.log"
        writer = RotatingFileWriter(path, max_bytes=5, backup_count=0)

        writer.write("aaaaaaaaaa")  # 10 bytes >> 5, would normally rotate
        writer.write("bbbbbbbbbb")  # another 10
        writer.flush()

        # All content accumulated in single file, no rotation
        assert path.read_text() == "aaaaaaaaaabbbbbbbbbb"
        assert not (tmp_path / "app.log.1").exists()


class TestRotatingFileWriterValidation:
    """Constructor validation — fail loudly on invalid configuration."""

    def test_zero_max_bytes_raises(self, tmp_path):
        """max_bytes=0 raises ValueError — rotation semantics require a positive cap."""
        path = tmp_path / "app.log"
        with pytest.raises(ValueError, match="max_bytes"):
            RotatingFileWriter(path, max_bytes=0, backup_count=3)

    def test_negative_max_bytes_raises(self, tmp_path):
        """Negative max_bytes raises ValueError."""
        path = tmp_path / "app.log"
        with pytest.raises(ValueError, match="max_bytes"):
            RotatingFileWriter(path, max_bytes=-1, backup_count=3)

    def test_negative_backup_count_raises(self, tmp_path):
        """Negative backup_count raises ValueError."""
        path = tmp_path / "app.log"
        with pytest.raises(ValueError, match="backup_count"):
            RotatingFileWriter(path, max_bytes=100, backup_count=-1)

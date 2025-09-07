import re
import textwrap

from nicestlog.assistant import migrate_file


def _norm(s: str):
    return textwrap.dedent(s).strip() + "\n"


def test_print_simple_literal_to_event_and_replace_msg():
    src = _norm(
        """
        def main():
            print("Hello World!")
        """,
    )
    new, changed = migrate_file(src)
    assert changed
    assert "log.info(" in new
    assert re.search(r"_replace_msg=([\"']?)Hello World!\1", new)
    assert "hello-world" in new


def test_print_literal_and_arg_placeholders():
    src = _norm(
        """
        def main():
            print("Result:", x)
        """,
    )
    new, changed = migrate_file(src)
    assert changed
    assert re.search(r"_replace_msg=([\"']?)Result: \{a0\}\1", new)
    assert "a0=x" in new


def test_print_args_only_placeholders():
    src = _norm(
        """
        def main():
            print(x, y)
        """,
    )
    new, changed = migrate_file(src)
    assert changed
    assert re.search(r"_replace_msg=([\"']?)\{a0\} \{a1\}\1", new)
    assert "a0=x" in new and "a1=y" in new


def test_inserts_import_and_logger():
    src = _norm(
        """
        def main():
            print("X")
        """,
    )
    new, changed = migrate_file(src)
    assert changed
    assert "import structlog" in new
    assert "log = structlog.get_logger()" in new

from importlib.metadata import version


def test_version_matches_metadata():
    import stogger

    assert stogger.__version__ == version("stogger"), (
        f"stogger.__version__={stogger.__version__!r} != metadata version={version('stogger')!r}"
    )

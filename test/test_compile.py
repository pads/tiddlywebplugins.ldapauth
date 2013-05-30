def test_compile():
    try:
        import tiddlywebplugins.ldapauth

        assert True
    except ImportError, exc:
        assert False, exc

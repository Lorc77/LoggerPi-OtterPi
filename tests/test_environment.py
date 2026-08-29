def test_python_environment():
    """Die Tests laufen innerhalb der erwarteten virtuellen Umgebung."""
    import sys

    assert sys.prefix != sys.base_prefix

def test_mock_discovery():
    from bambu_forge.printer.discovery import discover_printers

    printers = discover_printers(mock=True, timeout=1)
    assert len(printers) >= 1
    assert "ip" in printers[0]
    assert "model" in printers[0]
    assert "serial" in printers[0]

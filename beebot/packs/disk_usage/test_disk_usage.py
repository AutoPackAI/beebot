from disk_usage import DiskUsage


def test_disk_usage():
    usage = DiskUsage().run()

    assert "Total:" in usage
    assert "Used:" in usage
    assert "Available:" in usage
    assert "Percent Used:" in usage

from os_info.os_info import OSInfo


def test_os_info():
    info = OSInfo().run()
    assert "OS Name" in info
    assert "OS Version" in info

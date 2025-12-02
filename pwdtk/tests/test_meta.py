from unittest.mock import patch

import pwdtk


from pwdtk.meta import version_info


def check_types(info):
    """
    check that versioninfo returns ints if possible
    """
    for field in info:
        try:
            if int(field) == field:
                assert isinstance(field, int)
        except ValueError:
            pass


def test_can_get_version_info():
    """ can I the current version info """
    infostr = pwdtk.__version__
    info = version_info()
    joined = ".".join(str(v) for v in info)
    assert joined == infostr
    check_types(info)


def test_version_w_str():
    """
    Are versions with strings properly handled
    """
    infostr = "0.1.a"
    with patch("pwdtk.__version__", infostr):
        info = version_info()
        joined = ".".join(str(v) for v in info)
    assert joined == infostr
    check_types(info)


def test_version_w_rc():
    """
    Are versions with trailing rc handled 'nicely'
    """
    infostr = "0.1rc"
    with patch("pwdtk.__version__", infostr):
        info = version_info()
        assert info == (0, 1, -1, "rc")
    check_types(info)

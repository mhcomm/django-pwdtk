import pwdtk


def version_info():
    """
    returns version info as a tuple
    a trailing rc will be treated as ".-1.rc"
    to have better sorting results
    """
    version_str = pwdtk.__version__
    if version_str.endswith("rc"):
        version_str = version_str[:-2] + ".-1.rc"
    rslt = []
    for field in version_str.split("."):
        try:
            rslt.append(int(field))
        except ValueError:
            rslt.append(field)
    return tuple(rslt)

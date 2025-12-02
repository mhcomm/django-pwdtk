default_app_config = 'pwdtk.apps.PwdTkConfig'

try:
    from importlib.metadata import version
    __version__ = version("pwdtk")
except ImportError:
    from pwdtk._version import __version__  # noqa: F401

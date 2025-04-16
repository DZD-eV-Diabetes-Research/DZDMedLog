try:
    from medlogserver.__version__ import __version__
except ModuleNotFoundError:
    # get version from git
    from setuptools_scm import get_version
    from os import path

    __version__ = get_version(path.join(path.dirname(__file__), "../../.."))

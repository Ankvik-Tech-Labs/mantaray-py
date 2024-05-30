"""Mantaray data structure in Python"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version('mantaray-py')
except PackageNotFoundError:  # pragma: no cover
    __version__ = 'unknown'
finally:
    del version, PackageNotFoundError

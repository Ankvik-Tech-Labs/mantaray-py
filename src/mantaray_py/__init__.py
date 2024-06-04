"""Mantaray data structure in Python"""

from importlib.metadata import PackageNotFoundError, version

from mantaray_py.types.types import (
    MetadataMapping,
    NodeType,
    Reference,
    marshal_version_values,
    storage_loader,
    storage_saver,
)
from mantaray_py.utils import (
    check_reference,
    common,
    encrypt_decrypt,
    equal_bytes,
    find_index_of_array,
    flatten_bytes_array,
    keccak256_hash,
)

__all__ = [
    "MetadataMapping",
    "NodeType",
    "Reference",
    "check_reference",
    "common",
    "encrypt_decrypt",
    "equal_bytes",
    " find_index_of_array",
    "find_index_of_array",
    "flatten_bytes_array",
    "keccak256_hash",
    "marshal_version_values",
    "storage_loader",
    " storage_saver",
    "storage_saver",
]

try:
    __version__ = version("mantaray-py")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

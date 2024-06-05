"""Mantaray data structure in Python"""

from importlib.metadata import PackageNotFoundError, version

from mantaray_py.node import MantarayNode, equal_nodes
from mantaray_py.types.types import (
    MetadataMapping,
    NodeType,
    Reference,
    StorageLoader,
    StorageSaver,
    marshal_version_values,
)
from mantaray_py.utils import (
    check_reference,
    common,
    encrypt_decrypt,
    equal_bytes,
    find_index_of_array,
    flatten_bytes_array,
    gen_32_bytes,
    keccak256_hash,
)

__all__ = [
    "MantarayNode",
    "MetadataMapping",
    "NodeType",
    "Reference",
    "StorageLoader",
    "StorageSaver",
    " StorageSaver",
    "check_reference",
    "common",
    "encrypt_decrypt",
    "equal_bytes",
    " find_index_of_array",
    "find_index_of_array",
    "flatten_bytes_array",
    "gen_32_bytes",
    "keccak256_hash",
    "marshal_version_values",
    "equal_nodes"
]

try:
    __version__ = version("mantaray-py")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

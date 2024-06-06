"""Mantaray data structure in Python"""

from importlib.metadata import PackageNotFoundError, version

from mantaray_py.node import MantarayNode, equal_nodes, check_for_separator
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
    "check_reference",
    "common",
    "encrypt_decrypt",
    "equal_bytes",
    "equal_nodes",
    "find_index_of_array",
    "flatten_bytes_array",
    "gen_32_bytes",
    "keccak256_hash",
    "marshal_version_values",
    "check_for_separator"
]

def init_manifest_node(options: dict = None) -> MantarayNode:
    """
    Initializes a MantarayNode with an optional obfuscation key.

    Parameters:
    - options (dict): A dictionary containing an optional obfuscation key.

    Returns:
    - MantarayNode: An initialized MantarayNode instance.
    """
    manifest_node = MantarayNode()
    if options is None:
        options = {}
    if 'obfuscationKey' in options:
        manifest_node.set_obfuscation_key(options['obfuscationKey'])
    else:
        manifest_node.set_obfuscation_key(None)

    return manifest_node

try:
    __version__ = version("mantaray-py")
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"
finally:
    del version, PackageNotFoundError

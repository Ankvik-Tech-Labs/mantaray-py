from mantaray_py.types import (
    MetadataMapping,
    NodeType,
    Reference,
    marshal_version_values,
    storage_loader,
    storage_saver,
)
from mantaray_py.utils import (
    bytes_equal,
    check_reference,
    common,
    encrypt_decrypt,
    find_index_of_array,
    flatten_bytes_array,
    keccak256_hash,
)

PATH_SEPARATOR = '/'
PATH_SEPARATOR_BYTE = 47
PADDING_BYTE = 0x0a
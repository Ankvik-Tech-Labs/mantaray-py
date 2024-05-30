from typing import Callable, Literal, Optional, Union

from pydantic import BaseModel, conlist

# Equivalent to the 'marshal_versionValues' and 'marshal_version' in TypeScript
marshal_version_values = ('0.1', '0.2')
marshal_version = Literal['0.1', '0.2']


# Equivalent to the 'NodeType' enum in TypeScript
class NodeType:
    value = 2
    edge = 4
    with_path_separator = 8
    with_metadata = 16
    mask = 255


# Custom type for Bytes with constrained length
def create_bytes_type(length: int):
    return conlist(int, min_items=length, max_items=length)


Bytes32 = create_bytes_type(32)
Bytes64 = create_bytes_type(64)
Reference = Union[Bytes32, Bytes64]


# Equivalent to the 'metadata_mapping' type in TypeScript
metadata_mapping = dict[str, str]

# Equivalent to the 'Storage_loader' and 'StorageSaver' in TypeScript
Storage_loader = Callable[[Reference], bytes]
Storage_saver = Callable[[bytes, Optional[dict]], Reference]


# Equivalent to the 'StorageHandler' type in TypeScript
class StorageHandler(BaseModel):
    load: Storage_loader
    save: Storage_saver


# Example usage of the defined models and types
class ExampleUsage(BaseModel):
    version: marshal_version
    reference: Reference
    metadata: metadata_mapping
    handler: StorageHandler

    class Config:
        arbitrary_types_allowed = True

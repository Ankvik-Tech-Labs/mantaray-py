from enum import Enum
from typing import Callable, Optional

from pydantic import BaseModel

marshal_version_values: tuple[str, str] = ('0.1', '0.2')

MarshalVersion = str


class NodeType(Enum):
    value = 2
    edge = 4
    with_path_separator = 8
    with_metadata = 16
    mask = 255


class Bytes(BaseModel):
    length: int


Reference = Bytes


MetadataMapping = dict[str, str]


storage_loader = Callable[[Reference], bytes]
storage_saver = Callable[[bytes, Optional[dict]], Reference]


class StorageHandler(BaseModel):
    load: storage_loader
    save: storage_saver

from enum import Enum
from typing import Callable

from pydantic import BaseModel

marshal_version_values: tuple[str, str] = ("0.1", "0.2")

MarshalVersion = str


class NodeType(Enum):
    value = 2
    edge = 4
    with_path_separator = 8
    with_metadata = 16
    mask = 255


Reference = bytes


MetadataMapping = dict[str, str]


StorageLoader = Callable[[Reference], bytes]
StorageSaver = Callable


class StorageHandler(BaseModel):
    load: StorageLoader
    save: StorageSaver

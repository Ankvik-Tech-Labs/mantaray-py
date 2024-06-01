import json
from typing import Optional

from pydantic import BaseModel

from mantaray_py.types import (
    Reference,
)

PATH_SEPARATOR = "/"
PATH_SEPARATOR_BYTE = 47
PADDING_BYTE = 0x0A


class MantarayNode(BaseModel): ...


class MantarayFork(BaseModel):
    """
    A class used to represent a Mantaray Fork.

    Attributes:
        prefix (bytes): The non-branching part of the subpath.
        node (MantarayNode): In memory structure that represents the Node.
    """

    prefix: bytes
    node: MantarayNode

    @staticmethod
    def _create_metadata_padding(metadata_size_with_size: int) -> bytes:
        # can be done as bytes(0) as well
        padding = b""

        if metadata_size_with_size < NodeHeaderSizes.obfuscation_key:
            padding_len = NodeHeaderSizes.obfuscation_key - metadata_size_with_size
            padding = bytes([PADDING_BYTE] * padding_len)
        elif metadata_size_with_size > NodeHeaderSizes.obfuscation_key:
            padding_len = NodeHeaderSizes.obfuscation_key - (metadata_size_with_size % NodeHeaderSizes.obfuscation_key)
            padding = bytes([PADDING_BYTE] * padding_len)

        return padding

    def serialize(self) -> bytes:
        node_type = self.node.get_type
        prefix_len_bytes = bytes(1)
        prefix_len_bytes[0] = len(self.prefix)

        prefix_bytes = bytearray(NodeForkSizes.prefixMaxSize())
        prefix_bytes[: len(self.prefix)] = self.prefix

        entry: Optional[bytes] = self.node.getContentAddress()

        if entry is None:
            raise ValueError("Cannot serialize MantarayFork because it does not have contentAddress")

        data = bytes([node_type]) + prefix_len_bytes + prefix_bytes + entry

        if self.node.IsWithMetadataType():
            json_string = json.dumps(self.node.getMetadata())
            metadata_bytes = json_string.encode("utf-8")

            metadata_size_with_size = len(metadata_bytes) + NodeForkSizes.metadata()
            padding = self.create_metadata_padding(metadata_size_with_size)

            metadata_bytes_size = (len(metadata_bytes) + len(padding)).to_bytes(2, byteorder="big")

            return data + metadata_bytes_size + metadata_bytes + padding

        return data

    @classmethod
    def deserialize(cls, data: bytes, obfuscation_key: bytes, options: Optional[dict[str, dict[str, int]]] = None):
        node_type = data[0]
        prefix_length = data[1]

        if prefix_length == 0 or prefix_length > NodeForkSizes.prefixMaxSize():
            raise ValueError(
                f"Prefix length of fork is greater than {NodeForkSizes.prefixMaxSize()}. Got: {prefix_length}"
            )

        header_size = NodeForkSizes.header()
        prefix = data[header_size : header_size + prefix_length]
        node = MantarayNode()
        node.setObfuscationKey(obfuscation_key)

        with_metadata = options.get("withMetadata") if options else None

        if with_metadata:
            ref_bytes_size = with_metadata["refBytesSize"]
            metadata_byte_size = with_metadata["metadataByteSize"]

            if metadata_byte_size > 0:
                entry_start = NodeForkSizes.pre_reference()
                entry_end = entry_start + ref_bytes_size
                node.setEntry(data[entry_start:entry_end])

                start_metadata = entry_end + NodeForkSizes.metadata()
                metadata_bytes = data[start_metadata : start_metadata + metadata_byte_size]

                json_string = metadata_bytes.decode("utf-8")
                node.setMetadata(json.loads(json_string))
        else:
            entry_start = NodeForkSizes.pre_reference()
            node.setEntry(data[entry_start:])

        node.set_type(node_type)
        return cls(prefix=prefix, node=node)


ForkMapping = dict[int, MantarayFork]


class RecursiveSaveReturnType(BaseModel):
    reference: Reference
    changed: bool


class NodeForkSizes(BaseModel):
    node_type: int = 1
    prefix_length: int = 1
    # * Bytes length before `reference`
    pre_reference: int = 32
    metadata: int = 2

    @property
    def header(self) -> int:
        return self.node_type + self.prefix_length

    @property
    def prefix_max_size(self) -> int:
        return self.pre_reference - self.header


class NodeHeaderSizes(BaseModel):
    obfuscation_key: int = 32
    version_hash: int = 31
    # * Its value represents how long is the `entry` in bytes
    ref_bytes: int = 1

    @property
    def full(self) -> int:
        return self.obfuscation_key + self.version_hash + self.ref_bytes


class NotFoundError(Exception):
    def __init__(self, remaining_path_bytes: bytes, checked_prefix_bytes: Optional[bytes] = None):
        remaining_path = remaining_path_bytes.decode()
        prefix_info = (
            f"Prefix on lookup: {checked_prefix_bytes.decode()}" if checked_prefix_bytes else "No fork on the level"
        )
        super().__init__(
            f"Path has not found in the manifest. Remaining path on lookup: {remaining_path}. {prefix_info}!"
        )


class EmptyPathError(Exception):
    def __init__(self) -> None:
        super().__init__("Empty Path!")


class UndefinedFieldError(Exception):
    def __init__(self, field: str) -> None:
        super().__init__(f"{field} is not initialised!")


class PropertyIsUndefinedError(Exception):
    def __init__(self):
        super().__init__("Property does not exist in the object")


class NotImplementedError(Exception):
    def __init__(self):
        super().__init__("Not Implemented")

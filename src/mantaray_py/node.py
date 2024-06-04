import json
from typing import Optional

from pydantic import BaseModel, field_validator

from mantaray_py.types import (
    MarshalVersion,
    MetadataMapping,
    NodeType,
    Reference,
    storage_loader,
    storage_saver,
)
from mantaray_py.utils import IndexBytes, check_reference, common, equal_bytes

PATH_SEPARATOR = "/"
PATH_SEPARATOR_BYTE = 47
PADDING_BYTE = 0x0A


ForkMapping = dict


class MantarayFork(BaseModel):
    """
    A class used to represent a Mantaray Fork.

    Attributes:
        prefix (bytes): The non-branching part of the subpath.
        node (MantarayNode): In memory structure that represents the Node.
    """

    prefix: bytes
    node: "MantarayNode"

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

        if self.node.Iswith_metadataType():
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

        with_metadata = options.get("with_metadata") if options else None

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


class MantarayNode(BaseModel):
    # * Used with NodeType type
    __type: Optional[int]
    __obfuscation_key: Optional[bytes]
    # * reference of a loaded manifest node. if undefined, the node can be handled as `dirty`
    __content_address: Optional[Reference]
    # * reference of an content that the manifest refers to
    __entry: Optional[Reference]
    __metadata: Optional[MetadataMapping]
    # * Forks of the manifest. Has to be initialized with `{}` on load even if there were no forks
    forks: Optional[ForkMapping]

    @field_validator("type")
    def check_type(cls, v):
        if v > 255:
            msg = "Node type representation cannot be greater than 255"
            raise ValueError(msg)
        return v

    def set_content_address(self, content_address: Reference):
        self.__content_address = check_reference(content_address)

    def set_entry(self, entry: Reference):
        self.__entry = check_reference(entry)
        if not equal_bytes(entry, bytes(len(entry))):
            self.____make_value()
        self.make_dirty()

    def set_type(self, _type: int):
        if _type > 255:
            raise ValueError("Node type representation cannot be greater than 255")
        self.__type = _type

    def set_obfuscation_key(self, obfuscation_key: bytes):
        if not isinstance(obfuscation_key, bytes):
            raise TypeError("Given obfuscationKey is not a bytes instance.")
        if len(obfuscation_key) != 32:
            raise ValueError("Wrong obfuscationKey length. Entry can only be 32 bytes in length")
        self.__obfuscationKey = obfuscation_key
        self.make_dirty()

    def set_metadata(self, metadata: MetadataMapping):
        self.__metadata = metadata
        self.__make_with_metadata()
        if metadata.get("website-index-document") or metadata.get("website-error-document"):
            self.____make_value()
        self.make_dirty()

    def get_obfuscation_key(self) -> Optional[bytes]:
        return self.__obfuscationKey

    def get_entry(self) -> Optional[Reference]:
        return self.__entry

    def get_content_address(self) -> Optional[Reference]:
        return self.__content_address

    def get_metadata(self) -> Optional[MetadataMapping]:
        return self.__metadata

    def get_type(self) -> int:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        if self.__type > 255:
            raise ValueError("Property 'type' in Node is greater than 255")
        return self.__type

    # * Node type related functions
    # * dirty flag is not necessary to be set

    def is_value_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type and NodeType.value == NodeType.value

    def is_edge_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type and NodeType.edge == NodeType.edge

    def is_with_path_separator_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type and NodeType.with_path_separator == NodeType.with_path_separator

    def is_with_metadata_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type and NodeType.with_metadata == NodeType.with_metadata

    def __make_value(self) -> None:
        if self.__type is None:
            self.__type = NodeType.value
        self.__type |= NodeType.value

    def __make_edge(self) -> None:
        if self.__type is None:
            self.__type = NodeType.edge
        self.__type |= NodeType.edge

    def __make_with_path_separator(self) -> None:
        if self.__type is None:
            self.__type = NodeType.with_path_separator
        self.__type |= NodeType.with_path_separator

    def __make_with_metadata(self) -> None:
        if self.__type is None:
            self.__type = NodeType.with_metadata
        self.__type |= NodeType.with_metadata

    def __make_not_with_path_separator(self) -> None:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        self.__type = (NodeType.mask ^ NodeType.with_path_separator) and self.__type

    def __update_with_path_separator(self, path: bytes) -> None:
        if b"/" in path[1:]:
            self.__make_with_path_separator()
        else:
            self.__make_not_with_path_separator()

    # ? BL methods

    def add_fork(self, path: bytes, entry: Reference, metadata: MetadataMapping = {}) -> None:
        """
        Adds a fork to the current node based on the provided path, entry, and metadata.

        Parameters:
        - path (List[int]): A list representing the path in bytes. Can be empty, in which case `entry` will be set as the current node's entry.
        - entry (Reference): The entry to be associated with the fork.
        - metadata (Dict[str, Any], optional): Additional metadata to associate with the fork. Defaults to an empty dictionary.

        Returns:
        None
        """
        if not path:
            self.set_entry(entry)
            if metadata:
                self.set_metadata(metadata)
            self.make_dirty()
            return

        if self.is_dirty() and not self.forks:
            self.forks = {}

        if not self.forks:
            raise ValueError("Fork mapping is not defined in the manifest")

        fork = self.forks.get(path[0])

        if not fork:
            new_node = MantarayNode()
            if self.__obfuscation_key:
                new_node.set_obfuscation_key(self.__obfuscation_key)

            if len(path) > NodeForkSizes.prefix_max_size():
                prefix = path[: NodeForkSizes.prefix_max_size()]
                rest = path[NodeForkSizes.prefix_max_size() :]
                new_node.add_fork(rest, entry, metadata)
                new_node.__update_with_path_separator(prefix)
                self.forks[path[0]] = MantarayFork(prefix=prefix, node=new_node)
                self.make_dirty()
                self.__make_edge()
                return

            new_node.set_entry(entry)
            if metadata:
                new_node.set_metadata(metadata)
            new_node.__update_with_path_separator(path)
            self.forks[path[0]] = MantarayFork(prefix=path, node=new_node)
            self.make_dirty()
            self.__make_edge()
            return

        common_path = common(fork.prefix, path)
        rest_path = fork.prefix[len(common_path) :]
        new_node = fork.node

        if rest_path:
            new_node = MantarayNode()
            new_node.set_obfuscation_key(self.__obfuscation_key or bytes(32))
            fork.node.__update_with_path_separator(rest_path)
            new_node.forks = {rest_path[0]: MantarayFork(prefix=rest_path, node=fork.node)}
            new_node.__make_edge()

            if len(path) == len(common_path):
                new_node.____make_value()

        # * NOTE: special case on edge split
        # * new_node will be the common path edge node
        # TODO: change it on Bee side! -> new_node is the edge (parent) node of the newly
        # * created path, so `common_path` should be passed instead of `path`
        new_node.__update_with_path_separator(common_path)

        # * newNode's prefix is a subset of the given `path`, here the desired fork will be added with the
        # * truncated path
        new_node.add_fork(path[len(common_path) :], entry, metadata)
        self.forks[path[0]] = MantarayFork(prefix=common_path, node=new_node)
        self.__make_edge()
        self.make_dirty()

    def get_fork_at_path(self, path: bytes) -> Optional[MantarayFork]:
        """
        Retrieves a MantarayFork under the given path.

        Parameters:
        - path (list[int]): A list representing the path in bytes.

        Returns:
        Optional[MantarayFork]: The MantarayFork object with the last unique prefix and its node, or None if not found.

        Raises:
        ValueError: If there is no node under the given path.
        """
        if not path:
            raise EmptyPathError()
        if not self.forks:
            raise ValueError("Fork mapping is not defined in the manifest")

        fork = self.forks.get(path[0])
        if not fork:
            raise NotFoundError()

        if path.startswith(fork.prefix):
            rest = path[len(fork.prefix) :]
            if not rest:
                return fork
            return fork.node.get_fork_at_path(rest)
        else:
            raise NotFoundError(path)

    def remove_path(self, path: bytes) -> None:
        """
        Removes a path from the node.

        Parameters:
        - path (List[int]): A list representing the path in bytes.
        """
        if not path:
            raise ValueError("Path is empty")
        if not self.forks:
            raise ValueError("Fork mapping is not defined in the manifest")

        fork = self.forks.get(path[0])
        if not fork:
            raise NotFoundError(path)

        if path.startswith(fork.prefix):
            rest = path[len(fork.prefix) :]
            if not rest:
                del self.forks[path[0]]
                self.make_dirty()
            else:
                fork.node.remove_path(rest)
        else:
            raise NotFoundError(path)

    def load(self, storage_loader: storage_loader, reference: Reference) -> None:
        if not reference:
            raise ValueError("Reference is undefined at manifest load")
        data = storage_loader(reference)
        self.deserialize(data)
        self.set_content_address(reference)

    def save(self, storage_saver: storage_saver) -> Reference:
        """
        Saves dirty flagged ManifestNodes and its forks recursively.

        Parameters:
        - storage_saver (StorageSaver): An instance of StorageSaver responsible for saving data.

        Returns:
        - Reference: Reference of the top manifest node.
        """
        result = self.recursive_save(storage_saver)
        return result["reference"]

    def is_dirty(self) -> bool:
        """
        Checks if the node is marked as dirty.

        Returns:
        - bool: True if the node is dirty, False otherwise.
        """
        return self.__content_address is None

    def make_dirty(self) -> None:
        """
        Marks the content_address to None.
        """
        self.__content_address = None

    def serialize(self) -> bytes:
        """
        Serializes the node and its forks into a byte array.

        Returns:
        - bytes: Serialized byte array representation of the node.
        """
        if not self.__obfuscation_key:
            self.set_obfuscation_key(bytes(32))
        if not self.forks:
            if not self.__entry:
                raise UndefinedFieldError("Entry")
            # * if there were no forks initialized it is not intended to be
            self.forks = {}
        if not self.__entry:
            self.__entry = bytes(32)

        # Header
        version: MarshalVersion = "0.2"
        version_bytes: bytes = serialize_version(version)
        # * Entry is already in byte version
        reference_len_bytes: bytes = serialize_reference_len(self.__entry)

        # ForksIndexBytes
        index = IndexBytes()
        for fork_index in self.forks.keys():
            index.set_byte(int(fork_index))
        index_bytes = index.get_bytes()

        # Forks
        fork_serializations: list[bytes] = []

        for byte in index:
            fork = self.forks.get(byte)
            if fork is None:
                raise ValueError(f"Fork indexing error: fork has not found under {byte} index")
            fork_serializations.append(fork.serialize())

        bytes_data = b"".join(
            [
                self.obfuscation_key,
                version_bytes,
                reference_len_bytes,
                self.entry,
                index_bytes,
                *fork_serializations,
            ]
        )

        # Encryption
        # perform XOR encryption on bytes after obfuscation key
        encrypt_decrypt(self.__obfuscation_key, bytes_data, len(self.__obfuscation_key))

        return bytes_data

    def deserialize(self, data: bytes) -> None:
        """
        Deserializes a byte array back into a node.

        Parameters:
        - data (bytes): Byte array representation of the node.
        """
        node_header_size = NodeHeaderSizes.full()

        if len(data) < node_header_size:
            raise ValueError("The serialized input is too short")

        self.obfuscation_key = data[: NodeHeaderSizes.obfuscation_key]
        # * perform XOR decryption on bytes after obfuscation key
        encrypt_decrypt(self.obfuscation_key, data, len(self.obfuscation_key))

        version_hash = data[
            NodeHeaderSizes.obfuscation_key : NodeHeaderSizes.obfuscation_key + NodeHeaderSizes.version_hash
        ]

        if equal_bytes(version_hash, serialize_version("0.1")):
            raise NotImplementedError
        elif equal_bytes(version_hash, serialize_version("0.2")):
            ref_bytes_size = data[node_header_size - 1]
            entry = data[node_header_size : node_header_size + ref_bytes_size]

            # FIXME: in Bee. if one uploads a file on the bzz endpoint, the node under `/` gets 0 refsize
            if ref_bytes_size == 0:
                entry = bytes(32)
            self.entry = entry
            offset = node_header_size + ref_bytes_size
            index_bytes = data[offset : offset + 32]

            # Currently we don't persist the root nodeType when we marshal the manifest, as a result
            # the root nodeType information is lost on Unmarshal. This causes issues when we want to
            # perform a path 'Walk' on the root. If there is at least 1 fork, the root node type
            # is an edge, so we will deduce this information from index byte array
            if not equal_bytes(index_bytes, bytes(32)):
                self.__make_edge()
            self.forks = {}
            index_forks = IndexBytes()
            index_forks.set_bytes(index_bytes)
            offset += 32

            for byte in index_forks:
                if len(data) < offset + NodeForkSizes.node_type:
                    raise ValueError(f"There is not enough size to read nodeType of fork at offset {offset}")

                node_type = data[offset : offset + NodeForkSizes.node_type]
                node_fork_size = NodeForkSizes.pre_reference + ref_bytes_size

                if node_type_is_with_metadata_type(node_type[0]):
                    if len(data) < offset + NodeForkSizes.pre_reference + ref_bytes_size + NodeForkSizes.metadata:
                        raise ValueError(f"Not enough bytes for metadata node fork at byte {byte}")

                    metadata_byte_size = data[
                        offset + node_fork_size : offset + node_fork_size + NodeForkSizes.metadata
                    ]
                    node_fork_size += NodeForkSizes.metadata + metadata_byte_size

                    fork = MantarayFork.deserialize(
                        data[offset : offset + node_fork_size],
                        self.obfuscation_key,
                        {
                            "with_metadata": {
                                "ref_bytes_size": ref_bytes_size,
                                "metadata_byte_size": metadata_byte_size,
                            },
                        },
                    )
                else:
                    if len(data) < offset + NodeForkSizes.pre_reference + ref_bytes_size:
                        raise ValueError(f"There is not enough size to read fork at offset {offset}")

                    fork = MantarayFork.deserialize(data[offset : offset + node_fork_size], self.obfuscation_key)

                self.forks[byte] = fork

                offset += node_fork_size
        else:
            raise ValueError("Wrong mantaray version")

    def __recursive_save(self, storage_saver: storage_saver) -> dict[str, Reference]:
        """
        Recursively saves the node and its forks.

        Parameters:
        - storage_saver (StorageSaver): An instance of StorageSaver responsible for saving data.

        Returns:
        - dict[str, Reference]: A dictionary containing the reference of the top manifest node and a flag indicating if the node was changed.
        """
        if not self.forks:
            raise ValueError("Node has no forks")

        out = {}
        for fork in self.forks.values():
            out.update(fork.node.recursive_save(storage_saver))

        serialized_data = self.serialize()
        ref = storage_saver(serialized_data)
        self.set_content_address(ref)
        out["reference"] = ref
        return out


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
    def __init__(self) -> None:
        super().__init__("Property does not exist in the object")


# ! predefined in python
# class NotImplementedError(Exception):
#     def __init__(self) -> None:
#         super().__init__("Not Implemented")

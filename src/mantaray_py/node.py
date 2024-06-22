import json
from typing import Any, Optional, Union

from eth_utils import keccak
from pydantic import BaseModel, ConfigDict
from rich.console import Console
from rich.traceback import install

from mantaray_py.types import (
    MarshalVersion,
    MetadataMapping,
    NodeType,
    Reference,
    StorageLoader,
    StorageSaver,
)
from mantaray_py.utils import IndexBytes, check_reference, common, encrypt_decrypt, equal_bytes, flatten_bytes_array

install()
console = Console()

PATH_SEPARATOR = b"/"
PATH_SEPARATOR_BYTE = 47
PADDING_BYTE = 0x0A
NODE_SIZE = 255


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

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MantarayFork):
            return False
        return self.prefix == other.prefix and self.node == other.node

    def __hash__(self) -> int:
        """
        A class that implements __eq__ but not __hash__ will have its hash method implicitly set
        to None. This will cause the class to be unhashable, will in turn cause issues when
        using the class as a key in a dictionary or a member of a set.
        * https://docs.astral.sh/ruff/rules/eq-without-hash/
        """
        return hash(self.node)

    @staticmethod
    def __create_metadata_padding(metadata_size_with_size: int) -> bytes:
        # can be done as bytes(0) as well
        padding: bytes = b""
        node_headers_sizes: NodeHeaderSizes = NodeHeaderSizes()

        if metadata_size_with_size < node_headers_sizes.obfuscation_key:
            padding_len = node_headers_sizes.obfuscation_key - metadata_size_with_size
            padding = bytes([PADDING_BYTE] * padding_len)
        elif metadata_size_with_size > node_headers_sizes.obfuscation_key:
            padding_len = node_headers_sizes.obfuscation_key - (
                metadata_size_with_size % node_headers_sizes.obfuscation_key
            )
            padding = bytes([PADDING_BYTE] * padding_len)

        return padding

    def serialise(self) -> bytes:
        node_type = self.node.get_type()
        # * Bytes of len 1 & in big endian. Have to specify for python <= 3.10
        prefix_len_bytes: bytes = len(self.prefix).to_bytes(1, "big")
        node_fork_sizes: NodeForkSizes = NodeForkSizes()

        prefix_bytes = bytearray(node_fork_sizes.prefix_max_size)
        prefix_bytes[: len(self.prefix)] = self.prefix

        entry: Optional[Reference] = self.node.get_content_address()

        if entry is None:
            msg = "Cannot serialise MantarayFork because it does not have content_address"
            raise ValueError(msg)

        data = bytes([node_type]) + prefix_len_bytes + prefix_bytes + entry

        if self.node.is_with_metadata_type():
            # console.log(json.dumps(self.node.get_metadata()).replace(' ', ''))
            json_string = json.dumps(self.node.get_metadata()).replace(" ", "")
            # * the uploaded data returned by the bee is very odd. All white spaces are removed from dictionary key pars
            # * but the spaces after a `;` is kept as it is. So this is a hacky wat to fix this issue.
            # * First remove all white spaces then replace the `;` with a `;` and a spaced followed by ;)
            json_string = json_string.replace(";", "; ")
            # * default utf-8 encoding
            metadata_bytes = json_string.encode()

            metadata_size_with_size = len(metadata_bytes) + node_fork_sizes.metadata
            padding = self.__create_metadata_padding(metadata_size_with_size)

            metadata_bytes_size = (len(metadata_bytes) + len(padding)).to_bytes(2, byteorder="big")

            return data + metadata_bytes_size + metadata_bytes + padding

        return data

    @classmethod
    def deserialise(
        cls, data: bytes, obfuscation_key: bytes, options: Optional[dict[str, dict[str, int]]] = None
    ) -> "MantarayFork":
        node_type = data[0]
        prefix_length = data[1]
        node_fork_sizes: NodeForkSizes = NodeForkSizes()

        if prefix_length == 0 or prefix_length > node_fork_sizes.prefix_max_size:
            msg = f"Prefix length of fork is greater than {node_fork_sizes.prefix_max_size}. Got: {prefix_length}"
            raise ValueError(msg)

        header_size: int = node_fork_sizes.header
        prefix = data[header_size : header_size + prefix_length]
        node: MantarayNode = MantarayNode()
        node.set_obfuscation_key(obfuscation_key)

        with_metadata = options.get("with_metadata") if options else None

        if with_metadata:
            ref_bytes_size = with_metadata["ref_bytes_size"]
            metadata_byte_size = with_metadata["metadata_byte_size"]

            if metadata_byte_size > 0:
                entry_start = node_fork_sizes.pre_reference
                entry_end = entry_start + ref_bytes_size
                node.set_entry(data[entry_start:entry_end])

                start_metadata = entry_end + node_fork_sizes.metadata
                metadata_bytes = data[start_metadata : start_metadata + metadata_byte_size]

                json_string = metadata_bytes.decode("utf-8")
                node.set_metadata(json.loads(json_string))
        else:
            entry_start = node_fork_sizes.pre_reference
            node.set_entry(data[entry_start:])

        node.set_type(node_type)
        # * For some reason recursive save is making the last level fork nodes to None. To fix it tweaking the logic
        # ! FIXME: this condition should never happpen. Most likely some recursive fn. is breaking
        # if node.forks is None:
        #     node.forks = {}
        # console.log(f"-->{node.forks=}")
        return cls(prefix=prefix, node=node)


class MantarayNode(BaseModel):
    # * Used with NodeType type
    __type: Optional[int] = None
    __obfuscation_key: Optional[bytes] = None
    # * reference of a loaded manifest node. if undefined i.e. None, the node can be handled as `dirty`
    __content_address: Optional[Reference] = None
    # * reference of an content that the manifest refers to
    __entry: Optional[Reference] = None
    __metadata: Optional[MetadataMapping] = None
    # * Forks of the manifest. Has to be initialized with `{}` on load even if there were no forks
    forks: Optional[ForkMapping] = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, MantarayNode):
            return False

        # Check if forks are the same length
        if len(self.forks) != len(other.forks):  # type: ignore
            return False

        # Compare each fork
        for key in self.forks:  # type: ignore
            if key not in other.forks:  # type: ignore
                return False
            if self.forks[key] != other.forks[key]:  # type: ignore
                return False

        return True

    def __hash__(self) -> int:
        """
        A class that implements __eq__ but not __hash__ will have its hash method implicitly set
        to None. This will cause the class to be unhashable, will in turn cause issues when
        using the class as a key in a dictionary or a member of a set.
        * https://docs.astral.sh/ruff/rules/eq-without-hash/
        """
        return hash(self.forks)

    def set_content_address(self, content_address: Reference) -> None:
        check_reference(content_address)
        self.__content_address = content_address

    def set_entry(self, entry: Reference) -> None:
        check_reference(entry)
        self.__entry = entry
        if not equal_bytes(entry, bytes(len(entry))):
            self.__make_value()
        self.make_dirty()

    def set_type(self, _type: int) -> None:
        if _type > NODE_SIZE:
            msg = f"Node type representation cannot be greater than {NODE_SIZE}"
            raise ValueError(msg)
        self.__type = _type

    def set_obfuscation_key(self, obfuscation_key: bytes) -> None:
        if not isinstance(obfuscation_key, bytes):
            msg = "Given obfuscation_key is not a bytes instance."
            raise TypeError(msg)
        if len(obfuscation_key) != 32:  # noqa: PLR2004
            msg = "Wrong obfuscation_key length. Entry can only be 32 bytes in length"
            raise ValueError(msg)
        self.__obfuscation_key = obfuscation_key
        self.make_dirty()

    def set_metadata(self, metadata: MetadataMapping) -> None:
        self.__metadata = metadata
        self.__make_with_metadata()
        if metadata.get("website-index-document") or metadata.get("website-error-document"):
            self.__make_value()
        self.make_dirty()

    def get_obfuscation_key(self) -> Optional[bytes]:
        return self.__obfuscation_key

    def get_entry(self) -> Optional[Reference]:
        return self.__entry

    def get_content_address(self) -> Optional[Reference]:
        return self.__content_address

    def get_metadata(self) -> Optional[MetadataMapping]:
        return self.__metadata

    def get_type(self) -> int:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        if self.__type > NODE_SIZE:
            msg = "Property 'type' in Node is greater than NODE_SIZE"
            raise ValueError(msg)
        return self.__type

    # * Node type related functions
    # * dirty flag is not necessary to be set

    def is_value_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type & NodeType.value.value == NodeType.value.value

    def is_edge_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type & NodeType.edge.value == NodeType.edge.value

    def is_with_path_separator_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type & NodeType.with_path_separator.value == NodeType.with_path_separator.value

    def is_with_metadata_type(self) -> bool:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        return self.__type & NodeType.with_metadata.value == NodeType.with_metadata.value

    def __make_value(self) -> None:
        if self.__type is None:
            self.__type = NodeType.value.value
        self.__type |= NodeType.value.value

    def __make_edge(self) -> None:
        if self.__type is None:
            self.__type = NodeType.edge.value
        self.__type |= NodeType.edge.value

    def __make_with_path_separator(self) -> None:
        if self.__type is None:
            self.__type = NodeType.with_path_separator.value
        self.__type |= NodeType.with_path_separator.value

    def __make_with_metadata(self) -> None:
        if self.__type is None:
            self.__type = NodeType.with_metadata.value
        self.__type |= NodeType.with_metadata.value

    def __make_not_with_path_separator(self) -> None:
        if self.__type is None:
            raise PropertyIsUndefinedError()
        self.__type = (NodeType.mask.value ^ NodeType.with_path_separator.value) & self.__type

    def __update_with_path_separator(self, path: bytes) -> None:
        if PATH_SEPARATOR in path[1:]:
            self.__make_with_path_separator()
        else:
            self.__make_not_with_path_separator()

    # ? BL methods

    def add_fork(self, path: bytes, entry: Reference, metadata: Optional[MetadataMapping] = None) -> None:
        """
        Adds a fork to the current node based on the provided path, entry, and metadata.

        Parameters:
        - path (bytes): A byte array representing the path. Can be empty, in which case `entry`
        will be set as the current node's entry.
        - entry (Reference): The entry to be associated with the fork.
        - metadata (Optional[MetadataMapping]): Additional metadata to associate with the fork.
        Defaults to an empty dictionary.

        Returns:
        None
        """
        if metadata is None:
            metadata = {}

        if len(path) == 0:
            self.set_entry(entry)
            if metadata:
                self.set_metadata(metadata)
            self.make_dirty()
            return

        if self.is_dirty() and self.forks is None:
            self.forks = {}

        if self.forks is None:
            msg = "Fork mapping is not defined in the manifest"
            raise ValueError(msg)

        fork: MantarayFork = self.forks.get(path[0])  # type: ignore

        if not fork:
            new_node: MantarayNode = MantarayNode()
            if self.__obfuscation_key:
                new_node.set_obfuscation_key(self.__obfuscation_key)

            node_fork_sizes: NodeForkSizes = NodeForkSizes()
            # * check for prefix size limit
            if len(path) > node_fork_sizes.prefix_max_size:
                prefix = path[: node_fork_sizes.prefix_max_size]
                rest = path[node_fork_sizes.prefix_max_size :]
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
            # * move current common prefix node
            new_node = MantarayNode()
            new_node.set_obfuscation_key(self.__obfuscation_key or bytes(32))
            fork.node.__update_with_path_separator(rest_path)
            new_node.forks = {rest_path[0]: MantarayFork(prefix=rest_path, node=fork.node)}
            new_node.__make_edge()

            # * if common path is full path new node is value type
            if len(path) == len(common_path):
                new_node.__make_value()

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
        - path (bytes): The path in bytes.

        Returns:
        Optional[MantarayFork]: The MantarayFork object with the last unique prefix and its node, or None if not found.

        Raises:
        ValueError: If there is no node under the given path.
        """
        if not path:
            raise EmptyPathError()

        if self.forks is None:
            msg = "Fork mapping is not defined in the manifest"
            raise ValueError(msg)

        fork: MantarayFork = self.forks.get(path[0])  # type: ignore
        # print(f"{path=}")
        if fork is None:
            raise NotFoundError(path, fork.prefix)

        if path.startswith(fork.prefix):
            rest = path[len(fork.prefix) :]
            if not rest:
                return fork
            return fork.node.get_fork_at_path(rest)
        else:
            raise NotFoundError(path, fork.prefix)

    def remove_path(self, path: bytes) -> None:
        """
        Removes a path from the node.

        Parameters:
        - path (bytes): The path in bytes.
        """
        if len(path) == 0:
            msg = "Path is empty"
            raise ValueError(msg)
        if self.forks is None:
            msg = "Fork mapping is not defined in the manifest"
            raise ValueError(msg)

        fork: MantarayFork = self.forks.get(path[0])  # type: ignore
        if fork is None:
            raise NotFoundError(path)

        if path.startswith(fork.prefix):
            rest = path[len(fork.prefix) :]

            # console.print(f"{rest.hex()=}")
            # console.print(f"{path[0]}")
            # console.print(f"{self.forks[path[0]]=}")

            if len(rest) == 0:
                self.make_dirty()
                del self.forks[path[0]]
                return
            else:
                fork.node.remove_path(rest)
        else:
            raise NotFoundError(path, fork.prefix)

    def load(self, storage_loader: StorageLoader, reference: Reference) -> None:
        if not reference:
            msg = "Reference is undefined at manifest load"
            raise ValueError(msg)
        data = storage_loader(reference)
        console.log(f"Data from bee: {data.hex()=}")
        self.deserialise(data)
        self.set_content_address(reference)

    def save(self, storage_saver: StorageSaver) -> Reference:
        """
        Saves dirty flagged ManifestNodes and its forks recursively.

        Parameters:
        - StorageSaver (StorageSaver): An instance of StorageSaver responsible for saving data.

        Returns:
        - Reference: Reference of the top manifest node.
        """
        result = self.__recursive_save(storage_saver)
        return result.get("reference")  # type: ignore

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

    def serialise(self) -> bytes:
        """
        serialises the node and its forks into a byte array.

        Returns:
        - bytes: serialised byte array representation of the node.
        """
        if not self.__obfuscation_key:
            self.set_obfuscation_key(bytes(32))
            # self.set_obfuscation_key(
        if self.forks is None:
            if not self.__entry:
                msg = "Entry"
                raise UndefinedFieldError(msg)
            # * if there were no forks initialized it is not intended to be
            self.forks = {}
        if not self.__entry:
            self.__entry = bytes(32)

        # Header
        version: MarshalVersion = "0.2"
        version_bytes: bytes = serialise_version(version)
        # * Entry is already in byte version
        reference_len_bytes: bytes = serialise_reference_len(self.__entry)

        # ForksIndexBytes
        index: IndexBytes = IndexBytes()
        for fork_index in self.forks.keys():
            index.set_byte(int(fork_index))
        index_bytes = index.get_bytes()

        # Forks
        fork_serialisations: bytearray = bytearray([])

        for byte in range(256):
            byte = int(byte)
            if index.check_byte_present(byte):
                fork: MantarayFork = self.forks.get(byte)  # type: ignore
                if fork is None:
                    msg = f"Fork indexing error: fork has not found under {byte!r} index"
                    raise Exception(msg)
                fork_serialisations += bytearray(fork.serialise())

        # console.print(f"{bytearray(self.__obfuscation_key)=}")
        # console.print(f"{version_bytes=}")
        # console.print(f"{reference_len_bytes=}")
        # console.print(f"{self.__entry=}")
        # console.print(f"{index_bytes=}")
        # console.print(f"{fork_serialisations=}")

        bytes_data = b"".join(
            [
                self.__obfuscation_key,  # type: ignore
                version_bytes,
                reference_len_bytes,
                self.__entry,
                index_bytes,
                flatten_bytes_array(fork_serialisations),
            ]
        )

        # Encryption
        # perform XOR encryption on bytes after obfuscation key
        bytes_data = encrypt_decrypt(self.__obfuscation_key, bytes_data, len(self.__obfuscation_key))  # type:ignore

        # print(f"{list(bytearray(bytes_data))=}")

        return bytes_data

    def deserialise(self, data: bytes) -> None:
        """
        Deserialises a byte array back into a node.

        Parameters:
        - data (bytes): Byte array representation of the node.
        """
        node_header_sizes = NodeHeaderSizes()
        node_header_size = node_header_sizes.full

        if len(data) < node_header_size:
            msg = "The serialised input is too short"
            raise ValueError(msg)

        self.__obfuscation_key = data[: node_header_sizes.obfuscation_key]
        data = encrypt_decrypt(self.__obfuscation_key, data, len(self.__obfuscation_key))  # type: ignore

        version_hash = data[
            node_header_sizes.obfuscation_key : node_header_sizes.obfuscation_key + node_header_sizes.version_hash
        ]

        if equal_bytes(version_hash, serialise_version("0.1")):
            raise NotImplementedError()
        elif equal_bytes(version_hash, serialise_version("0.2")):
            ref_bytes_size = data[node_header_size - 1]
            entry = data[node_header_size : node_header_size + ref_bytes_size]

            # FIXME: in Bee. if one uploads a file on the bzz endpoint, the node under `/` gets 0 refsize
            if ref_bytes_size == 0:
                entry = bytes(32)
            self.set_entry(bytes(entry))
            offset = node_header_size + ref_bytes_size
            index_bytes = data[offset : offset + 32]

            """
            Currently we don't persist the root nodeType when we marshal the manifest, as a result
            the root nodeType information is lost on Unmarshal. This causes issues when we want to
            perform a path 'Walk' on the root. If there is at least 1 fork, the root node type
            is an edge, so we will deduce this information from index byte array
            """

            if not equal_bytes(index_bytes, bytes(32)):
                self.__make_edge()
            self.forks = {}
            index_forks: IndexBytes = IndexBytes()
            index_forks.set_bytes(bytearray(index_bytes))
            offset += 32
            node_fork_sizes = NodeForkSizes()

            for byte in range(256):
                if index_forks.check_byte_present(byte):
                    if len(data) < offset + node_fork_sizes.node_type:
                        msg = f"There is not enough size to read nodeType of fork at offset {offset}"
                        raise ValueError(msg)

                    node_type = data[offset : offset + node_fork_sizes.node_type]
                    node_fork_size = node_fork_sizes.pre_reference + ref_bytes_size

                    if node_type_is_with_metadata_type(node_type[0]):
                        if (
                            len(data)
                            < offset + node_fork_sizes.pre_reference + ref_bytes_size + node_fork_sizes.metadata
                        ):
                            msg = f"Not enough bytes for metadata node fork at byte {byte}"
                            raise ValueError(msg)

                        metadata_byte_size = int.from_bytes(
                            data[offset + node_fork_size : offset + node_fork_size + node_fork_sizes.metadata],
                            byteorder="big",
                        )
                        node_fork_size += node_fork_sizes.metadata + metadata_byte_size

                        fork = MantarayFork.deserialise(
                            data[offset : offset + node_fork_size],
                            self.__obfuscation_key,
                            {
                                "with_metadata": {
                                    "ref_bytes_size": ref_bytes_size,
                                    "metadata_byte_size": metadata_byte_size,
                                }
                            },
                        )
                    else:
                        if len(data) < offset + node_fork_sizes.pre_reference + ref_bytes_size:
                            msg = f"There is not enough size to read fork at offset {offset}"
                            raise ValueError(msg)

                        fork = MantarayFork.deserialise(data[offset : offset + node_fork_size], self.__obfuscation_key)
                    self.forks[byte] = fork
                    offset += node_fork_size
        else:
            msg = "Wrong mantaray version"
            raise ValueError(msg)

    def __recursive_save(self, storage_saver: StorageSaver) -> dict:
        """
        Recursively saves the node and its forks.

        Parameters:
        - StorageSaver (StorageSaver): An instance of StorageSaver responsible for saving data.

        Returns:
        - dict: A dictionary containing the reference of the top manifest node and a
        flag indicating if the node was changed.
        """
        # * Save forks first recursively
        save_returns = []

        # * There was no intention to define fork(s)
        if self.forks is None:
            self.forks = {}

        for fork in self.forks.values():
            save_returns.append(fork.node.__recursive_save(storage_saver))

        if self.__content_address and all(not v["changed"] for v in save_returns):
            return {"reference": self.__content_address, "changed": False}

        # Save the actual manifest as well
        data = self.serialise()
        reference = storage_saver(data)
        self.set_content_address(reference)

        return {"reference": reference, "changed": True}


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
        # 2
        return self.node_type + self.prefix_length

    @property
    def prefix_max_size(self) -> int:
        # 30
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


def node_type_is_with_metadata_type(node_type: int) -> bool:
    return node_type & NodeType.with_metadata.value == NodeType.with_metadata.value


def check_for_separator(node: MantarayNode) -> bool:
    """
    Checks for a separator character in the node and its descendants' prefixes.

    Parameters:
    - node (MantarayNode): The node to check for a separator character.

    Returns:
    - bool: True if a separator character is found, False otherwise.
    """
    if not node.forks:
        return False

    for fork in node.forks.values():
        if any(v == PATH_SEPARATOR_BYTE for v in fork.prefix):
            return True

        if check_for_separator(fork.node):
            return True

    return False


# * The hash length has to be 31 instead of 32 that comes from the keccak hash function
def serialise_version(version: Union[MarshalVersion, str]) -> bytes:
    """
    serialises the version into a 31-byte hash.

    Parameters:
    - version (str): The version string to serialise.

    Returns:
    - bytes: The serialised version as a 31-byte hash.
    """
    version_name = "mantaray"
    version_separator = ":"
    hash_bytes = keccak(text=(version_name + version_separator + version))

    return hash_bytes[:31]  # type: ignore


def serialise_reference_len(entry: Reference) -> bytes:
    """
    serialises the reference length into a single byte.

    Parameters:
    - entry (int): The reference length.

    Returns:
    - bytes: The serialised reference length as a single byte.
    """
    reference_len = len(entry)
    if reference_len not in {32, 64}:
        msg = f"Wrong referenceLength. It can be only 32 or 64. Got: {reference_len}"
        raise ValueError(msg)

    # serialise the reference length into a single byte
    byte_array = (reference_len).to_bytes(reference_len, byteorder="big", signed=False)
    # Remove leading and trailing zeros
    return bytearray(byte_array.strip(b"\x00"))


def load_all_nodes(storage_loader: StorageLoader, node: MantarayNode) -> None:
    """
    Loads all nodes recursively.

    Parameters:
    - storage_loader: The storage loader object used for loading nodes.
    - node: The initial node from which to start loading.
    """
    if not node.forks:
        return

    for fork in node.forks.values():
        if fork.node.get_entry():
            fork.node.load(storage_loader, fork.node.get_entry())
        load_all_nodes(storage_loader, fork.node)


def equal_nodes(a: MantarayNode, b: MantarayNode, accumulated_prefix: str = "") -> None:
    """
    Compares two MantarayNode instances recursively and raises an exception if they are not equal.

    Parameters:
    - a (MantarayNode): The first node to compare.
    - b (MantarayNode): The second node to compare.
    - accumulated_prefix (str): Accumulates the prefix during the recursion.

    Raises:
    - ValueError: If the nodes are not equal.
    """
    # Node type comparison
    if getattr(a, "__type", None) != getattr(b, "__type", None):
        msg = f"Nodes do not have the same type at prefix \"{accumulated_prefix}\".\na: {getattr(a, '__type', None)} <-> b: {getattr(b, '__type', None)}"  # noqa: E501
        raise ValueError(msg)

    # Node metadata comparison
    a_metadata = getattr(a, "__metadata", None)
    b_metadata = getattr(b, "__metadata", None)
    if a_metadata is not b_metadata:
        msg = "One of the nodes does not have metadata defined."
        raise ValueError(msg)

    if a_metadata is not None and b_metadata is not None:
        try:
            a_metadata_str = json.dumps(a_metadata)
            b_metadata_str = json.dumps(b_metadata)
        except Exception as exc:
            msg = f"Either of the nodes has invalid JSON metadata.\n a: {a_metadata}\n b: {b_metadata}"
            raise ValueError(msg) from exc

        if a_metadata_str != b_metadata_str:
            msg = f"The nodes' metadata are different.\na: {a_metadata_str}\nb: {b_metadata_str}"
            raise ValueError(msg)

    # Node entry comparison
    if getattr(a, "__entry", None) == getattr(b, "__entry", None):
        msg = f"Nodes do not have the same entries.\n a: {getattr(a, '__entry', None)} \n b: {getattr(b, '__entry', None)}"  # noqa: E501
        raise ValueError(msg)

    if getattr(a, "forks", None) is None:
        return

    # Node fork comparison
    a_keys = list(a.forks.keys())  # type: ignore
    if getattr(b, "forks", None) is None or len(a_keys) != len(list(b.forks.keys())):  # type: ignore
        msg = f"Nodes do not have the same fork length on equality check at prefix {accumulated_prefix}"
        raise ValueError(msg)

    for key in a_keys:
        a_fork = a.forks[int(key)]  # type: ignore
        b_fork = b.forks[int(key)]  # type: ignore
        prefix = a_fork["prefix"]
        prefix_string = "".join(chr(p) for p in prefix)

        if not equal_bytes(prefix, b_fork["prefix"]):
            msg = f'Nodes do not have the same prefix under the same key "{key}" at prefix {accumulated_prefix}'
            raise ValueError(msg)

        equal_nodes(a_fork["node"], b_fork["node"], accumulated_prefix + prefix_string)

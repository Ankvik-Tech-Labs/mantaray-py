from typing import Callable, Optional, Union

from eth_utils import keccak
from pydantic import BaseModel, ConfigDict, Field

from mantaray_py.types import Reference, get_random_values

BYTES_LENGTH = 32


class IndexBytes(BaseModel):
    bytes_data: bytearray = Field(bytearray(32), min_length=BYTES_LENGTH, max_length=BYTES_LENGTH)
    model_config = ConfigDict(arbitrary_types_allowed=True)

    def set_byte(self, byte: int) -> None:
        """Set a byte value."""
        if byte > 255:  # noqa: PLR2004
            msg = f"IndexBytes setByte error: {byte} is greater than 255"
            raise ValueError(msg)
        self.bytes_data[byte // 8] |= 1 << byte % 8

    def set_bytes(self, byte_array: bytearray) -> None:
        check_bytes(byte_array, 32)
        self.bytes_data = byte_array

    def get_bytes(self) -> bytes:
        return bytes(self.bytes_data)

    def check_byte_present(self, byte: int) -> bool:
        """Check if a byte is present."""
        return (self.bytes_data[byte // 8] >> byte % 8) & 1 > 0

    def for_each(self, hook: Callable[[int], None]) -> None:
        """Iterate through the indexed byte values."""
        for i in range(256):
            if self.check_byte_present(i):
                hook(i)


def check_reference(ref: Union[Reference, bytes]) -> None:
    if not isinstance(ref, bytes):
        msg = "Given Reference is not a valid bytes instance"
        raise TypeError(msg)
    if len(ref) not in {32, 64}:
        msg = "Wrong reference length. Entry only can be 32 or 64 length in bytes"
        raise ValueError(msg)


def check_bytes(data: bytearray, length: int) -> None:
    """
    Checks if the given bytes are of the correct type and length.

    Args:
        data (bytes): The bytes to check.
        length (int): The expected length of the bytes.

    Raises:
        ValueError: If bytes is not an instance of bytes.
        ValueError: If the length of bytes is not equal to the expected length.
    """
    if not isinstance(data, bytearray):
        msg = "Cannot set given bytes, because it is not a bytearray type"
        raise ValueError(msg)

    if len(data) != BYTES_LENGTH:
        msg = f"Cannot set given bytes, because it does not have {length} length. Got {len(data)}"
        raise ValueError(msg)


def find_index_of_array(element: bytes, search_for: bytes) -> int:
    """
    Finds starting index `search_for` in `element` byte arrays

    If `search_for` is not found in `element` it returns -1

    Args:
        element (bytes): The byte array to search in.
        search_for (bytes): The byte array to search for.

    Returns:
        int: starting index of `search_for` in `element` or -1 if not found.
    """
    for i in range(len(element) - len(search_for) + 1):
        for j in range(len(search_for)):
            if element[i + j] != search_for[j]:
                break
        else:
            return i
    return -1


def overwrite_bytes(a: bytes, b: bytes, i: Optional[int] = 0) -> bytes:
    """
    Overwrites `a` byte array's elements with elements of `b` starting from `i`.

    Args:
        a (bytes): The byte array to be overwritten.
        b (bytes): The byte array to copy from.
        i (int, optional): The starting index in `a` where `b` should be copied. Defaults to 0.
    Retuns:
        a (bytes): The overwritten byte array.
    Raises:
        ValueError: If `a` is not long enough to hold `b` from index `i`.
    """
    if len(a) < len(b) + i:  # type: ignore
        msg = f"Cannot copy bytes because the base byte array length is lesser ({len(a)}) than the others ({len(b)})."
        raise ValueError(msg)

    a[i : i + len(b)] = b  # type: ignore

    return a


def flatten_bytes_array(bytes_array: bytearray) -> bytes:
    """
    Flattens the given list that consists of byte arrays.

    Args:
        bytes_array (bytearray): The list of byte arrays to flatten.

    Returns:
        bytes: A flattened byte array.
    """
    # if len(bytes_array) == 0:
    #     return b""

    # bytes_length = len(bytes_array)
    # flatten_bytes = bytearray(bytes_length)
    # next_write_index = 0
    # for b in bytes_array:
    #     flatten_bytes = bytearray(overwrite_bytes(flatten_bytes, b, next_write_index))  # type: ignore
    #     next_write_index += len(b)  # type: ignore

    return bytes(bytes_array)


def equal_bytes(a: bytes, b: bytes) -> bool:
    """Returns True if the two byte arrays are equal, False otherwise.

    Args:
        a: The first byte array to compare.
        b: The second byte array to compare.

    Returns:
        True if the two byte arrays are equal, False otherwise.
    """

    if len(a) != len(b):
        return False

    return all(a[i] == b[i] for i in range(len(a)))


def encrypt_decrypt(
    key: bytes, data: bytes, start_index: Optional[int] = 0, end_index: Optional[int] = None
) -> Optional[bytes]:
    """
    Runs a XOR operation on data, encrypting it if it hasn't already been,
    and decrypting it if it has, using the key provided.

    Args:
        key (bytes): The byte array used as the key.
        data (bytes): The byte array to be encrypted or decrypted.
        start_index (int, optional): The starting index in `data` where the operation should start. Defaults to 0.
        end_index (int, optional): The ending index in `data` where the operation should end which defaults to None, which means the operation will go until the end of `data`.

    Returns:
        Optional[bytes]: The encrypted or decrypted byte array, or None if the operation cannot be performed.
    """  # noqa: E501
    if key == bytes(BYTES_LENGTH):
        return data

    if end_index is None:
        end_index = len(data)

    data = bytearray(data)
    for i in range(start_index, end_index, len(key)):  # type: ignore
        max_chunk_index = i + len(key)
        encryption_chunk_end_index = min(max_chunk_index, len(data))
        encryption_chunk = data[i:encryption_chunk_end_index]
        for j in range(len(encryption_chunk)):
            encryption_chunk[j] ^= key[j % len(key)]
        data[i:encryption_chunk_end_index] = encryption_chunk
    return data


def keccak256_hash(*messages: Union[str, bytes, bytearray]) -> bytes:
    """
    Helper function for calculating the keccak256 hash with

    Args:
        messages: Any number of messages (bytes, byte arrays or text)
    Returns:
        bytes
    """

    if isinstance(messages, str):
        return keccak(text=messages)

    combined = bytearray()
    for message in messages:
        if not isinstance(message, bytearray) and not isinstance(message, bytes):
            msg = f"Input should be either a string, bytes or bytearray: got {type(message)}."
            raise TypeError(msg)
        combined += message

    return keccak(combined)  # type: ignore


def gen_32_bytes() -> bytes:
    """
    Generates a bytearray of 32 random bytes.

    This function creates a bytearray of 32 bytes filled with random values generated by the
    operating system's secure random number generator. The resulting bytearray can be used for
    various cryptographic or security-related applications where random data is required.

    Returns:
        bytes: A byte array of length 32.
    """
    return get_random_values(BYTES_LENGTH)


def common(a: bytes, b: bytes) -> bytes:
    """
    Returns the common bytes of the two given byte arrays until the first byte difference.

    Args:
        a (bytes): The first byte array.
        b (bytes): The second byte array.

    Returns:
        bytes: The common bytes of `a` and `b` until the first byte difference.
    """
    common_bytes = bytearray()

    for byte_a, byte_b in zip(a, b):
        if byte_a == byte_b:
            common_bytes.append(byte_a)
        else:
            break

    return bytes(common_bytes)

from typing import Optional, Union

from mantaray_py.types import Bytes, Reference


def check_reference(ref: Union[Reference, Bytes]) -> None:
    if not isinstance(ref, Bytes):
        raise TypeError('Given Reference is not a valid bytes instance')
    if ref.length != 32 and ref.length != 64:
        raise ValueError('Wrong reference length. Entry only can be 32 or 64 length in bytes')


def check_bytes(data: bytes, length: int) -> None:
    """
    Checks if the given bytes are of the correct type and length.

    Args:
        data (bytes): The bytes to check.
        length (int): The expected length of the bytes.

    Raises:
        ValueError: If bytes is not an instance of bytes.
        ValueError: If the length of bytes is not equal to the expected length.
    """
    if not isinstance(data, bytes):
        raise ValueError('Cannot set given bytes, because it is not a bytes type')

    if len(data) != 32:
        raise ValueError(f'Cannot set given bytes, because it does not have {length} length. Got {len(data)}')


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
    if len(a) < len(b) + i:
        raise ValueError(
            f'Cannot copy bytes because the base byte array length is lesser ({len(a)}) than the others ({len(b)}).'
        )

    a[i : i + len(b)] = b

    return a


def flatten_bytes_array(bytes_array: bytearray) -> bytes:
    """
    Flattens the given list that consists of byte arrays.

    Args:
        bytes_array (bytearray): The list of byte arrays to flatten.

    Returns:
        bytes: A flattened byte array.
    """
    if len(bytes_array) == 0:
        return b''

    bytes_length = sum(len(v) for v in bytes_array)
    flatten_bytes = bytearray(bytes_length)
    next_write_index = 0
    for b in bytes_array:
        flatten_bytes = overwrite_bytes(flatten_bytes, b, next_write_index)
        next_write_index += len(b)

    return bytes(flatten_bytes)


def bytes_equal(a: bytes, b: bytes) -> bool:
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


def encrypt_decrypt(key: bytes, data: bytes, start_index: Optional[int] = 0, end_index: Optional[int] = None) -> None:
    """
    Runs a XOR operation on data, encrypting it if it hasn't already been,
    and decrypting it if it has, using the key provided.

    Args:
        key (bytes): The byte array used as the key.
        data (bytes): The byte array to be encrypted or decrypted.
        start_index (int, optional): The starting index in `data` where the operation should start. Defaults to 0.
        end_index (int, optional): The ending index in `data` where the operation should end.
        Defaults to None, which means the operation will go until the end of `data`.
    """
    if key == bytes(32):
        return

    if end_index is None:
        end_index = len(data)

    for i in range(start_index, end_index, len(key)):
        max_chunk_index = i + len(key)
        encryption_chunk_end_index = min(max_chunk_index, len(data))
        encryption_chunk = bytearray(data[i:encryption_chunk_end_index])
        for j in range(len(encryption_chunk)):
            encryption_chunk[j] ^= key[j % len(key)]
        data[i:encryption_chunk_end_index] = encryption_chunk


# def keccak256_hash(*messages: Union[bytes, bytearray]) -> bytes:
#     """
#     Helper function for calculating the keccak256 hash with

#     Args:
#         messages: Any number of messages (bytes, byte arrays)
#     Returns:
#         bytes
#     """
#     combined = bytearray()
#     for message in messages:
#         if not isinstance(message, bytearray) and not isinstance(message, bytes):
#             msg = f"Input should be either a string, bytes or bytearray: got {type(message)}."
#             raise TypeError(msg)
#         combined += message

#     return keccak(combined)

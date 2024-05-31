import secrets


def get_random_values(byte_size: int) -> bytes:
    return secrets.token_bytes(byte_size)

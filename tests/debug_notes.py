# BEE_POSTAGE = "b8f5483c9282fe0c8f8614ab537a3ecd8a452e2944fb09b9d8080c6baa04d560"
rand_address = bytearray(
    b"\xe5\x05\xf7\x9d\xd3\xa7\xc4\xa4R\r\x81\x8bK_:+\xbc)4\x1b4\xdd\xf2\x8c\x96Q\xbdZ\xb8x\x13\x1f"
)
import asyncio
from pathlib import Path
from typing import Callable

import pytest
from bee_py.bee import Bee
from bee_py.types.type import REFERENCE_HEX_LENGTH, Data
from bee_py.utils.hex import bytes_to_hex, hex_to_bytes
from rich.console import Console
from rich.traceback import install

from mantaray_py import (MantarayNode, Reference, check_for_separator,
                         gen_32_bytes, init_manifest_node)
from mantaray_py.node import NotFoundError

install()

bee_class = Bee("https://1633-ethersphere-mantarayjs-32woopg7uie.ws-us114.gitpod.io/")
get_debug_postage = "637de2e976082847c4167d788176bac378229cfaa5e3022ccd661d714ec78a95"
node = MantarayNode()
# node.set_obfuscation_key(bytes(bytearray([103,106,146,247,187,80,45,232,176,88,116,225,58,212,119,244,75,70,204,242,246,4,124,66,127,64,50,134,94,118,52,58])))

# node.set_entry(bytes(rand_address))
# list(bytearray(node.serialise()))
# node.serialise()
test_dir = Path(
    "/home/avik/Desktop/git_projects/Organizations/Ankvik-Technologies/mantaray-py/tests/data/testpage"
)

upload_result = bee_class.upload_files_from_directory(
    get_debug_postage, test_dir, {"pin": True, "indexDocument": "index.html"}
)

index_html_path = test_dir / "index.html"
image_path = test_dir / "img" / "icon.png"
text_path = test_dir / "img" / "icon.png.txt"


def upload_data(data: bytes, get_debug_postage: str, bee_class: Bee) -> str:
    result = bee_class.upload_data(get_debug_postage, data)

    return str(result.reference)


async def upload_file(file_path: str, get_debug_postage: str, bee_class: Bee) -> str:
    """
    Read the file in raw bytes
    """
    with open(file_path, "rb") as file:
        data = file.read()
    return upload_data(data, get_debug_postage, bee_class)


index_reference, image_reference, text_reference = await asyncio.gather(
    upload_file(index_html_path, get_debug_postage, bee_class),
    upload_file(image_path, get_debug_postage, bee_class),
    upload_file(text_path, get_debug_postage, bee_class),
)

i_node = MantarayNode()
i_node.add_fork(
    "index.html".encode(),
    hex_to_bytes(index_reference),
    {"Content-Type": "text/html; charset=utf-8", "Filename": "index.html"},
)
i_node.add_fork(
    "img/icon.png.txt".encode(),
    hex_to_bytes(text_reference),
    {"Content-Type": "", "Filename": "icon.png.txt"},
)
i_node.add_fork(
    "index.html".encode(),
    hex_to_bytes(image_reference),
    {"Content-Type": "image/png", "Filename": "img/icon.png"},
)
i_node.add_fork("/".encode(), bytes(32), {"website-index-document": "index.html"})

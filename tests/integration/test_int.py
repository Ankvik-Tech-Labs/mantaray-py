from pathlib import Path
import asyncio
import pytest
from typing import Callable
from bee_py.bee import Bee
from bee_py.types.type import Data
from rich.console import Console

from bee_py.utils.hex import bytes_to_hex, hex_to_bytes

from mantaray_py import Reference, MantarayNode

PROJECT_DIR = Path(__file__).resolve().parent.parent
console =  Console()

def create_save_function(bee_class: Bee, get_debug_postage: str) -> Callable[[bytes], bytes]:
    def save_function(data: bytes) -> bytes:
        console.print(f"{bytes_to_hex(data)=}")
        hex_reference = bee_class.upload_data(get_debug_postage, data)
        # console.print(f"{str(hex_reference.reference)=}")
        return hex_to_bytes(str(hex_reference.reference))
    return save_function


def load_function(address: bytes, bee_class: Bee) -> bytes:
    return bee_class.download_data(bytes_to_hex(address)).data


def upload_data(data: bytes, get_debug_postage: str, bee_class: Bee) -> str:
    result = bee_class.upload_data(get_debug_postage, data)

    return str(result.reference)


def bee_test_page_manifest_data(get_debug_postage: str, bee_class: Bee) -> Data:
    """
    Uploads the testpage directory with bee-py and return back its root manifest data
    """
    upload_result = bee_class.upload_files_from_directory(get_debug_postage, PROJECT_DIR / "testpage", {"pin": True, "indexDocument": "index.html"})

    # * Only download its manifest
    return bee_class.download_data(str(upload_result.reference))

async def upload_file(file_path: str, get_debug_postage: str, bee_class: Bee) -> str:
    """
    Read the file in raw bytes
    """
    with open(file_path, "rb") as file:
        data = file.read()
    return upload_data(data, get_debug_postage, bee_class)

# ? Tests
@pytest.mark.asyncio
async def test_should_generate_same_content_hash_as_bee(bee_class, get_debug_postage):
    test_dir = PROJECT_DIR / "data" / "testpage"
    upload_result = bee_class.upload_files_from_directory(get_debug_postage, test_dir, {"pin": True, "indexDocument": "index.html"})

    index_html_path = test_dir / "index.html"
    image_path = test_dir / "img" / "icon.png"
    text_path = test_dir / "img" / "icon.png.txt"

    index_reference, image_reference, text_reference = await asyncio.gather(
        upload_file(index_html_path, get_debug_postage, bee_class),
        upload_file(image_path, get_debug_postage, bee_class),
        upload_file(text_path, get_debug_postage, bee_class)
    )
    # console.log(index_reference, image_reference, text_reference)

    i_node = MantarayNode()
    i_node.add_fork("index.html".encode(), hex_to_bytes(index_reference), {"Content-Type": "text/html; charset=utf-8","Filename": "index.html"})
    i_node.add_fork("img/icon.png.txt".encode(), hex_to_bytes(text_reference), {"Content-Type": "", "Filename": "icon.png.txt"})
    i_node.add_fork("index.html".encode(), hex_to_bytes(image_reference), {"Content-Type": "image/png","Filename": "img/icon.png"})
    i_node.add_fork("/".encode(), bytes(32), {"website-index-document": "index.html"})
    # pytest.set_trace()

    save_function = create_save_function(bee_class, get_debug_postage)
    i_node_ref = i_node.save(save_function)

    assert str(upload_result.reference) == "e9d46950cdb17e15d0b3712bcb325724a3107560143d65a7acd00ea781eb9cd7"

    assert bytes_to_hex(i_node_ref) == upload_result.reference.value

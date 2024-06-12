from bee_py.bee import Bee
from bee_py.utils.hex import hex_to_bytes, bytes_to_hex
from bee_py.types.type import Data
from mantaray_py import Reference
from pathlib import Path

bee_url = "http://localhost:1633"
bee = Bee(bee_url)
PROJECT_DIR = Path(__file__)
postage_batch = "abcd"

def save_function(data: bytes) -> Reference:
    hex_reference = bee.upload_data(postage_batch, data)

    return hex_to_bytes(str(hex_reference.reference))

def load_function(address: bytes) -> bytes:
    return bee.download_data(bytes_to_hex(address)).data

def upload_data(data: bytes) -> str:
    result = bee.upload_data(postage_batch, data)

    return str(result.reference)

def bee_test_page_manifest_data() -> Data:
    """
    Uploads the testpage directory with bee-py and return back its root manifest data
    """
    upload_result = bee.upload_files_from_directory(postage_batch, PROJECT_DIR / "testpage", {"pin": True, "indexDocument": "index.html"})
    
    #* Only download its manifest
    return bee.download_data(str(upload_result.reference))
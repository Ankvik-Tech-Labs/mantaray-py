import json
import os
from pathlib import Path
from time import sleep

import pytest
import requests
from bee_py.bee import Bee
from bee_py.modules.debug.stamps import create_postage_batch, get_postage_batch
from bee_py.types.type import BatchId

from mantaray_py import MantarayNode, gen_32_bytes

PROJECT_PATH = Path(__file__).parent
ENV_FILE = PROJECT_PATH / "../.env"


@pytest.fixture
def get_sample_mantaray_node() -> dict[MantarayNode, bytes]:
    node = MantarayNode()
    random_address = gen_32_bytes()
    node.set_entry(random_address)

    paths = [
        "path1/valami/elso",
        "path1/valami/masodik",
        "path1/valami/masodik.ext",
        "path1/valami",
        "path2"
    ]

    for path in paths:
        encoded_path = path.encode()
        node.add_fork(encoded_path, random_address)

    return {
        "node": node,
        "paths": [path.encode() for path in paths],
    }


@pytest.fixture(scope="session", autouse=True)
def bee_api_url():
    if os.path.isfile(ENV_FILE):
        with open(ENV_FILE) as f:
            data = json.loads(f.read())
        if data["BEE_API_URL"]:
            BEE_API_URL = data["BEE_API_URL"]
    else:
        BEE_API_URL = "http://localhost:1633"

    return BEE_API_URL


@pytest.fixture(scope="session", autouse=True)
def bee_debug_url():
    if os.path.isfile(ENV_FILE):
        with open(ENV_FILE) as f:
            data = json.loads(f.read())
        if data["BEE_DEBUG_API_URL"]:
            BEE_DEBUG_API_URL = data["BEE_DEBUG_API_URL"]
    else:
        BEE_DEBUG_API_URL = "http://localhost:1635"

    return BEE_DEBUG_API_URL


@pytest.fixture
def bee_url(bee_api_url) -> str:
    return bee_api_url


@pytest.fixture
def bee_class(bee_url) -> Bee:
    return Bee(bee_url)


@pytest.fixture
def bee_ky_options(bee_url) -> dict:
    return {"baseURL": bee_url, "timeout": 300, "onRequest": True}


@pytest.fixture
def bee_peer_ky_options(bee_peer_url) -> dict:
    return {"baseURL": bee_peer_url, "timeout": 300, "onRequest": True}


@pytest.fixture
def bee_debug_ky_options(bee_debug_url) -> dict:
    return {"baseURL": bee_debug_url, "timeout": 300, "onRequest": True}


@pytest.fixture
def bee_debug_peer_ky_options(bee_peer_debug_url) -> dict:
    return {"baseURL": bee_peer_debug_url, "timeout": 300, "onRequest": True}


# * Not a fixture
def request_debug_postage_stamp(bee_debug_ky_options) -> BatchId:
    stamp: BatchId
    stamp = create_postage_batch(bee_debug_ky_options, 100, 20)

    if not stamp:
        msg = "There is no valid postage stamp"
        raise ValueError(msg)

    print("[*]Waiting for postage to be usable....")
    usable = None
    while True:
        try:
            usable = get_postage_batch(bee_debug_ky_options, stamp).usable
        except requests.exceptions.HTTPError:
            sleep(5)
        if usable:
            break
    print(f"[*]Valid Postage found: {stamp}")
    return stamp

@pytest.fixture
def get_cache_debug_postage_stamp(request, bee_debug_ky_options) -> BatchId:
    stamp = request.config.cache.get("debug_postage_stamp", None)

    if not stamp:
        print("[*]Getting postage stamp!....")
        stamp = request_debug_postage_stamp(bee_debug_ky_options)
        request.config.cache.set("debug_postage_stamp", stamp)
    return stamp


@pytest.fixture
def get_debug_postage() -> BatchId:
    print("[*]Getting Debug Postage....")
    return "413a6f2b6787a04e8d8514b8fc82d8eb4743c3e582c044e6d722ec0f39a02a28"
    return get_cache_debug_postage_stamp


@pytest.fixture
def bee_debug_url_postage(get_postage_batch) -> BatchId:
    return get_postage_batch("bee_debug_url")


@pytest.fixture
def bee_peer_debug_url_postage(get_postage_batch) -> BatchId:
    return get_postage_batch("bee_peer_debug_url")


@pytest.fixture
def bee_peer_debug_ky_options(bee_peer_debug_url):
    return {"baseURL": bee_peer_debug_url, "timeout": 300, "onRequest": True}

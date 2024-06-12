from mantaray_py import MantarayNode, gen_32_bytes
from pytest import fixture
from bee_py.bee import Bee
from bee_py.bee_debug import BeeDebug
from bee_py.modules.debug.chunk import delete_chunk_from_local_storage
from bee_py.modules.debug.connectivity import get_node_addresses
from bee_py.modules.debug.stamps import create_postage_batch, get_postage_batch
from bee_py.types.type import BatchId, Reference
from bee_py.utils.hex import bytes_to_hex

bee_url = "http://localhost:1633"

@fixture
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

@fixture
def bee_class() -> Bee:
    return Bee(bee_url)

@fixture
def bee_ky_options() -> dict:
    return {"baseURL": bee_url, "timeout": 300, "onRequest": True}

def request_postage_stamp(bee_ky_options) -> BatchId:
    stamp: BatchId
    stamp = create_postage_batch(bee_ky_options, 100, 20)

    if not stamp:
        msg = "There is no valid postage stamp"
        raise ValueError(msg)

    print("[*]Waiting for postage to be usable....") 
    while True:
        usable = get_postage_batch(bee_ky_options, stamp).usable
        if usable:
            break
    print(f"[*]Valid Postage found: {stamp}") 
    return stamp

@fixture
def get_cache_postage_stamp(request, bee_ky_options)-> BatchId:
    stamp = request.config.cache.get("debug_postage_stamp", None)

    if not stamp:
        print("[*]Getting postage stamp!....")
        stamp = request_postage_stamp(bee_ky_options)
        request.config.cache.set("debug_postage_stamp", stamp)
    return stamp


@fixture
def get_postage(get_cache_postage_stamp)-> BatchId:
    print("[*]Getting Debug Postage....")
    # return "b0a5239a968736020a56517b7bad14d4634d2147896e9bacd840ff56f20bb05b"
    return get_cache_postage_stamp
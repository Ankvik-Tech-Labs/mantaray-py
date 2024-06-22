import asyncio
from pathlib import Path
from typing import Callable

import pytest
from bee_py.bee import Bee
from bee_py.types.type import Data
from bee_py.utils.hex import bytes_to_hex, hex_to_bytes
from rich.console import Console

from mantaray_py import MantarayNode, load_all_nodes

PROJECT_DIR = Path(__file__).resolve().parent.parent
console = Console()


def create_save_function(
    bee_class: Bee, get_debug_postage: str
) -> Callable[[bytes], bytes]:
    def save_function(data: bytes) -> bytes:
        # console.print(f"{list(data)=}")
        hex_reference = bee_class.upload_data(get_debug_postage, data)
        # console.print(f"{str(hex_reference.reference)=}")
        return hex_to_bytes(str(hex_reference.reference))

    return save_function


def create_load_function(bee_class: Bee) -> Callable:
    def load_function(address: bytes) -> bytes:
        # console.print(f"{address.hex()=}")
        return bee_class.download_data(bytes_to_hex(address)).data

    return load_function


# def load_function(address:bytes) -> bytes:
#     console.print(f"{address=}")
#     bee_class = Bee("https://1633-ethersphere-mantarayjs-32woopg7uie.ws-us114.gitpod.io/")
#     return bee_class.download_data(bytes_to_hex(address)).data


def upload_data(data: bytes, get_debug_postage: str, bee_class: Bee) -> str:
    result = bee_class.upload_data(get_debug_postage, data)
    return str(result.reference)


def bee_test_page_manifest_data(get_debug_postage: str, bee_class: Bee) -> bytes:
    """
    Uploads the testpage directory with bee-py and return back its root manifest data
    """
    upload_result = bee_class.upload_files_from_directory(
        get_debug_postage,
        PROJECT_DIR / "data" / "testpage",
        {"pin": True, "indexDocument": "index.html"},
    )

    # * Only download its manifest
    return bee_class.download_data(str(upload_result.reference)).data


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
    upload_result = bee_class.upload_files_from_directory(
        get_debug_postage, test_dir, {"pin": True, "indexDocument": "index.html"}
    )

    index_html_path = test_dir / "index.html"
    image_path = test_dir / "img" / "icon.png"
    text_path = test_dir / "img" / "icon.png.txt"

    index_reference, image_reference, text_reference = await asyncio.gather(
        upload_file(index_html_path, get_debug_postage, bee_class),
        upload_file(image_path, get_debug_postage, bee_class),
        upload_file(text_path, get_debug_postage, bee_class),
    )
    # console.log(index_reference, image_reference, text_reference)

    i_node = MantarayNode()
    i_node.add_fork(
        b"index.html",
        hex_to_bytes(index_reference),
        {"Content-Type": "text/html; charset=utf-8", "Filename": "index.html"},
    )
    i_node.add_fork(
        b"img/icon.png.txt",
        hex_to_bytes(text_reference),
        {"Content-Type": "", "Filename": "icon.png.txt"},
    )
    i_node.add_fork(
        b"img/icon.png",
        hex_to_bytes(image_reference),
        {"Content-Type": "image/png", "Filename": "icon.png"},
    )
    i_node.add_fork(b"/", bytes(32), {"website-index-document": "index.html"})

    console.log(i_node.forks)

    save_function = create_save_function(bee_class, get_debug_postage)
    i_node_ref = i_node.save(save_function)

    assert (
        str(upload_result.reference)
        == "e9d46950cdb17e15d0b3712bcb325724a3107560143d65a7acd00ea781eb9cd7"
    )

    assert bytes_to_hex(i_node_ref) == upload_result.reference.value


def test_serialise_n_deserialise_the_same_as_Bee(bee_class, get_debug_postage):
    data = bee_test_page_manifest_data(get_debug_postage, bee_class)
    node = MantarayNode()

    node.deserialise(data)
    load_function = create_load_function(bee_class)
    load_all_nodes(load_function, node)

    serialisation = node.serialise()
    # console.print(f"{serialisation=}")

    assert serialisation == data

    node_again = MantarayNode()
    node_again.deserialise(serialisation)
    load_all_nodes(load_function, node_again)

    assert node_again == node


@pytest.mark.asyncio
async def test_construct_manifests_of_testpage_folder(get_debug_postage, bee_class):
    data = bee_test_page_manifest_data(get_debug_postage, bee_class)
    node = MantarayNode()
    node.deserialise(data)
    load_function = create_load_function(bee_class)
    load_all_nodes(load_function, node)

    test_dir = PROJECT_DIR / "data" / "testpage"
    index_html_path = test_dir / "index.html"
    image_path = test_dir / "img" / "icon.png"

    index_reference, image_reference = await asyncio.gather(
        upload_file(index_html_path, get_debug_postage, bee_class),
        upload_file(image_path, get_debug_postage, bee_class),
    )
    text_reference = upload_data(
        bytes(bytearray([104, 97, 108, 105])), get_debug_postage, bee_class
    )

    i_node = MantarayNode()

    i_node.add_fork(
        b"index.html",
        hex_to_bytes(index_reference),
        {
            "Content-Type": "text/html; charset=utf-8",
            "Filename": "index.html",
        },
    )
    i_node.add_fork(
        b"img/icon.png.txt",
        hex_to_bytes(text_reference),
        {
            "Content-Type": "",
            "Filename": "icon.png.txt",
        },
    )
    i_node.add_fork(
        b"img/icon.png",
        hex_to_bytes(image_reference),
        {
            "Content-Type": "image/png",
            "Filename": "icon.png",
        },
    )
    i_node.add_fork(
        b"/",
        bytes(32),
        {
            "website-index-document": "index.html",
        },
    )
    console.log(i_node.forks)

    save_function = create_save_function(bee_class, get_debug_postage)
    i_node_ref = i_node.save(save_function)

    assert list(i_node.forks.keys())[::-1] == list(node.forks.keys())

    marshal = i_node.serialise()
    i_node_again = MantarayNode()
    i_node_again.deserialise(marshal)
    load_all_nodes(load_function, i_node_again)

    # Check after serialisation the object is the same
    assert i_node == i_node_again

    # Check Bee manifest is equal to the constructed one
    assert i_node == node


def test_remove_fork_then_upload(
    get_sample_mantaray_node, get_debug_postage, bee_class
):
    sample_node = get_sample_mantaray_node
    node: MantarayNode = sample_node["node"]
    path1 = sample_node["paths"][0]
    path2 = sample_node["paths"][1]

    save_function = create_save_function(bee_class, get_debug_postage)
    # Save the sample node
    ref_original = node.save(save_function)

    check_node1 = node.get_fork_at_path(b"path1/valami/").node
    ref_check_node1 = check_node1.get_content_address()

    # Current forks of the node
    assert list(check_node1.forks.keys()) == [path1[13], path2[13]]

    # Remove the path and save the node
    node.remove_path(path2)

    ref_deleted = node.save(save_function)

    # Root reference should not remain the same
    assert ref_deleted != ref_original

    load_function = create_load_function(bee_class)
    # Load the node from the deleted reference
    #node.load(load_function, ref_deleted)

    # console.log(f"{node=}")

    # 'm' key of prefix table disappeared
    check_node2 = node.get_fork_at_path(b"path1/valami/").node
    assert list(check_node2.forks.keys()) == [path1[13]]

    # Reference should differ because the fork set changed
    ref_check_node2 = check_node2.get_content_address()
    assert ref_check_node2 != ref_check_node1


def test_modify_tree_and_save_load(bee_class, get_debug_postage):
    data = bee_test_page_manifest_data(get_debug_postage, bee_class)
    node = MantarayNode()
    node.deserialise(data)
    load_function = create_load_function(bee_class)
    load_all_nodes(load_function, node)

    # it modifies a node value and then 2 levels above a descendant node
    first_node = node.forks[105].node
    descendant_node = first_node.forks[109].node.forks[46].node
    metadata1: dict = first_node.get_metadata() if first_node.get_metadata() else {}
    first_node.set_metadata(
        {
            **metadata1,
            "additionalParam": "first",
        }
    )
    descendant_node.set_metadata(
        {
            **descendant_node.get_metadata(),
            "additionalParam": "second",
        }
    )

    save_function = create_save_function(bee_class, get_debug_postage)
    reference = node.save(save_function)
    node_again = MantarayNode()
    node_again.load(load_function, reference)
    load_all_nodes(load_function, node_again)
    first_node_again = node_again.forks[105].node
    descendant_node_again = first_node_again.forks[109].node.forks[46].node

    assert first_node_again.get_metadata() == first_node.get_metadata()
    assert first_node_again.get_metadata()["additionalParam"] == "first"
    # fails if the save does not walk the whole tree
    assert descendant_node_again.get_metadata() == descendant_node.get_metadata()
    assert descendant_node_again.get_metadata()["additionalParam"] == "second"

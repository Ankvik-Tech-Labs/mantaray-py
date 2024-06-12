import pytest
from rich.console import Console

from mantaray_py import MantarayNode, check_for_separator, gen_32_bytes, init_manifest_node
from mantaray_py.node import NotFoundError

console = Console()


def test_single_manaray_node_with_a_random_address():
    node = init_manifest_node()
    random_address = gen_32_bytes()
    node.set_entry(random_address)
    serialised = node.serialise()

    new_node = MantarayNode()
    new_node.deserialise(serialised)

    assert random_address == new_node.get_entry()


def test_get_fork_at_path_and_check_for_separator(get_sample_mantaray_node):
    sample_node = get_sample_mantaray_node
    node = sample_node["node"]

    # Test that get_fork_at_path throws an error for a non-existent path
    with pytest.raises(Exception):
        node.get_fork_at_path(b"path/not/exists")

    # Test get_fork_at_path with a path that does not contain a separator in its descendants
    fork1 = node.get_fork_at_path(b"path1/valami/")
    assert not check_for_separator(
        fork1.node
    ), "Expected no separator in the descendants"

    # Test get_fork_at_path with a path that contains a separator in its descendants
    path2 = sample_node["paths"][3]
    fork2 = node.get_fork_at_path(path2)
    assert check_for_separator(fork2.node), "Expected a separator in the descendants"

    # Test get_fork_at_path with a path that does not contain a separator in its descendants and has no forks
    path3 = sample_node["paths"][4]
    fork3 = node.get_fork_at_path(path3)
    assert not check_for_separator(
        fork3.node
    ), "Expected no separator in the descendants and no forks"


def test_fail_serialise_with_no_storage_saves():
    node = init_manifest_node()
    rand_address = gen_32_bytes()
    path = "vmi".encode()
    node.add_fork(path, rand_address)
    with pytest.raises(ValueError):
        node.serialise()


def test_checks_the_expected_structure_of_the_sample_mantaray_node(
    get_sample_mantaray_node,
):
    sample_node = get_sample_mantaray_node
    node = sample_node["node"]
    path1 = sample_node["paths"][0]
    path2 = sample_node["paths"][1]
    path3 = sample_node["paths"][2]
    path4 = sample_node["paths"][3]
    path5 = sample_node["paths"][4]

    # * first level: 'p'
    assert list(node.forks.keys()) == [path1[0]]

    second_level_fork = node.forks[path5[0]]
    assert second_level_fork.prefix == "path".encode()

    second_level_node = second_level_fork.node
    # * second level: '1', '2'
    assert list(second_level_node.forks.keys()) == [path1[4], path5[4]]

    third_level_fork2 = second_level_node.forks[path5[4]]
    assert third_level_fork2.prefix == bytes([path5[4]])

    third_level_fork1 = second_level_node.forks[path1[4]]
    assert third_level_fork1.prefix == b"1/valami"

    third_level_node1 = third_level_fork1.node
    # * third level 1: '/'
    assert list(third_level_node1.forks.keys()) == [path1[12]]

    fourth_level_fork1 = third_level_node1.forks[path1[12]]
    assert fourth_level_fork1.prefix == bytes([path1[12]])

    fourth_level_node1 = fourth_level_fork1.node
    # * fourth level 1: 'e', 'm'
    assert list(fourth_level_node1.forks.keys()) == [path1[13], path2[13]]

    fifth_level_fork2 = fourth_level_node1.forks[path2[13]]
    assert fifth_level_fork2.prefix == b"masodik"

    fifth_level_node2 = fifth_level_fork2.node
    # * fifth level 2: '.'
    assert list(fifth_level_node2.forks.keys()) == [path3[20]]

    sixth_level_node1 = fifth_level_node2.forks[path3[20]]
    assert sixth_level_node1.prefix == b".ext"


def test_remove_forks(get_sample_mantaray_node):
    sample_node = get_sample_mantaray_node
    node = sample_node["node"]
    path1 = sample_node["paths"][0]
    path2 = sample_node["paths"][1]

    #* Non-existing path check
    with pytest.raises(NotFoundError):
        node.remove_path(b"\x00\x01\x02")

    #* Node where the fork set will change
    check_node1 = node.get_fork_at_path(b"path1/valami/").node

    #* Current forks of node
    assert list(check_node1.forks.keys()) == [path1[13], path2[13]]

    node.remove_path(path2)

    #* 'm' key of prefix table disappeared
    assert list(check_node1.forks.keys()) == [path1[13]]

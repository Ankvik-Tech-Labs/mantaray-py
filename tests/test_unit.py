from mantaray_py import MantarayNode, equal_nodes, gen_32_bytes, check_for_separator, init_manifest_node
import pytest


def test_single_manaray_node_with_a_random_address(get_sample_mantaray_node):
    node = init_manifest_node()
    random_address = gen_32_bytes()
    node.set_entry(random_address)

    serialized = node.serialize()
    new_node = MantarayNode()
    new_node.deserialize(serialized)

    assert random_address == new_node.get_entry()


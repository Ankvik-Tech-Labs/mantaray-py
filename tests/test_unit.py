from mantaray_py import MantarayNode, equal_nodes, gen_32_bytes, check_for_separator, init_manifest_node
import pytest
from rich.console import Console

console = Console()

def test_single_manaray_node_with_a_random_address():
    node = init_manifest_node()
    random_address = gen_32_bytes()
    node.set_entry(random_address)
    serialised = node.serialise()
    
    new_node = MantarayNode()
    new_node.deserialise(serialised)

    assert random_address == new_node.get_entry()

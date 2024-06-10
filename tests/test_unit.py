from mantaray_py import MantarayNode, equal_nodes, gen_32_bytes, check_for_separator, init_manifest_node
import pytest
from rich.console import Console

console = Console()

def test_single_manaray_node_with_a_random_address():
    node = init_manifest_node()
    # random_address = gen_32_bytes()
    random_address = bytes([
      229,  5, 247, 157, 211, 167, 196, 164,
       82, 13, 129, 139,  75,  95,  58,  43,
      188, 41,  52,  27,  52, 221, 242, 140,
      150, 81, 189,  90, 184, 120,  19,  31
    ])
    # console.print(random_address)

    node.set_entry(random_address)

    serialized = node.serialize()
    print(list(serialized))
    new_node = MantarayNode()
    new_node.deserialize(serialized)

    assert random_address == new_node.get_entry()


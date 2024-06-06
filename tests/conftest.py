from mantaray_py import MantarayNode, equal_nodes, gen_32_bytes
from pytest import fixture

@fixture
def get_sample_mantaray_node() -> dict[MantarayNode, bytes]:
    node = MantarayNode()
    random_address = gen_32_bytes()
    node.set_entry(random_address)

    paths = [
        'path1/valami/elso',
        'path1/valami/masodik',
        'path1/valami/masodik.ext',
        'path1/valami',
        'path2'
    ]

    for path in paths:
        encoded_path = path.encode()
        node.add_fork(encoded_path, random_address)

    return {
        'node': node,
        'paths': [path.encode() for path in paths],  # Return encoded paths
    }
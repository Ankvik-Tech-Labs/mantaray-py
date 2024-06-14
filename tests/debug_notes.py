BEE_POSTAGE = "b8f5483c9282fe0c8f8614ab537a3ecd8a452e2944fb09b9d8080c6baa04d560"
rand_address = bytearray(b'\xe5\x05\xf7\x9d\xd3\xa7\xc4\xa4R\r\x81\x8bK_:+\xbc)4\x1b4\xdd\xf2\x8c\x96Q\xbdZ\xb8x\x13\x1f')
import pytest
from rich.console import Console

from mantaray_py import (MantarayNode, check_for_separator, gen_32_bytes,
                         init_manifest_node)
from mantaray_py.node import NotFoundError
from pathlib import Path
import asyncio
import pytest
from typing import Callable
from bee_py.bee import Bee
from bee_py.types.type import Data, REFERENCE_HEX_LENGTH
from rich.console import Console

from bee_py.utils.hex import bytes_to_hex, hex_to_bytes

from mantaray_py import Reference, MantarayNode
from rich.traceback import install
install()

bee_class = Bee("https://1633-ethersphere-mantarayjs-32woopg7uie.ws-us114.gitpod.io/")

node = MantarayNode()
node.set_obfuscation_key(bytes(bytearray([103,106,146,247,187,80,45,232,176,88,116,225,58,212,119,244,75,70,204,242,246,4,124,66,127,64,50,134,94,118,52,58])))

node.set_entry(bytes(rand_address))
# list(bytearray(node.serialise()))
node.serialise()
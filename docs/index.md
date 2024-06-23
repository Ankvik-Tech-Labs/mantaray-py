# mantaray py


> Mantaray data structure in Python



| Feature       | Value                     |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Technology    | [![Python](https://img.shields.io/badge/Python-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org/) [![Hatch project](https://img.shields.io/badge/%F0%9F%A5%9A-Hatch-4051b5.svg)](https://github.com/pypa/hatch) [![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-2088FF.svg?style=flat&logo=GitHub-Actions&logoColor=white)](https://github.com/features/actions) [![Pytest](https://img.shields.io/badge/Pytest-0A9EDC.svg?style=flat&logo=Pytest&logoColor=white)](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/tests.yml/badge.svg)                           |
| Type Checking | [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Checked with mypy](http://www.mypy-lang.org/static/mypy_badge.svg)](http://mypy-lang.org/)                                                                                                                                                                                                                                                                                                                                                                                                                                                     |
| CI/CD         | [![Release](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/release.yml/badge.svg)](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/build.yml) [![Tests](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/tests.yml/badge.svg)](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/tests.yml) [![Labeler](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/labeler.yml/badge.svg)](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/labeler.yml) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit) [![codecov](https://codecov.io/gh/Ankvik-Tech-Labs/mantaray-py/graph/badge.svg?token=ISTIW37DO6)](https://codecov.io/gh/Ankvik-Tech-Labs/mantaray-py)                                                                                                                                                                                                           |
| Docs          | [![Docs](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/documentation.yml/badge.svg)](https://github.com/Ankvik-Tech-Labs/mantaray-py/actions/workflows/build.yml)                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |
| Package       | [![PyPI - Version](https://img.shields.io/pypi/v/mantaray-py.svg)](https://pypi.org/project/mantaray-py/) [![PyPI - Python Version](https://img.shields.io/pypi/pyversions/mantaray-py)](https://pypi.org/project/mantaray-py/) [![PyPI - License](https://img.shields.io/pypi/l/mantaray-py)](https://pypi.org/project/mantaray-py/)                                                                                                                                                                                                                                                                                                                                                                                                        |
| Meta          | [![GitHub license](https://img.shields.io/github/license/Ankvik-Tech-Labs/mantaray-py?style=flat&color=1573D5)](https://github.com/Ankvik-Tech-Labs/mantaray-py/blob/main/LICENSE) [![GitHub last commit](https://img.shields.io/github/last-commit/Ankvik-Tech-Labs/mantaray-py?style=flat&color=1573D5)](https://github.com/Ankvik-Tech-Labs/mantaray-py/commits/main) [![GitHub commit activity](https://img.shields.io/github/commit-activity/m/Ankvik-Tech-Labs/mantaray-py?style=flat&color=1573D5)](https://github.com/Ankvik-Tech-Labs/mantaray-py/graphs/commit-activity) [![GitHub top language](https://img.shields.io/github/languages/top/Ankvik-Tech-Labs/mantaray-py?style=flat&color=1573D5)](https://github.com/Ankvik-Tech-Labs/mantaray-py) |



# Description

With this package you can manipulate and interpret mantaray data via `MantarayNode` and `MantarayFork` abstractions.

# Installation

- Install using `pip`
```py
pip install mantaray_py
```

# Usage

### Construct Mantaray

```py
from mantaray_py import MantarayNode, MantarayFork, init_manifest_node, gen_32_bytes

node = init_manifest_node()
address1 = gen_32_bytes()
address2 = gen_32_bytes()
address3 = gen_32_bytes()
address4 = gen_32_bytes()
address5 = gen_32_bytes()
address6 = gen_32_bytes()

path1 = "path1/valami/elso".encode()
path2 = "path1/valami/masodik".encode()
path3 = "path1/valami/masodik.ext".encode()
path4 = "path1/valami".encode()
path5 = "path2".encode()
path6 = "path3/haha".encode()

node.add_fork(path1, address1, { "vmi": "elso" })
node.add_fork(path2, address2)
node.add_fork(path3, address3)
node.add_fork(path4, address4, {"vmi": "negy"})
node.add_fork(path5, address5)
node.add_fork(path6, address6, {"vmi": "haha"})
node.remove_path(path3)

print(node)
```

### Mantaray Storage Operations

```py
from mantaray_py import MantarayNode

node = MantarayNode()
"""
here `reference` parameter is a `Reference` type which can be a 32 or 64 of bytes
and `load_function` is a [load_function: (address: bytes): bytes] typed function
that returns the serialised raw data of a MantarayNode of the given reference. See tests/integration/test_int.py file for reference.
"""
node.load(load_function, reference)

# Manipulate `node` object then save it again
# (...)

# save into the storage with a storage handler [save_function: (data: bytes): Reference]
# See tests/integration/test_int.py file for reference.
reference = node.save(save_function)
```

<!-- These are examples of badges you might want to add to your README:
     please update the URLs accordingly

[![Built Status](https://api.cirrus-ci.com/github/<USER>/maccor-utility.svg?branch=main)](https://cirrus-ci.com/github/<USER>/maccor-utility)
[![ReadTheDocs](https://readthedocs.org/projects/maccor-utility/badge/?version=latest)](https://maccor-utility.readthedocs.io/en/stable/)
[![Coveralls](https://img.shields.io/coveralls/github/<USER>/maccor-utility/main.svg)](https://coveralls.io/r/<USER>/maccor-utility)
[![PyPI-Server](https://img.shields.io/pypi/v/maccor-utility.svg)](https://pypi.org/project/maccor-utility/)
[![Conda-Forge](https://img.shields.io/conda/vn/conda-forge/maccor-utility.svg)](https://anaconda.org/conda-forge/maccor-utility)
[![Monthly Downloads](https://pepy.tech/badge/maccor-utility/month)](https://pepy.tech/project/maccor-utility)
[![Twitter](https://img.shields.io/twitter/url/http/shields.io.svg?style=social&label=Twitter)](https://twitter.com/maccor-utility)
-->

[![Project generated with PyScaffold](https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold)](https://pyscaffold.org/)

# maccor-utility

> Utility tools for processing Maccor battery tester data

This repository contains utility tools for processing Maccor battery tester data.

## Legal notice
"Maccor" is a trademark of Maccor, Inc. This repository and its developers don't claim ownership of the trademark
or intend to infringe copyright or proprietary rights.

The software in this repository is not affiliated with [Maccor, Inc.](http://www.maccor.com/) or any of its subsidiaries.
The software is not endorsed by Maccor, Inc. or any of its subsidiaries. The software is provided as is and
without any warranty.

## Disclaimer
This is a work in progress. The code is not yet fully tested and may contain bugs. Use at your own risk.

## Installation
Most of the functions in this repository are usable without proprietary Maccor software. Solely, the functions to read
Maccor RAW data files directly require the proprietary "MaccorReadDataFileLIB.dll". This DLL is not included in this
repository. You will need to get it by request from [Maccor, Inc.](http://www.maccor.com/TechnicalSupport.aspx) or their
service partner in Europe, [CellCare Technologies Ltd.](https://www.cellcare.com/contact/index.php).

### Easy installation (limited functionality)
```cmd
pip install maccor-utility
```
### Step-by-step instructions (full functionality)
* Clone the repository
* Copy the "MaccorReadDataFileLIB.dll" file to the "src/maccor_dll" directory in your local clone of this repository
  * Depending on your operating system, choose the correct variant, e.g., 32bit or 64bit
  * Rename the file to "MaccorReadDataFileLIB.dll" if necessary
* Open a command prompt in the repository directory
* Activate your python environment which you want to install this package in
* Run `pip install .` to install the package

## Usage
For examples on how to read Maccor data files, see the "examples" directory.

## Contributing
Contributions are welcome and manged with issue tracking and pull requests.

<!-- pyscaffold-notes -->

## Note

This project has been set up using PyScaffold 4.5. For details and usage
information on PyScaffold see https://pyscaffold.org/.

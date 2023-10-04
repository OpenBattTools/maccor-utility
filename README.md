# Maccor-Utility
Utility tools for processing Maccor battery tester data

## Installation
This utility are not usable without proprietary Maccor software. We were supplied with a copy of the 
"MaccorReadDataFileLIB.dll" by Maccor. This file is not included in this repository. You will need to get it from 
them and place it in the "maccor_dll" directory.

This utility tools are not yet packed in to a python package. To use them, you will need to clone this repository and 
install the dependencies (see import statements) and will need to put the contents of this repository in a directory 
in the sys.path variable.

## Known Issues
* (Fixed) Occasionally, especially when reading large files, the Maccor DLL will throw an exception. This is not 
  handled yet. Since the DLL is proprietary, we cannot fix this issue. The workaround is to re-run the script. Some files are not 
  readable at all. We have not yet determined the cause of this issue. Any hints on how to fix this are welcome. 
  Feel free to open an issue or pull request.
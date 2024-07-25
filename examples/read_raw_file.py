from pathlib import Path

from maccor_utility.read import MaccorDataRawFile

# To read a raw file, use the following code
# The test file is not included in this repository, use your own file
cwd = Path(__file__)
path2file = cwd.parents[1] / "test_data" / "231004_test_data_raw.024"
file = MaccorDataRawFile(path2file)
file.read()
data = file.data

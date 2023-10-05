from pathlib import Path

from maccor_utility.read import read_maccor_data

# Path to the test data
cwd = Path(__file__)
test_data_path = cwd.parents[1] / "test_data"

file_name_com = "231004_test_data"
raw_path = test_data_path / (file_name_com + "_raw.024")
mims_client1_path = test_data_path / (file_name_com + "_mims_client1.024.txt")
mims_client2_path = test_data_path / (file_name_com + "_mims_client2.024.txt")
export1_path = test_data_path / (file_name_com + "_export1.024.txt")
export2_path = test_data_path / (file_name_com + "_export2.024.txt")
mims_server2_path = test_data_path / (file_name_com + "_mims_server2.024.txt")

results = dict()

options = {
    "raw": raw_path,
    "Maccor Export 1": export1_path,
    "Maccor Export 2": export2_path,
    "MIMS Server 2": mims_server2_path,
    "MIMS Client 1": mims_client1_path,
    "MIMS Client 2": mims_client2_path,
}

for key, value in options.items():
    results[key] = read_maccor_data(value, key)

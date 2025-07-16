from pathlib import Path

from maccor_utility.read import MaccorDataFormat, read_maccor_data_file

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
# key: (file_path, format)
options = {
    "raw": (raw_path, MaccorDataFormat.raw),
    "Maccor Export 1": (export1_path, MaccorDataFormat.maccor_export1),
    "Maccor Export 2": (export2_path, MaccorDataFormat.maccor_export2),
    "MIMS Client 1": (mims_client1_path, MaccorDataFormat.mims_client1),
    "MIMS Client 2": (mims_client2_path, MaccorDataFormat.mims_client2),
    "MIMS Server 2": (mims_server2_path, MaccorDataFormat.mims_server2),
}

for key, value in options.items():
    results[key] = read_maccor_data_file(file_path=value[0], frmt=value[1])

    for str_format, format_tuple in options.items():
        format = format_tuple[1]
        results[key].data.change_column_names(format)


# todo: besides raw, no other result contains meta data, description or units

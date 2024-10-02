from maccor_utility.read import MaccorDataFormat


def test_maccor_data_format():
    for ele in [
        "raw",
        "Maccor Export 1",
        "Maccor Export 2",
        "MIMS Client 1",
        "MIMS Client 2",
        "MIMS Server 2",
    ]:
        assert ele in MaccorDataFormat.__members__.values()

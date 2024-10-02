import maccor_utility.helperfunctions as hf


def test_inverse_dict_one_to_x():
    input_dict = {"a": ["1", "2", "3"], "b": ["4", "5", "6"], "c": ["7", "8", "9"]}
    expected_output = {
        "1": "a",
        "2": "a",
        "3": "a",
        "4": "b",
        "5": "b",
        "6": "b",
        "7": "c",
        "8": "c",
        "9": "c",
    }
    assert hf.inverse_dict_one_to_x(input_dict) == expected_output

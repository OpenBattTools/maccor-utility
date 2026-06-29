import math
from pathlib import Path

import pandas as pd
import pytest

from maccor_utility.helper_functions import parse_duration_to_seconds
from maccor_utility.read import (
    MaccorDataFormat,
    read_maccor_data_file,
    rename_columns,
)

DATA_DIR = Path(__file__).parent / "data"


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


def test_parse_duration_to_seconds():
    # duration strings (with and without days / fractional, decimal comma)
    assert parse_duration_to_seconds("  0d 00:00:01,00") == 1.0
    assert parse_duration_to_seconds("0d 00:00:1") == 1.0
    assert parse_duration_to_seconds("1d 02:03:04") == 86400 + 2 * 3600 + 3 * 60 + 4
    assert parse_duration_to_seconds("00:01:30,5") == 90.5
    # numeric inputs pass through unchanged
    assert parse_duration_to_seconds(12.5) == 12.5
    assert parse_duration_to_seconds("15.0") == 15.0
    # unparseable values yield NaN
    assert math.isnan(parse_duration_to_seconds("not a duration"))


@pytest.mark.parametrize(
    "filename, export_format",
    [
        ("sample_maccor_export1_trimmed.txt", MaccorDataFormat.maccor_export1),
        ("sample_mims_client2_trimmed.txt", MaccorDataFormat.mims_client2),
    ],
)
def test_duration_time_columns_parsed_to_seconds(filename, export_format):
    # These text formats export TestTime/StepTime as duration strings. After
    # reading, the canonical TestTime column must be numeric seconds and
    # monotonically non-decreasing across the (trimmed) cycles in the sample.
    result = read_maccor_data_file(str(DATA_DIR / filename), export_format)
    df = rename_columns(
        result.data.as_dataframe.copy(),
        input_format=export_format,
        target_format=MaccorDataFormat.raw,
    )
    test_time = df["TestTime"]
    assert pd.api.types.is_numeric_dtype(test_time)
    assert not test_time.isna().any()
    assert test_time.diff().dropna().ge(0).all()

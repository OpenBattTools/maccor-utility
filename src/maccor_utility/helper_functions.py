# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 11:45 2021
Last modified: see git version control

@author: LukasGold | lukas.gold@isc.fraunhofer.de

Description:
A collection of functions to be used repeatedly throughout the scripts in this project.
"""

# Importing required modules
import re
from pathlib import Path

from batt_utility.helper_functions import read_specific_line_from_file
from typing_extensions import Union

# Maccor duration strings look like "Nd HH:MM:SS[,ff]" (days, hours, minutes,
# seconds; the seconds may carry a decimal comma or point).
_DURATION_PATTERN = re.compile(r"^\s*(?:(\d+)d\s+)?(\d+):(\d+):(\d+(?:[.,]\d+)?)\s*$")


# Definitions of the functions
def get_column_names_mims_client1(file_path: Union[str, Path], header_num: int):
    columns = read_specific_line_from_file(file_path, header_num).split("\t")
    first_row_with_data = read_specific_line_from_file(file_path, header_num + 2)
    number_of_data_columns = len(first_row_with_data.split("\t"))
    cntr = 0
    while number_of_data_columns > len(columns):
        columns.append(f"dummy_col{cntr}")
        cntr += 1
    while number_of_data_columns < len(columns):
        columns = columns[: len(columns) - 1]
    return columns


def parse_duration_to_seconds(value):
    """Convert a Maccor duration string to a number of seconds.

    Some Maccor text exports (e.g. "Maccor Export 1", "MIMS Client 2") report the
    test and step time as a duration string of the form ``"Nd HH:MM:SS[,ff]"``
    instead of a numeric number of seconds. This converts such a string to a
    float number of seconds.

    Numeric inputs are returned unchanged. Values that are neither numeric nor a
    recognised duration string yield ``float("nan")``.
    """
    if value is None or isinstance(value, (int, float)):
        return value
    text = str(value).strip()
    match = _DURATION_PATTERN.match(text)
    if match is None:
        try:
            return float(text.replace(",", "."))
        except ValueError:
            return float("nan")
    days, hours, minutes, seconds = match.groups()
    return (
        (int(days) if days else 0) * 86400
        + int(hours) * 3600
        + int(minutes) * 60
        + float(seconds.replace(",", "."))
    )


# Line before the last line of the file

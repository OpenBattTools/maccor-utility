# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 11:45 2021
Last modified: see git version control

@author: LukasGold | lukas.gold@isc.fraunhofer.de

Description:
A collection of functions to be used repeatedly throughout the scripts in this project.
"""

# Importing required modules
from pathlib import Path

from batt_utility.helper_functions import read_specific_line_from_file
from typing_extensions import Union


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


# Line before the last line of the file

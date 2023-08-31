# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 11:45 2021
Last modified: see git version control

@author: lukas.gold

Description:
A collection of functions to be used repeatedly throughout the scripts in this project.
"""


# Importing required modules
import os
import datetime
import pathlib
import numpy as np
import scipy as sp
from scipy import interpolate
from typing import List, Union


# Definitions of the functions
def print_ts(msg: str):
    """A mock-up of the print function, prepending a time stamp with date

    Parameters
    ----------
    msg:
        Message to be printed

    Returns
    -------

    """
    # prepends timestamp in the form of '[20.05.2021 11:41:28] '
    print(datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S] ') + msg)


def read_specific_line_from_file(
        file_path: Union[pathlib.Path, str],
        line_idx: int
) -> str:
    file = open(file_path)
    all_lines = file.readlines()
    file.close()
    return all_lines[line_idx]


def search_all_files(directory: pathlib.Path) -> List[pathlib.Path]:
    """Creates a list of file paths (pathlib.path objects) in the specified directory
    and its subdirectories using the pathlib module. If you want to get filterable
    strings you need to call each element of the returned list and use a method like
    as_uri() or call the attribute you are interested in, e.g. name or parts.

    Parameters
    ----------
    directory:
        Specifies the to crawl through directory

    Returns
    -------
    file_list:
        List of pathlib.path objects

    """
    dir_path = pathlib.Path(directory)
    assert (dir_path.is_dir())
    file_list = []
    for x in dir_path.iterdir():
        if x.is_file():
            file_list.append(x)
        elif x.is_dir():
            file_list.extend(search_all_files(x))
    return file_list


def filter_file_list(
        file_list: List[pathlib.Path],
        string: str,
        extension: bool = False
) -> List[pathlib.Path]:
    """Filters a list of files, as returned by search_all_files(), according to a string
     within the name of the file or the file extensions.

    Parameters
    ----------
    file_list:
        List of pathlib.path objects
    string:
        String or file extension (without the '.') to filter
    extension:
        Whether to look for the string in the file name or the file extension

    Returns
    -------
    filtered_file_list
    """
    filtered_file_list = []
    for file in file_list:
        if extension:
            if ('.'+string) == file.suffix:
                filtered_file_list.append(file)
        else:
            if string in file.stem:
                filtered_file_list.append(file)
    # Return filtered file list
    return filtered_file_list


def get_list_of_files(directory: Union[pathlib.Path, str]) -> List[str]:
    """Creates a list of file paths (strings) in the specified directory and its
    subdirectories using the os module.

    Parameters
    ----------
    directory

    Returns
    -------
    file_paths: list

    """
    # Initializing empty file paths list
    file_paths = []

    # Crawling through directory and subdirectories
    for root, directories, files in os.walk(directory):
        for filename in files:
            # join the two strings in order to form the full file path.
            file_path = os.path.join(root, filename)
            file_paths.append(file_path)

    # Return all the paths
    return file_paths


# Line before the last line of the file

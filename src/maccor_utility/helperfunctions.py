# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 11:45 2021
Last modified: see git version control

@author: LukasGold | lukas.gold@isc.fraunhofer.de

Description:
A collection of functions to be used repeatedly throughout the scripts in this project.
"""

# Importing required modules
import datetime
import pathlib


# Definitions of the functions
def print_(msg: str, ts: bool = False, dg: bool = True):
    """A mock-up of the print function, optionally prepending a time stamp with date,
    and allowing to suppress the printing.

    Parameters
    ----------
    msg:
        Message to be printed
    ts:
        Whether to prepend a time stamp to the print message
    dg:
        Whether to print the message. dg = True prints the message.

    Returns
    -------

    """
    if dg:
        if ts:
            print(datetime.datetime.now().strftime("[%d.%m.%Y %H:%M:%S] ") + msg)
        else:
            print(msg)


def print_ts(msg: str):
    """A mock-up of the print function, prepending a time stamp with date.

    Parameters
    ----------
    msg:
        Message to be printed

    Returns
    -------

    """
    # prepends timestamp in the form of '[20.05.2021 11:41:28] '
    print_(msg=msg, ts=True, dg=True)


def read_specific_line_from_file(file_path, line_idx):
    file = open(file_path)
    all_lines = file.readlines()
    file.close()
    return all_lines[line_idx]


def search_all_files(directory):
    """Creates a list of file paths (pathlib.path objects) in the specified directory
    and its subdirectories using the pathlib module. If you want to get filterable
    strings you need to call each element of the returned list and use a method like
    as_uri() or call the attribute you are interested in, e.g. name or parts.

    Parameters
    ----------
    directory: pathlib.Path or str
        Specifies the to crawl through directory

    Returns
    -------
    file_list: list
        List of pathlib.path objects

    """
    dir_path = pathlib.Path(directory)
    assert dir_path.is_dir()
    file_list = []
    for x in dir_path.iterdir():
        if x.is_file():
            file_list.append(x)
        elif x.is_dir():
            file_list.extend(search_all_files(x))
    return file_list


def filter_file_list(file_list, string, extension=False):
    """Filters a list of files, as returned by search_all_files(), according to a string
     within the name of the file or the file extensions.

    Parameters
    ----------
    file_list:
        List of pathlib.Path objects
    string: str
        String or file extension (without the '.') to filter
    extension: bool
        Whether to look for the string in the file name or the file extension

    Returns
    -------
    filtered_file_list
    """
    filtered_file_list = []
    for file in file_list:
        if extension:
            if ("." + string) == file.suffix:
                filtered_file_list.append(file)
        else:
            if string in file.stem:
                filtered_file_list.append(file)
    # Return filtered file list
    return filtered_file_list


# Line before the last line of the file

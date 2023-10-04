# -*- coding: utf-8 -*-
"""
Created on Thu Nov 18 11:45 2021
Last modified: see git version control

@author: lukas.gold

Description:
A collection of functions to be used repeatedly throughout the scripts in this project.
"""


# List of ToDos:
# todo: create uniform structure


# Importing required modules
import os
import datetime
import pathlib
import numpy as np
from scipy import interpolate


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
            print(datetime.datetime.now().strftime('[%d.%m.%Y %H:%M:%S] ') + msg)
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


def slice_list(list_in, start, end):
    """Slices a list or numpy.array without returning an KeyError if the slicing indices exceed the available
    length of the list. When the end slicing index exceeds the length, the list is sliced until the last entry.
    When the start slicing index exceeds the length, the last list entry is returned.

    Parameters
    ----------
    list_in
    start
    end

    Returns
    -------
    list

    """
    length = len(list_in)
    if type(end) != int:
        return ValueError('The parameters start and end need to be integers!')
    if end >= length:
        end_out = length
    else:
        end_out = end
    if start >= length:
        if type(list_in) == list:
            return [list_in[-1]]
        elif type(list_in) == np.ndarray:
            return np.array([list_in[-1]])
    else:
        start_out = start
        return list_in[start_out:end_out]


def search_all_files(directory):
    """Creates a list of file paths (pathlib.path objects) in the specified directory and its subdirectories using the
    pathlib module. If you want to get filterable strings you need to call each element of the returned list and use
    a method like as_uri() or call the attribute you are interested in, e.g. name or parts.

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
    assert (dir_path.is_dir())
    file_list = []
    for x in dir_path.iterdir():
        if x.is_file():
            file_list.append(x)
        elif x.is_dir():
            file_list.extend(search_all_files(x))
    return file_list


def filter_file_list(file_list, string, extension=False):
    """Filters a list of files, as returned by search_all_files(), according to a string within the name of the file or
    the file extensions.

    Parameters
    ----------
    file_list: list
        List of pathlib.path objects
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
            if ('.'+string) == file.suffix:
                filtered_file_list.append(file)
        else:
            if string in file.stem:
                filtered_file_list.append(file)
    # Return filtered file list
    return filtered_file_list


def get_list_of_files(directory):
    """Creates a list of file paths (strings) in the specified directory and its subdirectories using the os module

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


def filter_list_of_files(file_paths, selected_extension):
    """Filters the input list of files (strings, as returned by get_list_of_files()) according to the selected extension

    Parameters
    ----------
    file_paths: list
        List of file paths
    selected_extension: str
        Selexted file extension

    Returns
    -------
    filtered_file_paths: list
        List of filtered file paths (with the desired extension)

    """
    # Process input parameters
    if len(selected_extension.split('.')) > 1:
        selected_extension = selected_extension.split('.')[-1]
    # Filters a given list of files according to their file extension
    filtered_file_paths = list()
    # Iterate of all entries
    for entry in file_paths:
        fractions = entry.split('.')
        if len(fractions) > 1:
            extension = fractions[-1]
            if extension == selected_extension:
                filtered_file_paths.append(entry)

    return filtered_file_paths


def filter_xy_by_min_dx(x_in, y_in, dx_min):
    """

    Parameters
    ----------
    x_in: list-like
        x-axis values
    y_in: list-like
        y-axis values
    dx_min: float
        Minimum difference between adjacent values to be included in the filtered result

    Returns
    -------
    x_out: numpy.array
        Filtered x-axis values
    y_out: numpy.array
        Filtered y-axis values
    """
    if len(x_in) > 0:
        x_filtered = [x_in[0]]
    else:
        x_filtered = []
    if len(y_in) > 0:
        y_filtered = [y_in[0]]
    else:
        y_filtered = []
    for index in np.arange(1, len(x_in)):
        if x_in[index] - x_filtered[-1] >= dx_min:
            x_filtered.append(x_in[index])
            y_filtered.append(y_in[index])
    x_out = np.array(x_filtered)
    y_out = np.array(y_filtered)
    return x_out, y_out


def filter_xy_by_min_dy(x_in, y_in, dy_min):
    """

    Parameters
    ----------
    x_in: list-like
        x-axis values
    y_in: list-like
        y-axis values
    dy_min: float
        Minimum difference between adjacent values to be included in the filtered result

    Returns
    -------
    x_out: numpy.array
        Filtered x-axis values
    y_out: numpy.array
        Filtered y-axis values
    """

    if len(x_in) > 0:
        x_filtered = [x_in[0]]
    else:
        x_filtered = []
    if len(y_in) > 0:
        y_filtered = [y_in[0]]
    else:
        y_filtered = []
    for index in np.arange(1, len(x_in)):
        if y_in[index] - y_filtered[-1] >= dy_min:
            x_filtered.append(x_in[index])
            y_filtered.append(y_in[index])
    x_out = np.array(x_filtered)
    y_out = np.array(y_filtered)
    return x_out, y_out


def filter_xy_x_monotonously_increasing(x_in, y_in):
    """

    Parameters
    ----------
    x_in: list or numpy.array
        x-axis values
    y_in: list-like
        y-axis values

    Returns
    -------
    x_out: numpy.array
        Filtered x-axis values
    y_out: numpy.array
        Filtered y-axis values
    """
    if len(x_in) > 0:
        x_filtered = [x_in[0]]
    else:
        x_filtered = []
    if len(y_in) > 0:
        y_filtered = [y_in[0]]
    else:
        y_filtered = []
    for index in np.arange(1, len(x_in)):
        if x_in[index] >= x_filtered[-1]:
            x_filtered.append(x_in[index])
            y_filtered.append(y_in[index])
    x_out = np.array(x_filtered)
    y_out = np.array(y_filtered)
    return x_out, y_out


def filter_xy_x_monotonously_falling(x_in, y_in):
    """

    Parameters
    ----------
    x_in: list-like
        x-axis values
    y_in: list-like
        y-axis values

    Returns
    -------
    x_out: numpy.array
        Filtered x-axis values
    y_out: numpy.array
        Filtered y-axis values
    """
    if len(x_in) > 0:
        x_filtered = [x_in[0]]
    else:
        x_filtered = []
    if len(y_in) > 0:
        y_filtered = [y_in[0]]
    else:
        y_filtered = []
    for index in np.arange(1, len(x_in)):
        if x_in[index] <= x_filtered[-1]:
            x_filtered.append(x_in[index])
            y_filtered.append(y_in[index])
    x_out = np.array(x_filtered)
    y_out = np.array(y_filtered)
    return x_out, y_out


def interpolate_to_fixed_dx(x_in, y_in, dx):
    """

    Parameters
    ----------
    x_in: list-like
        x-axis values
    y_in: list-like
        y-axis values
    dx: float
        Spacing between points of the x-axis

    Returns
    -------
    x_out: numpy.array
        Equally spaced x-axis values
    y_out: numpy.array
        Interpolated y-axis values
    """
    increasing = False
    flipped = False
    monotonous = False
    # Check if increasing or decreasing
    avg_diff = np.mean(np.diff(x_in))
    if avg_diff > 0:
        increasing = True
    elif avg_diff < 0:
        increasing = False
        x_in = np.flip(x_in)
        y_in = np.flip(y_in)
        flipped = True
    # Check if x is monotonically in creasing
    if not np.all(np.diff(x_in) > 0):
        monotonous = True
    else:
        monotonous = False
        x_in, y_in = filter_xy_x_monotonously_increasing(x_in, y_in)
    interpolated = interpolate.interp1d(x=x_in, y=y_in)
    x_out = np.arange(np.min(x_in), np.max(x_in), dx)
    y_out = interpolated(x_out)
    if flipped:
        x_out = np.flip(x_out)
        y_out = np.flip(y_out)
    return x_out, y_out

# Line before the last line of the file

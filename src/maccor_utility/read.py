#!/usr/bin/env python
# -*- coding: utf-8 -*-

__docformat__ = "NumPy"
__author__ = "Lukas Gold, Simon Stier"

__doc__ = """
Created on Tue Mar 29 12:28:17 2022
Last modified: see git version control

@author: LukasGold | lukas.gold@isc.fraunhofer.de
@author: SimonStier | simon.stier@isc.fraunhofer.de
"""

# import modules
import copy
import ctypes
import datetime
import gc

# modules as in readmacfile.py
import os  # Required
import subprocess
import sys
import time  # Required!
from enum import Enum

# Python version dependent import statement:
try:
    from enum import StrEnum
except ImportError:
    from strenum import StrEnum

# from ctypes import *
from pathlib import Path
from typing import Any
from warnings import warn

import pandas as pd
from pydantic import field_validator
from typing_extensions import Callable, Dict, List, Literal, Optional, Self, Union

# Platform dependent import statement
try:
    import pythoncom  # Require COM
except ImportError:
    warn(
        "COM not available. Most like you are running on a non-Windows operating "
        "system. Else make sure to hav pywin32 installed. If you read this "
        "message, you will most likely not be able to use the DLL and read Maccor "
        "raw files directly."
    )

# Own modules
from batt_utility.data_models import (
    DecimalSeparator,
    Encoding,
    ReadFileParameter,
    ReadTableResult,
    TabularData,
    ThousandsSeparator,
)
from batt_utility.helper_functions import (
    apply_regex_return_match_groups,
    flatten_dict_one_to_x,
    inverse_dict_one_to_x,
    print_,
    read_first_x_lines,
)

from maccor_utility.helper_functions import get_column_names_mims_client1
from maccor_utility.lookup import (
    MACCOR_COLUMN_UNITS,
    MACCOR_HEADER_UNITS,
    TO_EXPORT1,
    TO_EXPORT2,
    TO_MIMS_CLIENT1,
    TO_MIMS_CLIENT2,
    TO_MIMS_SERVER2,
    TO_RAW,
    TDLLFRARecord,
    TDLLHeaderData,
    TDLLReading,
    TDLLScopeTrace,
    TDLLTimeData,
    TScopeTraceVI,
)

# Do something to make packages required by the DLL used (to avoid linting error)
_ = type(os)
try:
    _ = type(pythoncom)
except NameError:
    warn("Pythoncom not available.")
_ = type(time)
_ = type(TDLLFRARecord)
_ = type(TScopeTraceVI)
_ = type(TDLLReading)


class MaccorDataFormat(StrEnum):
    raw = "raw"
    maccor_export1 = "Maccor Export 1"
    maccor_export2 = "Maccor Export 2"
    mims_client1 = "MIMS Client 1"
    mims_client2 = "MIMS Client 2"
    mims_server2 = "MIMS Server 2"


# Classes
class MaccorTabularData(TabularData):
    data_format: MaccorDataFormat

    def change_column_names(self, target_format: MaccorDataFormat):
        self.as_dataframe = rename_columns(
            self.as_dataframe,
            input_format=self.data_format,
            target_format=target_format,
        )
        self.as_list = self.as_dataframe.to_dict(orient="records")
        self.data_format = target_format


class ReadMaccorTextFileParameter(ReadFileParameter):
    skiprows: int = None
    index_col: Union[Any, Literal[False], None] = None  # IndexLabel,
    usecols: Any = None  # UsecolsArgType
    column_names: Union[List[str], Callable] = None
    skip_blank_lines: bool = None
    exclude_from_params: List[str] = ["column_names"]

    def __init__(self, **data):
        super().__init__(**data)
        for key in ["column_names"]:
            if key not in self.exclude_from_params:
                self.exclude_from_params.append(key)


class HeaderRegExs(StrEnum):
    maccor_export1 = r"([^\t\n\d\:]+)\:*\t([^\t\n]+)[\n]{1}"
    maccor_export2 = r"([^\t\d\:]+)[\s\:]+\t([^\t\n]+)[\n]{1}"
    mims_client1 = r"([^\t\n\d\:]+)\:*\t([^\t\n]+)[\n]{1}"
    mims_client2 = r"([^\t\n\:]+)[\:]{1}\t([^\t\n]+)[\t\n]{1}"
    mims_server2 = r"([^\t\n\d\:]+)\:\t([^\t\n]+)[\n\t]{1}"


class Configurations(Enum):
    maccor_export1 = ReadMaccorTextFileParameter(
        decimal=DecimalSeparator.comma,
        thousands=ThousandsSeparator.point,
        encoding=Encoding.utf8,
        header=2,
        index_col=False,
    )
    maccor_export2 = ReadMaccorTextFileParameter(
        decimal=DecimalSeparator.comma,
        thousands=ThousandsSeparator.point,
        encoding=Encoding.utf8,
        header=2,
        index_col=False,
    )
    mims_client1 = ReadMaccorTextFileParameter(
        decimal=DecimalSeparator.point,
        thousands=ThousandsSeparator.none,
        encoding=Encoding.utf8,
        header=13,
        column_names=get_column_names_mims_client1,
        skiprows=13 + 1,  # header + 1
        skip_blank_lines=False,
    )
    mims_client2 = ReadMaccorTextFileParameter(
        decimal=DecimalSeparator.comma,
        thousands=ThousandsSeparator.point,
        encoding=Encoding.cp1252,
        header=3,
    )
    mims_server2 = ReadMaccorTextFileParameter(
        decimal=DecimalSeparator.point,
        thousands=ThousandsSeparator.comma,
        encoding=Encoding.utf8,
        header=1,
        index_col=False,
    )


class MaccorDataRawFile(object):
    """Adapted from class definition in readmacfile.py"""

    # todo: read procedure and save to meta
    def __init__(
        self, file_path: Union[str, Path], dll_path: Optional[Union[str, Path]] = None
    ):
        super(MaccorDataRawFile, self).__init__()
        if dll_path is None:
            warn("No DLL path provided. Trying to use default path.")
            # Determine whether the operating system is 32bit or 64 bit
            dll_root = Path(__file__).parent / "maccor_dll"
            dll_path = dll_root / "MacReadDataFileLIB 32 bit" / "MacReadDataFileLIB.dll"
            if sys.maxsize > 2**32:
                dll_path = (
                    dll_root / "MacReadDataFileLIB 64 bit" / "MacReadDataFileLIB.dll"
                )
        if not isinstance(dll_path, Path):
            dll_path = Path(dll_path)
        if not dll_path.exists():
            raise FileNotFoundError(f"DLL '{dll_path}' does not exist!")
        self.dll_path = str(dll_path)
        if not isinstance(file_path, Path):
            file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Data file '{file_path}' does not exist!")
        self.file_name = str(file_path)
        self.meta: Optional[dict] = None
        self.data: Optional[MaccorTabularData] = None
        print(f"Reading target file: {self.file_name}")

    def read(self, debug: bool = False) -> Self:
        # stdcall
        dll = ctypes.windll.LoadLibrary(self.dll_path)
        meta = {
            "Units": {**MACCOR_HEADER_UNITS, **MACCOR_COLUMN_UNITS},
        }
        data = []
        try:
            pfile_name = ctypes.c_wchar_p(self.file_name)  # OpenDataFile
            pfile_name_ascii = ctypes.c_char_p(self.file_name.encode("utf-8"))
            _ = pfile_name
            _ = pfile_name_ascii
            # OpenDataFileASCII
            s_array = (ctypes.c_wchar * 256)()

            file = dll.OpenDataFile(self.file_name)

            if file >= 0:
                print_(f"File access successful! handle = {file}", dg=debug)
                print_("Header data", dg=debug)
                # Use the handle to get the header data (Not required)
                dll_header_data = TDLLHeaderData()
                dll.GetDataFileHeader(file, ctypes.pointer(dll_header_data))
                meta["Header data"] = {
                    field_str: getattr(dll_header_data, field_str)
                    for field_str in dll_header_data.field_strings_
                }
                # todo: StartDateTime is useless in the float format
                meta["Parameter"] = {
                    "Start date time": datetime_fromdelphi(
                        getattr(dll_header_data, "StartDateTime")
                    ),
                    "File type": getattr(dll_header_data, "FileType"),
                    "Test channel": getattr(dll_header_data, "TestChan"),
                    "Mass / g": getattr(dll_header_data, "Mass"),
                    "Volume": getattr(dll_header_data, "Volume"),
                    "C-Rate / A": getattr(dll_header_data, "C_Rate"),
                    "Aux units": {},
                    "SMB units": {},
                    "Number of Aux": getattr(dll_header_data, "AUXtot"),
                    "Number of SMB": getattr(dll_header_data, "SMBtot"),
                }
                # "Key": (func, arg)
                test_params_mapping = {
                    "System ID": (dll.GetSystemID, dll_header_data.SystemIDLen),
                    "Test procedure": (dll.GetProcName, dll_header_data.ProcNameLen),
                    "Test name": (dll.GetTestName, dll_header_data.TestNameLen),
                    "Test info": (dll.GetTestInfo, dll_header_data.TestInfoLen),
                    "Procedure description": (
                        dll.GetProcDesc,
                        dll_header_data.ProcDescLen,
                    ),
                }
                for key, (func, arg) in test_params_mapping.items():
                    func(file, ctypes.pointer(s_array), arg)
                    meta[key] = copy.deepcopy(s_array)
                    print_(f"{key} is: {s_array.value}", dg=debug)
                # Key: (func, arg)
                aux_smb_units_mapping = {
                    "Aux units": (dll.GetAuxUnits, meta["Parameter"]["Number of Aux"]),
                    "SMB units": (dll.GetSMBUnits, meta["Parameter"]["Number of SMB"]),
                }
                for key, (func, arg) in aux_smb_units_mapping.items():
                    units = {}
                    for num in range(0, arg):
                        func(file, num, ctypes.pointer(s_array))
                        print_(f"{key} {num + 1} unit is: {s_array.value}", dg=debug)
                        units[f"{key} {num + 1}"] = copy.deepcopy(s_array.value)
                    meta["Parameter"][key] = units

                # Read time series data
                # The number of variables depends on the file type
                if meta["Parameter"]["File type"] == 4:
                    var_cnt = 50
                elif meta["Parameter"]["File type"] == (1 or 2):
                    var_cnt = 15
                else:
                    var_cnt = 0
                count = 0
                dll_time_data = TDLLTimeData()
                dll_scope_trace = TDLLScopeTrace()
                _ = dll_scope_trace
                # Read the file by calling LoadAndGetNextTimeData until <> 0
                exceptions = []
                while (
                    dll.LoadAndGetNextTimeData(file, ctypes.pointer(dll_time_data)) == 0
                ):
                    try:
                        row = {"Index": count}
                        try:  # Try separately for CAN Data, to avoid complete fail
                            # For each loaded data point more details of this data point
                            # can be accessed
                            # CAN Data
                            can_val = ctypes.c_float()
                            can_str = ""
                            for can_num in range(0, 2):
                                dll.GetCANData(file, can_num, ctypes.pointer(can_val))
                                can_str += (
                                    "\nThermistor "
                                    + str(can_num)
                                    + ": "
                                    + "%.3f" % can_val.value
                                )
                            can0 = ""
                            for can_num in range(0, 1):
                                dll.GetCANData(file, can_num, ctypes.pointer(can_val))
                                can0 = "%.4f" % can_val.value
                            can1 = ""
                            for can_num in range(1, 2):
                                dll.GetCANData(file, can_num, ctypes.pointer(can_val))
                                can1 = "%.4f" % can_val.value
                            # Data
                            row.update({"CanStr": can_str, "CAN0": can0, "CAN1": can1})
                        except Exception as e:
                            exceptions.append(e)
                            # todo: trace back why: "function 'GetCANData' not found"
                        # Continue to read the other than CAN data
                        for field_str in dll_time_data.field_strings_:
                            row[field_str] = getattr(dll_time_data, field_str)
                        # Aux data
                        if meta["Parameter"]["Number of Aux"] > 0:
                            for aux_num in range(0, meta["Parameter"]["Number of Aux"]):
                                aux_obj = ctypes.c_float(1.0)
                                dll.GetAuxData(file, aux_num, ctypes.byref(aux_obj))
                                row[f"Aux{aux_num + 1}"] = copy.deepcopy(aux_obj.value)
                        # Variables
                        if (
                            meta["Parameter"]["Number of SMB"] > 0
                            and dll_time_data.HasVarData
                        ):
                            for var_num in range(1, var_cnt + 1):
                                var_obj = ctypes.c_float(1.0)
                                dll.GetVARData(file, var_num, ctypes.byref(var_obj))
                                row[f"Var{var_num}"] = copy.deepcopy(var_obj.value)
                        # todo:
                        #  * global flags
                        #  * SMB data
                        #  * FRA data
                        #  * EV data
                        #  * scope data
                        data.append(row)
                        print_(f"Row {count}: {row}", dg=debug)
                        count += 1

                    # While try-except
                    except Exception as e:
                        exceptions.append(e)

                if len(exceptions) > 0:
                    exceptions = [str(exception) for exception in exceptions]
                    unique_exceptions = set(exceptions)
                    print(
                        f"Number of exceptions with a unique string:"
                        f" {len(unique_exceptions)}"
                    )
                    for exception in unique_exceptions:
                        print(
                            f"Exception occurred {exceptions.count(exception)}x times: "
                            f"{exception}"
                        )
                # Finally close file
                dll.CloseDataFile(file)
                # Unload dll
                del dll
                # Collect garbage!
                gc.collect()
            else:
                print("Error getting file handle")
        # func try-except
        except Exception as e:
            # print(f"Exception: {e}")
            raise e
        finally:
            # Unload dll
            if "dll" in locals():
                del dll
            # Collect garbage!
            gc.collect()

        # todo: make sure that no empty cols are included (if hasglobalflags is 0 in
        #  all records, then the global flags columns should not be present)
        #  same for Var, SMB, FRA, EV, Scope

        self.data = MaccorTabularData(as_list=data, data_format=MaccorDataFormat.raw)
        self.meta = meta
        return self


class MaccorDataTxtFile(ReadTableResult):
    file_path: Union[str, Path]
    export_format: MaccorDataFormat
    meta: Optional[dict] = None
    data: Optional[MaccorTabularData] = None

    def read(self, remove_nan_cols: bool = True) -> Self:
        config = Configurations[self.export_format.name].value
        params = {
            key: (getattr(value, "value", value))
            for key, value in config.model_dump().items()
            if value is not None
        }
        # In case of MIMS Client 1 export:
        if callable(config.column_names):
            params["names"] = config.column_names(self.file_path, config.header)
        else:
            params["names"] = config.column_names
        for key in config.exclude_from_params:
            if key in params:
                del params[key]
        df = pd.read_table(filepath_or_buffer=self.file_path, **params)
        if remove_nan_cols:
            df.dropna(axis="columns", how="all", inplace=True)
        df.dropna(axis="index", how="all", inplace=True)
        self.data = MaccorTabularData(
            as_list=rename_columns(
                df, input_format=self.export_format, target_format=MaccorDataFormat.raw
            ).to_dict(orient="records"),
            data_format=self.export_format,
        )
        first_ten_lines = read_first_x_lines(self.file_path, 10)
        ftl_str = "\n".join(first_ten_lines)
        self.meta = {}
        new_meta = apply_regex_return_match_groups(
            HeaderRegExs[self.export_format.name].value,
            ftl_str,
        )
        for key, value in new_meta.items():
            if "today" in key.lower():
                self.meta["Date of export"] = value
            elif ("started" or "date of test") in key.lower():
                self.meta["Date of test"] = value
            elif "date of test" in key.lower():
                self.meta["Date of test"] = value
            elif "name" in key.lower():
                self.meta["Filename"] = value
            else:
                self.meta[key] = value
        self.meta.update(new_meta)
        # todo: read units from header where possible
        return self

    @field_validator("export_format")
    def check_export_format(cls, v):
        if v not in MaccorDataFormat:
            raise ValueError(f"Export format '{v}' not supported!")
        if v == MaccorDataFormat.raw:
            raise ValueError(
                "Export format 'raw' not supported for text files! Use "
                "'MaccorDataRawFile' instead."
            )
        return v


# Functions
def read_maccor_data_file(
    file_path: Union[str, Path],
    frmt: MaccorDataFormat,
    dll_path: Optional[Union[str, Path]] = None,
):
    # todo: check if current and capacity (sign, accumulative counting etc. can be
    #  read and harmonized)
    """Read a Maccor data file in the specified format

    Parameters
    ----------
    file_path : The path to the file
    frmt : The format of the file
    dll_path : The path to the DLL file - only required to read raw files. If none is
        provided the DLL will be looked for in the default location
        (src/maccor_utility/maccor_dll). The proprietary DLL is not part of this package
        and needs to be provided by the user.
    """
    if frmt == MaccorDataFormat.raw:
        maccor_data_raw_file = MaccorDataRawFile(file_path=file_path, dll_path=dll_path)
        maccor_data_raw_file.read()
        return maccor_data_raw_file
    maccor_data_txt_file = MaccorDataTxtFile(file_path=file_path, export_format=frmt)
    maccor_data_txt_file.read()
    return maccor_data_txt_file


class Translations(Enum):
    raw = TO_RAW
    maccor_export1 = TO_EXPORT1
    maccor_export2 = TO_EXPORT2
    mims_client1 = TO_MIMS_CLIENT1
    mims_client2 = TO_MIMS_CLIENT2
    mims_server2 = TO_MIMS_SERVER2


def rename_columns(
    df: pd.DataFrame,
    input_format: MaccorDataFormat,
    target_format: MaccorDataFormat = MaccorDataFormat.raw,
) -> pd.DataFrame:
    if input_format == target_format:
        return df
    input_to_raw = inverse_dict_one_to_x(Translations[input_format.name].value)
    replacements = input_to_raw
    if not target_format == MaccorDataFormat.raw:
        raw_to_target = flatten_dict_one_to_x(Translations[target_format.name].value)
        replacements = {
            k: raw_to_target.get(v, None)
            for k, v in input_to_raw.items()
            if raw_to_target.get(v, None) is not None
        }
    df.rename(columns=replacements, inplace=True, errors="ignore")
    return df


def datetime_fromdelphi(dvalue: float):
    """

    Parameters
    ----------
    dvalue : float
        Datetime as float

    Returns
    -------
    datetime.datetime

    References
    ----------
    [1] https://stackoverflow.com/questions/49599004/
    how-to-convert-a-python-datetime-to-a-delphi-tdatetime
    """
    # A delphi datetime value is the (fractional) number of days since the epoch
    # e.g. 42 minutes past the UNIX epoch is 25569.029166666667 in Delphi terms.
    delphi_epoch = datetime.datetime(year=1899, month=12, day=30)
    return delphi_epoch + datetime.timedelta(days=dvalue)


def get_bool_array_from_bit_field(
    ctype_bitfield, opts: Dict[str, bool] = None
) -> List[bool]:
    # example
    # bitfield = ctypes.c_uint8(0b01100000)
    # value = bitfield.value
    # bool_array = get_bool_array_from_bit_field(bitfield)
    # print("{}: {}".format(value, bool_array))
    if opts is None:  # don't use mutable objects as default value
        opts = {"most_significant_bit_first": True}
    bitfield = ctype_bitfield  # copy value
    bit_len = 8 * ctypes.sizeof(bitfield)  # bit size is 8 * byte size
    bit_map = ctypes.c_uint8(1)  # map to select least significant bit first
    bool_array = []  # result array

    for x in range(0, bit_len):
        bit_set = ctypes.c_bool(
            (bitfield.value & bit_map.value)
        )  # compare the lowest bit
        bool_array.append(bit_set.value)
        bitfield.value >>= 1  # shift one bit to the right, equal to device by 2

    if opts["most_significant_bit_first"]:
        bool_array.reverse()
    return bool_array


class DllArchitecture(StrEnum):
    _order_ = "bit32 bit64"
    bit32 = "32bit"
    bit64 = "64bit"


def get_top_lvl_procedure(
    path_to_file: Union[str, Path],
    save_procedure_to: Union[str, Path],
    loaded_dll: Optional[ctypes.CDLL] = None,
    path_to_dll: Optional[Union[str, Path]] = None,
    dll_architecture: Optional[DllArchitecture] = DllArchitecture.bit64,
):
    """Python wrapper for MacReadDataFileLIB.dll to read the top level procedure from a
    Maccor raw file directly. Top level means here the main procedure without the
    called subroutine

    Parameters
    ----------
    path_to_file : str or pathlib.Path
        Path to the file to read in
    save_procedure_to : str or pathlib.Path
        Path to save the procedure to
    loaded_dll :
        The loaded DLL, actually a ctypes.WinDLL
    path_to_dll : str or None or pathlib.Path
        Choose 'None' to use the DLL provided with this repository, otherwise specify
        a path.
    dll_architecture: str
        Has two options: '32bit' and '64bit'. Has no relevance if path_to_dll is not
        None

    Returns
    -------

    """
    # will use maccor dll
    # check and eventually replace optional parameters
    if path_to_dll is None:
        warn("No DLL path provided. Trying to use default path.")
        # Determine whether the operating system is 32bit or 64 bit
        dll_root = Path(__file__).parent / "maccor_dll"
        path_to_dll = dll_root / "MacReadDataFileLIB 32 bit" / "MacReadDataFileLIB.dll"
        if sys.maxsize > 2**32:
            path_to_dll = (
                dll_root / "MacReadDataFileLIB 64 bit" / "MacReadDataFileLIB.dll"
            )
    # the Maccor dll
    if loaded_dll is None:
        md = ctypes.WinDLL(str(Path(path_to_dll).resolve()))
    else:
        md = loaded_dll
    # specify the path to the file, make the path absolute
    p2f_path = str(Path(path_to_file).resolve())
    # we actually need a reference to an ascii encoded buffer of the string - more or
    # less try-and-error without the dll
    # source code
    p2f_enc = p2f_path.encode("ascii")
    p2f_enc_buff = ctypes.create_string_buffer(p2f_enc)
    p2f = ctypes.byref(p2f_enc_buff)
    # same goes for the saving path
    sp2_path = str(Path(save_procedure_to).resolve())
    sp2_enc = sp2_path.encode("ascii")
    sp2_enc_buff = ctypes.create_string_buffer(sp2_enc)
    sp2 = ctypes.byref(sp2_enc_buff)
    # creating the file handle
    hdl = md.OpenDataFileASCII(p2f)
    md.SaveTestProcedureToFileASCII(hdl, sp2)
    # no return value --> function returns None

    # Unlock DLL handle
    if loaded_dll is None:
        handle = md._handle
        ctypes.windll.kernel32.FreeLibrary(handle)
        del md


def get_procedure_and_subroutine(path_to_file, save_procedure_to):
    # not implemented yet. Will work as follows:
    # * read raw file as text file
    # * identify sections containing procedure by opening statement
    #   <MaccorTestProcedure> and by closing statement
    #   </MaccorTestProcedure>
    # * read the procedure name from the block of partially encoded text by looking
    #   for '*.000'
    # * the procedure description might be readable as well and can be found in front
    #   of the procedure name
    # * RecNum and StartDateTime of the subroutine call might not be identifiable since
    #   they are encoded / stored in bits
    # * save the XML data as a procedure file
    pass


def import_maccor_cycling_data(file):
    data = pd.read_table(
        filepath_or_buffer=file, header=1, decimal=".", thousands=",", index_col=False
    )
    return data


def import_maccor_cycling_stats(file):
    # Attention: the header line is actually in line 7 (indexed from 0), but an empty
    # line with a new line statement is ignored
    data = pd.read_table(
        filepath_or_buffer=file,
        header=6,
        decimal=",",
        index_col=False,
        encoding="windows-1252",
    )
    return data


# function definition as in readmacfile.py
def process_exists(process_name):
    call = "TASKLIST", "/FI", "imagename eq %s" % process_name
    # use buildin check_output right away
    output = subprocess.check_output(call).decode()
    # check in last line for process name
    last_line = output.strip().split("\r\n")[-1]
    # because Fail message could be translated
    return last_line.lower().startswith(process_name.lower())


# Line before the last line of the file

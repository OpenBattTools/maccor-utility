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
import pathlib
from pathlib import Path

import pandas as pd

# own modules
import maccor_utility.helperfunctions as hf
from maccor_utility.helperfunctions import print_


# classes
class TDLLHeaderData(ctypes.Structure):
    """
    References
    ----------
    [1] https://stackoverflow.com/questions/14771150/python-ctypes-pragma-pack-for-byte-aligned-read
    """

    _pack_ = 1  # packed record
    _fields_ = [
        ("Size", ctypes.c_ulonglong),
        ("FileType", ctypes.c_int32),
        ("SystemType", ctypes.c_int32),
        ("SystemIDLen", ctypes.c_int32),
        ("TestChan", ctypes.c_int32),
        ("TestNameLen", ctypes.c_int32),
        ("TestInfoLen", ctypes.c_int32),
        ("ProcNameLen", ctypes.c_int32),
        ("ProcDescLen", ctypes.c_int32),
        ("Mass", ctypes.c_float),
        ("Volume", ctypes.c_float),
        ("Area", ctypes.c_float),
        ("C_Rate", ctypes.c_float),
        ("V_Rate", ctypes.c_float),
        ("R_Rate", ctypes.c_float),
        ("P_Rate", ctypes.c_float),
        ("I_Rate", ctypes.c_float),
        ("E_Rate", ctypes.c_float),
        ("ParallelR", ctypes.c_float),
        ("VDivHiR", ctypes.c_float),
        ("VDivLoR", ctypes.c_float),
        ("HeaderIndex", ctypes.c_int32),
        ("LastRecNum", ctypes.c_int32),
        ("TestStepNum", ctypes.c_int32),
        ("StartDateTime", ctypes.c_double),
        ("MaxV", ctypes.c_float),
        ("MinV", ctypes.c_float),
        ("MaxChI", ctypes.c_float),
        ("MaxDisChI", ctypes.c_float),
        ("AUXtot", ctypes.c_ushort),
        ("SMBtot", ctypes.c_ushort),
        ("CANtot", ctypes.c_ushort),
        ("EVChamberNum", ctypes.c_ushort),
        ("HasDigIO", ctypes.c_bool),
        ("MaxStepsPerSec", ctypes.c_float),
        ("MaxDataRate", ctypes.c_float),
    ]
    field_strings_ = [field_tpl[0] for field_tpl in _fields_]


class TDLLTimeData(ctypes.Structure):
    _pack_ = 1  # packed record
    _fields_ = [
        ("RecNum", ctypes.c_ulong),
        ("CycleNumProc", ctypes.c_int),
        ("HalfCycleNumCalc", ctypes.c_int),
        ("StepNum", ctypes.c_ushort),
        ("DPtTime", ctypes.c_double),
        ("TestTime", ctypes.c_double),
        ("StepTime", ctypes.c_double),
        ("Capacity", ctypes.c_double),
        ("Energy", ctypes.c_double),
        ("Current", ctypes.c_float),
        ("Voltage", ctypes.c_float),
        ("ACZ", ctypes.c_float),
        ("DCIR", ctypes.c_float),
        ("MainMode", ctypes.c_wchar),
        ("Mode", ctypes.c_byte),
        ("EndCode", ctypes.c_ubyte),
        ("Range", ctypes.c_byte),
        ("GlobFlags", ctypes.c_ulonglong),
        ("HasVarData", ctypes.c_ushort),
        ("HasGlobFlags", ctypes.c_ushort),
        ("HasFRAData", ctypes.c_ushort),
        ("DigIO", ctypes.c_ushort),
        ("FRAStartTime", ctypes.c_double),
        ("FRAExpNum", ctypes.c_int),
    ]
    field_strings_ = [field_tpl[0] for field_tpl in _fields_]


class TDLLReading(ctypes.Structure):
    _pack_ = 1  # packed record
    _fields_ = [("V", ctypes.c_float), ("I", ctypes.c_float)]  # single;  # single;
    field_strings_ = [field_tpl[0] for field_tpl in _fields_]


class TScopeTraceVI(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("V", ctypes.c_float),
        ("I", ctypes.c_float),
    ]
    field_strings_ = [field_tpl[0] for field_tpl in _fields_]


class TDLLScopeTrace(ctypes.Structure):
    """
    References
    ----------
    [1] https://stackoverflow.com/questions/17101845/python-ctypes-array-of-structs
    """

    _pack_ = 1  # packed record
    _fields_ = [("Samples", ctypes.c_byte), ("Reading", TScopeTraceVI * 50)]
    field_strings_ = [field_tpl[0] for field_tpl in _fields_]


class TDLLFRARecord(ctypes.Structure):
    _pack_ = 1  # packed record
    _fields_ = [
        ("TestTime", ctypes.c_long),
        ("FRAFreq", ctypes.c_float),
        ("fZreal", ctypes.c_float),
        ("fZImag", ctypes.c_float),
        ("fVoltMag", ctypes.c_float),
        ("fCurrMag", ctypes.c_float),
        ("TestVoltage", ctypes.c_float),
    ]
    field_strings_ = [field_tpl[0] for field_tpl in _fields_]


class MacDataFile:
    def __init__(self, rawfile: pathlib.Path):
        if not Path(rawfile).exists():
            raise FileNotFoundError(f"File {rawfile} does not exist!")
        self.file_name = str(rawfile)
        self.data_dict = {}
        print(f"target file: {self.file_name}")

    def read(self, debug: bool = False) -> dict:
        # Patch print function
        def print(msg):
            print_(msg=msg, ts=False, dg=debug)

        # stdcall
        dll_path = str(
            Path(__file__).parents[1] / "maccor_dll" / "MacReadDataFileLIB64bit.dll"
        )
        dll = ctypes.windll.LoadLibrary(dll_path)

        rd = {  # return dictionary
            "Meta data": {
                "Description": {
                    "Description": "Description of the dictionary key-value pairs",
                    "Exceptions": "List of exceptions that occurred during reading of "
                    "the file",
                    "Header dict": "Dictionary containing the the fields of the header "
                    "as keys and the associated values",
                    # 'Header data': 'The header object as received by the function '
                    #                'called from the MacReadDataFileLIB.dll',
                    "Parameters": "Selected parameters, as read from the header of the "
                    "binary Maccor data file",
                    "Units": "Dictionary containing the units for each of the "
                    "parameters.",
                },
                "Exceptions": [],
                "Header dict": {},
                "Parameters": {},
                "Header units": {
                    # See manual > 11.3.1.5 Keywords + 11.3.2.2 Delphi + 11.6.4.7
                    "Size": "",
                    "FileType": "",
                    "SystemType": "",
                    "SystemIDLen": "",
                    "TestChan": "",
                    "TestNameLen": "",
                    "TestInfoLen": "",
                    "ProcNameLen": "",
                    "ProcDescLen": "",
                    "Mass": "g",
                    "Volume": "cm³",
                    "Area": "cm²",
                    "C_Rate": "A",
                    "V_Rate": "V",
                    "R_Rate": "Ohm",
                    "P_Rate": "W",
                    "I_Rate": "A",  # todo: research
                    "E_Rate": "Wh",  # todo: research
                    "ParallelR": "Ohm",  # todo: research
                    "VDivHiR": "Ohm",  # todo: research
                    "VDivLoR": "Ohm",  # todo: research
                    "HeaderIndex": "",
                    "LastRecNum": "",
                    "TestStepNum": "",
                    "StartDateTime": "d",  # days since Delphi epoch (1899)
                    "MaxV": "V",
                    "MinV": "V",
                    "MaxChI": "A",
                    "MaxDisChI": "A",
                    "AUXtot": "",  # number of columns
                    "SMBtot": "",  # number of columns
                    "CANtot": "",  # number of columns
                    "EVChamberNum": "",
                    "HasDigIO": "",
                    "MaxStepsPerSec": "",
                    "MaxDataRate": "s",  # minimum distance between two samples
                },
            },
            "Description": {
                "Description": "Description of the dictionary key-value pairs",
                "Meta data": "Information read from the header of the binary Maccor "
                "data file",
                "Time series data": "The tabular time series data from the Maccor file "
                "as pandas.DataFrame",
                "Units": "Dictionary containing the units for each column in the "
                "time series data",
            },
            "Time series data": "Oops, something went wrong. Have a look in the "
            "Exceptions!",
            "Units": {
                "RecNum": "",
                "CycleNumProc": "",
                "HalfCycleNumCalc": "",
                "StepNum": "",
                "DPtTime": "d",  # days since Delphi epoch
                "TestTime": "s",
                "StepTime": "s",
                "Capacity": "Ah",
                "Energy": "Wh",
                "Current": "A",
                "Voltage": "V",
                "ACZ": "Ohm",
                "DCIR": "Ohm",
                "MainMode": "",
                "Mode": "",
                "EndCode": "",
                "Range": "",
                "GlobFlags": "",
                "HasVarData": "",
                "HasGlobFlags": "",
                "HasFRAData": "",
                "DigIO": "",
                "FRAStartTime": "s",  # todo: check - maybe seconds or  days since
                #  Delphi epoch
                "FRAExpNum": "",
            },
        }

        try:
            # Might be useful later:
            # pfile_name = ctypes.c_wchar_p(self.file_name)  # OpenDataFile
            # pfile_name_ascii = ctypes.c_char_p(self.file_name.encode("utf-8"))
            # OpenDataFileASCII
            s_array = (ctypes.c_wchar * 256)()
            file_handle = dll.OpenDataFile(self.file_name)

            if file_handle >= 0:
                print(f"file access successful! handle = {file_handle}\n")
                # Use the handle to get the header data (Not required)
                hdr_obj = TDLLHeaderData()  # hdr_obj
                dll.GetDataFileHeader(file_handle, ctypes.pointer(hdr_obj))
                # rd["Meta data"]["Header data"] = hdr_obj
                hdr_dict = dict()
                for field in hdr_obj.field_strings_:
                    attr = getattr(hdr_obj, field)
                    hdr_dict[field] = attr
                rd["Meta data"]["Header dict"] = hdr_dict
                # some attributes are asked explicitly for later access
                start_date_time = datetime_fromdelphi(getattr(hdr_obj, "StartDateTime"))
                file_type = getattr(hdr_obj, "FileType")
                test_ch = getattr(hdr_obj, "TestChan")
                mass = getattr(hdr_obj, "Mass")
                volume = getattr(hdr_obj, "Volume")
                c_rate = getattr(hdr_obj, "C_Rate")
                # number of aux/smb/can channels/entries
                aux_tot = getattr(hdr_obj, "AUXtot")  # DLLHeaderData.AUXtot
                smb_tot = getattr(hdr_obj, "SMBtot")  # DLLHeaderData.SMBtot
                # Might be useful later:
                # can_tot = getattr(hdr_obj, "CANtot")  # DLLHeaderData.CANtot
                rd["Meta data"]["Parameters"] = {
                    "Test channel": test_ch,
                    "Mass / g": mass,
                    "Volume": volume,
                    "C-rate / A": c_rate,
                    "Start date time": start_date_time,
                    "Aux units": {},
                    "SMB units": {},
                    "File type": file_type,
                }
                # Use the handle to get the System ID  (Not required)
                dll.GetSystemID(
                    file_handle, ctypes.pointer(s_array), hdr_obj.SystemIDLen
                )
                print(f"System ID is: {s_array.value}")
                sac = copy.deepcopy(s_array)
                rd["Meta data"]["Parameters"]["System ID"] = sac.value
                # Use the handle to get the name of the test procedure (Not required)
                dll.GetProcName(
                    file_handle, ctypes.pointer(s_array), hdr_obj.ProcNameLen
                )
                print(f"Test procedure is: {s_array.value}")
                sac1 = copy.deepcopy(s_array)
                rd["Meta data"]["Parameters"]["Procedure name"] = sac1.value
                # Use the handle to get the name of the test
                dll.GetTestName(
                    file_handle, ctypes.pointer(s_array), hdr_obj.TestNameLen
                )
                print(f"Test name is: {s_array.value}")
                sac2 = copy.deepcopy(s_array)
                rd["Meta data"]["Parameters"]["Test name"] = sac2.value
                # Use the handle to get the test info (Not required)
                dll.GetTestInfo(
                    file_handle, ctypes.pointer(s_array), hdr_obj.TestInfoLen
                )
                print(f"Test info is: {s_array.value}")
                sac3 = copy.deepcopy(s_array)
                rd["Meta data"]["Parameters"]["Test info"] = sac3.value
                # Use the handle to get the procedure description (Not required)
                dll.GetProcDesc(
                    file_handle, ctypes.pointer(s_array), hdr_obj.ProcDescLen
                )
                print(f"Procedure description is: {s_array.value}")
                sac4 = copy.deepcopy(s_array)
                rd["Meta data"]["Parameters"]["Procedure description"] = sac4.value
                # Use the handle to get aux units
                aux_units = dict()
                if aux_tot > 0:
                    for aux_num in range(0, aux_tot):
                        dll.GetAuxUnits(file_handle, aux_num, ctypes.pointer(s_array))
                        print(f"AUX{aux_num+1} unit is: {s_array.value}")
                        sac5 = copy.deepcopy(s_array)
                        aux_units[f"AUX{aux_num+1}"] = sac5.value
                rd["Meta data"]["Parameters"]["Aux units"] = aux_units
                # smb units - not tested
                smb_units = dict()
                if smb_tot > 0:
                    for smb_num in range(0, smb_tot):
                        dll.GetSMBUnits(file_handle, smb_num, ctypes.pointer(s_array))
                        print(f"SMB{smb_num+1} unit is: {s_array.value}")
                        sac6 = copy.deepcopy(s_array)
                        smb_units[f"SMB{smb_num+1}"] = sac6.value
                # Use the handle to get the time (series) data
                dll_time_data = TDLLTimeData()
                # Might be useful later:
                # dll_scope_trace = TDLLScopeTrace()
                # The number of variables depends on the file type
                if file_type == 4:
                    var_cnt = 50
                elif file_type == (1 or 2):
                    var_cnt = 15
                else:
                    var_cnt = 0
                # List of lists to append the data to - an efficient way to read data
                #  into a structure prior to converting to a pandas.DataFrame
                lol = []
                # Counter for the while loop
                count = 0
                # Read the file by calling LoadAndGetNextTimeData until <> 0
                while (
                    dll.LoadAndGetNextTimeData(
                        file_handle, ctypes.pointer(dll_time_data)
                    )
                    == 0
                ):
                    try:
                        sub_list = []
                        # Time series data
                        for field in dll_time_data.field_strings_:
                            attr = getattr(dll_time_data, field)
                            # if field == 'MainMode':
                            #     sub_list.append(attr.decode('ascii'))
                            # else:
                            sub_list.append(attr)
                        # Aux data
                        if aux_tot > 0:
                            for aux_num in range(0, aux_tot):
                                # dll.GetAuxData(
                                #     file_handle,
                                #     aux_num,
                                #     ctypes.pointer(s_array)
                                # )
                                # sac7 = copy.deepcopy(s_array)
                                # sub_list.append(sac7.value)
                                aux_obj = ctypes.c_float(1.0)
                                dll.GetAuxData(
                                    file_handle, aux_num, ctypes.byref(aux_obj)
                                )
                                aux_val = aux_obj.value
                            sub_list.append(aux_val)
                        # Var data
                        has_var_data = getattr(dll_time_data, "HasVarData")
                        if has_var_data == 0:
                            sub_list.extend([0] * var_cnt)
                        else:
                            for var_num in range(1, var_cnt + 1):
                                # var_obj = ctypes.c_float(1.0)
                                # dll.GetVARData(
                                #     file_handle,
                                #     var_num,
                                #     ctypes.byref(var_obj)
                                # )
                                # var_val = var_obj.value
                                # sub_list.append(var_val)
                                var_obj = ctypes.c_float(1.0)
                                dll.GetVARData(
                                    file_handle, var_num, ctypes.byref(var_obj)
                                )
                                var_val = var_obj.value
                                sub_list.append(var_val)
                        # todo:
                        #  * global flags
                        #  * SMB data
                        #  * FRA data
                        #  * EV data
                        #  * scope data

                        # For each loaded data point more details of this data point
                        #  can be accessed
                        # CAN Data
                        CAN_val = ctypes.c_float()
                        can_str = ""
                        for can_num in range(0, 2):  # 0, 1
                            dll.GetCANData(
                                file_handle, can_num, ctypes.pointer(CAN_val)
                            )
                            can_str += (
                                "\nThermistor "
                                + str(can_num)
                                + ": "
                                + "%.3f" % CAN_val.value
                            )
                        for can_num in range(0, 1):  # 0
                            dll.GetCANData(
                                file_handle, can_num, ctypes.pointer(CAN_val)
                            )
                            # CAN0 = "%.4f" % CAN_val.value
                            sub_list.append(CAN_val.value)
                        for can_num in range(1, 2):  # 1
                            dll.GetCANData(
                                file_handle, can_num, ctypes.pointer(CAN_val)
                            )
                            # CAN1 = "%.4f" % CAN_val.value
                            sub_list.append(CAN_val.value)
                        # todo: handle can values in the same way as aux values
                        count += 1
                        lol.append(sub_list)
                    # while try-except
                    except Exception as e:
                        print(f"Exception: {e}")
                        rd["Meta data"]["Exceptions"].append(e)

                # finally close file
                dll.CloseDataFile(file_handle)
                # unload dll
                del dll
                # collect garbage!
                gc.collect()
                # Finalize time data reading by transferring the time series to a
                #  dataframe
                cols = copy.deepcopy(dll_time_data.field_strings_)
                # Column names for aux channel data - is not always required
                if aux_tot > 0:
                    # Indexing of aux channels starts at 1 when adding them in the
                    #  Maccor test control pane
                    aux_col_names = [f"AUX{aux_num+1}" for aux_num in range(0, aux_tot)]
                    cols.extend(aux_col_names)
                # Column names for var data
                var_col_names = [f"VAR{var_num}" for var_num in range(1, var_cnt + 1)]
                cols.extend(var_col_names)
                # Units for var data
                var_units = {col: "" for col in var_col_names}
                # Column names for global flags - global flags read out not implemented
                # glob_flags_col_names = [
                #     f'GlobFlag{glob_flag_num}' for glob_flag_num in range(1, 64 + 1)
                # ]
                # cols.extend(glob_flags_col_names)
                # Column names for smb data - SMB read out not implemented yet
                # if smb_tot > 0:
                #     smb_col_names = [f'SMB{smb_num}' for smb_num in range(0, smb_tot)]
                #     cols.extend(smb_col_names)
                # Column names for fra data - FRA read out not implemented yet
                # Column names for ev data - EV read out not implemented yet
                # Column names for scope - scope read out not implemented yet
                # Column names for CAN data
                can_col_names = ["CAN0", "CAN1"]
                cols.extend(can_col_names)
                # Units for CAN data
                can_units = {col: "" for col in can_col_names}
                rd["Units"].update(
                    {
                        **aux_units,
                        **smb_units,
                        **var_units,
                        **can_units,
                        # **fra_units, **ev_units, **scope_units
                        # global_flag_units
                    }
                )
                rd["Time series data"] = pd.DataFrame(data=lol, columns=cols)
            else:
                raise IOError("Error getting file handle!")

        # read func try-except
        except Exception as e:
            print(f"Exception: {e}")
            rd["Meta data"]["Exceptions"].append(e)
        # todo: make sure that no empty cols are included (if hasglobalflags is 0 in
        #  all records, then the global flags columns should not be present)
        #  same for Var, SMB, FRA, EV, Scope
        self.data_dict = rd
        return rd


# functions
def datetime_fromdelphi(dvalue):
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
    [1] https://stackoverflow.com/questions/49599004/how-to-convert-a-python-datetime-to-a-delphi-tdatetime
    """
    # A delphi datetime value is the (fractional) number of days since the epoch
    # e.g. 42 minutes past the UNIX epoch is 25569.029166666667 in Delphi terms.
    delphi_epoch = datetime.datetime(year=1899, month=12, day=30)
    return delphi_epoch + datetime.timedelta(days=dvalue)


def get_bool_array_from_bit_field(ctype_bitfield, opts=None):
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


def get_top_lvl_procedure(
    path_to_file,
    save_procedure_to,
    loaded_dll=None,
    path_to_dll=None,
    dll_architecture="64bit",
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
    loaded_dll : ctypes.WinDLL
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
        ddl_paths = {
            "32bit": r"maccor_dll/MacReadDataFileLIB32bit.dll",
            "64bit": r"maccor_dll/MacReadDataFileLIB64bit.dll",
        }
        path_to_dll = ddl_paths.get(dll_architecture)
        if path_to_dll is None:
            raise KeyError(
                f"Architecture {dll_architecture} is not one of the specified options!"
            )
    # the Maccor dll
    if loaded_dll is None:
        md = ctypes.WinDLL(str(pathlib.Path(path_to_dll).resolve()))
    else:
        md = loaded_dll
    # specify the path to the file, make the path absolute
    p2f_path = str(pathlib.Path(path_to_file).resolve())
    # we actually need a reference to an ascii encoded buffer of the string - more or
    # less try-and-error without the dll
    # source code
    p2f_enc = p2f_path.encode("ascii")
    p2f_enc_buff = ctypes.create_string_buffer(p2f_enc)
    p2f = ctypes.byref(p2f_enc_buff)
    # same goes for the saving path
    sp2_path = str(pathlib.Path(save_procedure_to).resolve())
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


def read_maccor_raw_data_file(path_to_file: pathlib.Path) -> dict:
    """Python wrapper for MacReadDataFileLIB.dll to read a Maccor raw file's content
    directly.

    Parameters
    ----------
    path_to_file :
        Path to the file to read in

    Returns
    -------
    return_dict :
        Dictionary containing the meta data and time series data read from the specified
         file

    Warnings
    --------
    * Users should use ASCII encoded strings for file name, path, procedure name and
    description only! This means that German umlauts and special characters are not
    permitted!
    * Files created under the old Maccor Test Software (version 1 before ) can not be
    opened with the present DLL.

    Notes
    -----

    References
    ----------
    [1] https://stackoverflow.com/questions/27127413/converting-python-string-object-to-c-char-using-ctypes
    [2] https://stackoverflow.com/questions/55768057/using-dll-on-delphi-in-python
    """
    file = MacDataFile(path_to_file)
    return_dict = file.read()
    return return_dict


def read_maccor_data(
    file,
    option,
    decimal=None,
    thousands=None,
    header=None,
    encoding=None,
    remove_nan_cols=True,
):
    # todo: implement translation of column names according to set standard for every
    #  case below
    """

    Parameters
    ----------
    file : filepath, buffer, or pathlib.Path object
        The file to read from
    option : str
        One of the following:
            * 'raw',
            * 'Maccor Éxport 1'
            * 'Maccor Export 2'
            * 'MIMS Server 2'
            * 'MIMS Client 1'
            * 'MIMS Client 2
    decimal : str or None
        Decimal separator
    thousands : str or None
        Separator for thousands
    header : int or None
        0 denotes the first line of the file (if skip_blank_lines == False), as the
        lines of the file are 0 indexed
    encoding : str


    Returns
    -------

    """

    def rename_columns(df):
        replacements = {
            "RecNum": "Rec",
            "Rec#": "Rec",
            "CycleNumProc": "Cycle P",
            "Cyc#": "Cycle P",
            "StepNum": "Step",
            "Step#": "Step",
            "Full Step #": "Full Step",
            "DPtTime": "DPT Time",
            "DPt Time": "DPT Time",
            "TestTime": "Test Time (s)",
            "StepTime": "Step Time (s)",
            "Capacity": "Capacity (Ah)",
            "Amp-hr": "Capacity (Ah)",
            "Energy": "Energy (Wh)",
            "Watt-hr": "Energy (Wh)",
            "Current": "Current (A)",
            "Amps": "Current (A)",
            "Voltage": "Voltage (V)",
            "Volts": "Voltage (V)",
            "ACZ": "ACImp (Ohms)",
            "ACR": "ACImp (Ohms)",
            "DCIR": "DCIR (Ohms)",
            "MainMode": "MD",
            "State": "MD",
            "EndCode": "ES",
            "Range": "I Range",
            "Resistance": "Resistance (Ohms)",
        }
        for ii in range(0, 65):
            replacements[f"VARx{ii}"] = f"VAR{ii}"
            replacements[f"FLGx{ii}"] = f"GlobFlag{ii}"
            # aux
        # potentially use rename() with a function with regular expression
        # todo: define regex function and pass to rename()
        df.rename(columns=replacements, inplace=True, errors="ignore")
        return df

    def read_maccor_raw(
        file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_
    ):
        data_dict = read_maccor_raw_data_file(
            path_to_file=file_
        )  # already packed in a dictionary
        data_ = data_dict["Time series data"]
        if remove_nan_cols_:
            data_.dropna(axis="columns", how="all", inplace=True)
        data_.dropna(axis="index", how="all", inplace=True)
        data = rename_columns(data_)
        data_dict["Time series data"] = data
        return data_dict

    def read_maccor_export1(
        file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_
    ):
        data_ = pd.read_table(
            filepath_or_buffer=file_,
            header=header_,
            decimal=decimal_,
            thousands=thousands_,
            index_col=False,
            encoding=encoding_,
        )
        if remove_nan_cols_:
            data_.dropna(axis="columns", how="all", inplace=True)
        data_.dropna(axis="index", how="all", inplace=True)
        data = rename_columns(data_)
        return {"Time series data": data}

    def read_maccor_export2(
        file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_
    ):
        data_ = pd.read_table(
            filepath_or_buffer=file_,
            header=header_,
            decimal=decimal_,
            thousands=thousands_,
            index_col=False,
            encoding=encoding_,
        )
        if remove_nan_cols_:
            data_.dropna(axis="columns", how="all", inplace=True)
        data_.dropna(axis="index", how="all", inplace=True)
        data = rename_columns(data_)
        return {"Time series data": data}

    def read_mims_server2(
        file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_
    ):
        data_ = pd.read_table(
            filepath_or_buffer=file_,
            header=header_,
            decimal=decimal_,
            thousands=thousands_,
            index_col=False,
            encoding=encoding_,
        )
        if remove_nan_cols_:
            data_.dropna(axis="columns", how="all", inplace=True)
        data_.dropna(axis="index", how="all", inplace=True)
        data = rename_columns(data_)
        return {"Time series data": data}

    def read_mims_client1(
        file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_
    ):
        # issue: number of columns in header not matching number of columns in the
        #  rest of the file
        # this can be solved by reading the first line of data from the file and
        #  estimate its number of columns
        columns = hf.read_specific_line_from_file(file_, header_).split("\t")
        first_row_with_data = hf.read_specific_line_from_file(file_, header_ + 2)
        number_of_data_columns = len(first_row_with_data.split("\t"))
        cntr = 0
        while number_of_data_columns > len(columns):
            columns.append(f"dummy_col{cntr}")
            cntr += 1
        while number_of_data_columns < len(columns):
            columns = columns[: len(columns) - 1]
        try:
            data_ = pd.read_table(
                filepath_or_buffer=file_,
                names=columns,
                skiprows=header_ + 1,
                decimal=decimal_,
                thousands=thousands_,
                index_col=False,
                encoding=encoding_,
                skip_blank_lines=False,
            )
            if remove_nan_cols_:
                data_.dropna(axis="columns", how="all", inplace=True)
            data_.dropna(axis="index", how="all", inplace=True)
        except Exception as e:
            raise e
        data = rename_columns(data_)
        return {"Time series data": data}

    def read_mims_client2(
        file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_
    ):
        data_ = pd.read_table(
            filepath_or_buffer=file_,
            header=header_,
            decimal=decimal_,
            thousands=thousands_,
            index_col=False,
            encoding=encoding_,
        )
        if remove_nan_cols_:
            data_.dropna(axis="columns", how="all", inplace=True)
        data_.dropna(axis="index", how="all", inplace=True)
        data = rename_columns(data_)
        return {"Time series data": data}

    switcher = {
        "raw": {
            "decimal": ".",
            "encoding": None,
            "header": None,
            "thousands": ",",
            "function": read_maccor_raw,
        },
        "Maccor Export 1": {
            "decimal": ",",
            "encoding": "utf-8",
            "header": 2,
            "thousands": ".",
            "function": read_maccor_export1,
        },
        "Maccor Export 2": {
            "decimal": ",",
            "encoding": "utf-8",
            "header": 2,
            "thousands": ".",
            "function": read_maccor_export2,
        },
        "MIMS Server 2": {
            "decimal": ".",
            "encoding": "utf-8",
            "header": 1,
            "thousands": ",",
            "function": read_mims_server2,
        },
        "MIMS Client 1": {
            "decimal": ".",
            "encoding": "utf-8",
            "header": 13,
            "thousands": None,
            "function": read_mims_client1,
        },
        "MIMS Client 2": {
            "decimal": ",",
            "encoding": "cp1252",
            "header": 3,
            "thousands": ".",
            "function": read_mims_client2,
        },
    }
    if not Path(file).exists():
        raise FileNotFoundError(f"File {file} does not exist!")
    # 'MIMS Client 1 and MIMS Export 1 should be identical
    switcher["View Data 1"] = switcher["MIMS Client 1"]
    switcher["View Data 2"] = switcher["MIMS Client 2"]
    # Get the function from switcher dictionary, if key is not found in the dictionary,
    #  the default (None) is returned
    func = switcher.get(option).get("function")
    if type(func) is type(None):
        raise KeyError(
            "The selected option for the source to read from is not a defined case!"
        )
    decimal = decimal if decimal is not None else switcher.get(option).get("decimal")
    thousands = (
        thousands if thousands is not None else switcher.get(option).get("thousands")
    )
    header = header if header is not None else switcher.get(option).get("header")
    encoding = (
        encoding if encoding is not None else switcher.get(option).get("encoding")
    )

    return func(file, decimal, thousands, header, encoding, remove_nan_cols)


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


# Line before the last line of the file

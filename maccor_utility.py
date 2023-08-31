#!/usr/bin/env python
# -*- coding: utf-8 -*-

__docformat__ = "NumPy"
__author__ = "Lukas Gold, Simon Stier"

__doc__ = """
Created on Tue Mar 29 12:28:17 2022
Last modified: see git version control

@author: lukas.gold | luk55302 | lukas.gold@isc.fraunhofer.de
@author: simon.stier | sim09011 | simon.stier@isc.fraunhofer.de

Description:
------------
A Python wrapper for the MacReadDataFileLIB.dll provided by Maccor, Inc.
Contributions are welcome and manged with requests for pulls or
issues.

This is very much a work in progress and not yet ready or stable for use in a data 
pipeline or production environment!

Notes:
------
What to read from the raw file
* header lines --> TDLLHeaderData
  * System --> GetSystemIDASCII
  * Test info --> GetTestInfoASCII
  * procedure
    * GetProcNameASCII
    * GetProcDescASCII
    * SaveTestProcedureToFileASCII
* time data --> TDLLTimeData | check if HasVarData, HasGlobFlags, HasFRAData
  --> after each read function below has been called: LoadAndGetNextTimeData
  * RecNum
  * CycleNumProc (Cycle P?)
  * HalfCycleNumCalc (Cycle C?)
  * StepNum
  * DPtTime (typo? Instead maybe DPTTime? DptTime?)
  * TestTime
  * StepTime
  * Capacity
  * Energy
  * Current
  * Voltage
  * ACZ
  * DCIR
  * MainMode
  * Mode
  * EndCode
  * Range
  * GlobFlags
  * HasVarData: if HasVarData: --> GetVARData
    => Variable names, list of values
  * HasGlobFlags: if HasGlobFlags: --> read from TDLLTimeData
  * HasFRAData: if HasFraData: --> GetFRAData, read from TDLLFRARecord
  * DigIO
  * FRAStartTime 
  * FRAExpNum
  
  What about: 
  * Aux data? 
    * Units --> GetAuxUnitsASCII
    * Data --> GetAuxData
    => list of values, units, labels
  * SMB?
    * Units --> GetSMBUnitsASCII
    * Data --> GetSMBDataASCII, GetSMBDataWideChar
    => list of values, units, labels
  * Scope trace? --> GetScopeTrace, read from TDLLScopeTrace 
  * EV data? --> GetEVData
  * Scope trace --> TDLLScopeTrace
    * Samples: byte; //Number of samples in a ms
    * Reading: array[0..49] of packed record
      * V: single;
      * I: single;
  * FRA record --> TDLLFRARecord
    * TestTime: longint;
    * FRAFreq: single;
    * fZreal: single;
    * fZImag: single;
    * fVoltMag: single;
    * fCurrMag: single
    * TestVoltage: single
"""

# Open tasks:
# todo: function to read xml structure from raw file and save to file
# todo: write a server and client structure to open a raw file using the dll on a remote windows machine and return the
#       dictionary containing the pandas.DataFrame to the JupyterLab (linux machine)
# herefore we need to open the file as text, look for the xml opening and closing statements and cut the pieces in
# between. Then look for '.000' string within clear text sections of the encoded part
# todo: ask maccor for access to fullstep #
# todo: ask maccor for access to datetime + rec# to identify subroutine calls + loop count


# import modules
import ctypes
import datetime
import pathlib
import pandas as pd
import pandas
import copy
# own modules
import helperfunctions as hf


# classes
class TDLLHeaderData(ctypes.Structure):
    """
    References
    ----------
    [1] https://stackoverflow.com/questions/14771150/python-ctypes-pragma-pack-for-byte-aligned-read
    """
    _pack_ = 1  # packed record
    _fields_ = [
        ('Size', ctypes.c_uint64),
        ('FileType', ctypes.c_int),  # 1: MacTest32; 2: Indexed; 3: ASCII; 4: NG
        ('SystemType', ctypes.c_int),
        ('SystemIDLen', ctypes.c_int),
        ('TestChan', ctypes.c_int),
        ('TestNameLen', ctypes.c_int),
        ('TestInfoLen', ctypes.c_int),
        ('ProcNameLen', ctypes.c_int),
        ('ProcDescLen', ctypes.c_int),
        ('Mass', ctypes.c_float),
        ('Volume', ctypes.c_float),
        ('Area', ctypes.c_float),
        ('C_Rate', ctypes.c_float),
        ('V_Rate', ctypes.c_float),
        ('R_Rate', ctypes.c_float),
        ('P_Rate', ctypes.c_float),
        ('I_Rate', ctypes.c_float),
        ('E_Rate', ctypes.c_float),
        ('ParallelR', ctypes.c_float),
        ('VDivHiR', ctypes.c_float),
        ('VDivLoR', ctypes.c_float),
        ('HeaderIndex', ctypes.c_int),
        ('LastRecNum', ctypes.c_int),
        ('TestStepNum', ctypes.c_int),
        ('StartDateTime', ctypes.c_double),  # delphi:TDateTime
        ('MaxV', ctypes.c_float),
        ('MinV', ctypes.c_float),
        ('MaxChI', ctypes.c_float),
        ('MaxDisChI', ctypes.c_float),
        ('AUXtot', ctypes.c_uint16),  # delphi:word
        ('SMBtot', ctypes.c_uint16),
        ('CANtot', ctypes.c_uint16),
        ('EVChamberNum', ctypes.c_uint16),
        ('HasDigIO', ctypes.c_bool),
        ('MaxStepsPerSec', ctypes.c_float),
        ('MaxDataRate', ctypes.c_float)]

    @property
    def fields_(self):
        return self._fields_


class TDLLTimeData(ctypes.Structure):
    _pack_ = 1  # packed record
    _fields_ = [
        ('RecNum', ctypes.c_uint32),  # dword;
        ('CycleNumProc', ctypes.c_int),  # integer;
        ('HalfCycleNumCalc', ctypes.c_int),  # integer;
        ('StepNum', ctypes.c_uint16),  # word;
        ('DPtTime', ctypes.c_double),  # TDateTime;
        ('TestTime', ctypes.c_double),  # double;
        ('StepTime', ctypes.c_double),  # double;
        ('Capacity', ctypes.c_double),  # double;
        ('Energy', ctypes.c_double),  # double;
        ('Current', ctypes.c_float),  # single;
        ('Voltage', ctypes.c_float),  # single;
        ('ACZ', ctypes.c_float),  # single;
        ('DCIR', ctypes.c_float),  # single;
        ('MainMode', ctypes.c_char),  # Char;
        ('Mode', ctypes.c_uint8),  # Byte;  ctypes.c_byte
        ('something', ctypes.c_uint8),  # a guess
        ('EndCode', ctypes.c_uint8),  # Byte;  what we tried before: ctypes.c_byte
        ('Range', ctypes.c_uint8),  # byte;  what we tried before: ctypes.c_byte
        ('GlobFlags', ctypes.c_uint64),  # uint64;
        ('HasVarData', ctypes.c_uint16),  # word;
        ('HasGlobFlags', ctypes.c_uint16),  # word;
        ('HasFRAData', ctypes.c_uint16),  # word;
        ('DigIO', ctypes.c_uint16),  # word;
        ('FRAStartTime', ctypes.c_double),  # TDateTime;
        ('FRAExpNum', ctypes.c_int)]  # integer;

    @property
    def fields_(self):
        return self._fields_


class TDLLReading(ctypes.Structure):
    _pack_ = 1  # packed record
    _fields_ = [
        ('V', ctypes.c_float),  # single;
        ('I', ctypes.c_float)]  # single;

    @property
    def fields_(self):
        return self._fields_


class TDLLScopeTrace(ctypes.Structure):
    """
    References
    ----------
    [1] https://stackoverflow.com/questions/17101845/python-ctypes-array-of-structs
    """
    _pack_ = 1  # packed record
    _fields_ = [
        ('Samples', ctypes.c_byte),  # byte; //Number of samples in a ms
        ('Reading', ctypes.POINTER(TDLLReading))]  # array[0..49] of packed record

    def __init__(self, num_of_structs=50):
        elms = (TDLLReading * num_of_structs)()
        self.STRUCT_ARRAY = ctypes.cast(elms, ctypes.POINTER(TDLLReading))
        self.elements = num_of_structs

        for num in range(0, num_of_structs):
            self.STRUCT_ARRAY[num].field_1 = 1
            self.STRUCT_ARRAY[num].field_2 = 2
            self.STRUCT_ARRAY[num].field_3 = 3
            self.STRUCT_ARRAY[num].field_4 = 4

    @property
    def fields_(self):
        return self._fields_


class TDLLFRARecord(ctypes.Structure):
    _pack_ = 1  # packed record
    _fields_ = [
        ('TestTime', ctypes.c_int),  # longint; 4-byte signed integer in win32 / win64
        ('FRAFreq', ctypes.c_float),  # single;
        ('fZreal', ctypes.c_float),  # single;
        ('fZImag', ctypes.c_float),  # single;
        ('fVoltMag', ctypes.c_float),  # single;
        ('fCurrMag', ctypes.c_float),  # single
        ('TestVoltage', ctypes.c_float)]  # single

    @property
    def fields_(self):
        return self._fields_


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
    # e.g. 42 minutes past the the UNIX epoch is 25569.029166666667 in Delphi terms.
    delphi_epoch = datetime.datetime(1899, 12, 30)
    return delphi_epoch + datetime.timedelta(days=dvalue)


def get_bool_array_from_bit_field(ctype_bitfield, opts=None):
    # example
    # bitfield = ctypes.c_uint8(0b01100000)
    # value = bitfield.value
    # bool_array = get_bool_array_from_bit_field(bitfield)
    # print("{}: {}".format(value, bool_array))
    if opts is None:  # don't use mutable objects as default value
        opts = {'most_significant_bit_first': True}
    bitfield = ctype_bitfield  # copy value
    bit_len = 8*ctypes.sizeof(bitfield)  # bit size is 8 * byte size
    bit_map = ctypes.c_uint8(1)  # map to select least significant bit first
    bool_array = []  # result array

    for x in range(0, bit_len):
        bit_set = ctypes.c_bool((bitfield.value & bit_map.value))  # compare the lowest bit
        bool_array.append(bit_set.value)
        bitfield.value >>= 1  # shift one bit to the right, equal to device by 2

    if opts['most_significant_bit_first']:
        bool_array.reverse()
    return bool_array


def get_top_lvl_procedure(path_to_file, save_procedure_to, path_to_dll=None, dll_architecture='64bit'):
    """Python wrapper for MacReadDataFileLIB.dll to read the top level procedure from a Maccor raw file directly. Top
    level means here the main procedure without the called subroutine

    Parameters
    ----------
    path_to_file : str or pathlib.Path
        Path to the file to read in
    save_procedure_to : str or pathlib.Path
        Path to save the procedure to
    path_to_dll : str or None or pathlib.Path
        Choose 'None' to use the DLL provided with this repository, otherwise specify a path.
    dll_architecture: str
        Has two options: '32bit' and '64bit'. Has no relevance if path_to_dll is not None

    Returns
    -------

    """
    # will use maccor dll
    # check and eventually replace optional parameters
    if path_to_dll is None:
        ddl_paths = {
            '32bit': r'maccor_dll/MacReadDataFileLIB32bit.dll',
            '64bit': r'maccor_dll/MacReadDataFileLIB64bit.dll'
        }
        path_to_dll = ddl_paths.get(dll_architecture)
        if path_to_dll is None:
            raise KeyError(f'Architecture {dll_architecture} is not one of the specified options!')
    # the Maccor dll
    md = ctypes.WinDLL(str(pathlib.Path(path_to_dll).resolve()))
    # specify the path to the file, make the path absolute
    p2f_path = str(pathlib.Path(path_to_file).resolve())
    # we actually need a reference to an ascii encoded buffer of the string - more or less try-and-error without the dll
    # source code
    p2f_enc = p2f_path.encode('ascii')
    p2f_enc_buff = ctypes.create_string_buffer(p2f_enc)
    p2f = ctypes.byref(p2f_enc_buff)
    # same goes for the saving path
    sp2_path = str(pathlib.Path(save_procedure_to).resolve())
    sp2_enc = sp2_path.encode('ascii')
    sp2_enc_buff = ctypes.create_string_buffer(sp2_enc)
    sp2 = ctypes.byref(sp2_enc_buff)
    # creating the file handle
    hdl = md.OpenDataFileASCII(p2f)
    md.SaveTestProcedureToFileASCII(hdl, sp2)
    # no return value --> function returns None


def get_procedure_and_subroutine(path_to_file, save_procedure_to):
    # not implemented yet. Will work as follows:
    # * read raw file as text file
    # * identify sections containing procedure by opening statement <MaccorTestProcedure> and by closing statement
    #   </MaccorTestProcedure>
    # * read the procedure name from the block of partially encoded text by looking for '*.000'
    # * the procedure description might be readable as well and can be found in front of the procedure name
    # * RecNum and StartDateTime of the subroutine call might not be identifiable since they are encoded / stored in
    #   bits
    # * save the XML data as a procedure file
    pass


def read_maccor_raw_data_file(path_to_file, path_to_dll=None, dll_architecture='64bit'):
    """Python wrapper for MacReadDataFileLIB.dll to read a Maccor raw file's content directly

    Parameters
    ----------
    path_to_file : str or pathlib.Path
        Path to the file to read in
    path_to_dll : str or None or pathlib.Path
        Choose 'None' to use the DLL provided with this repository, otherwise specify a path.
    dll_architecture: str
        Has two options: '32bit' and '64bit'. Has no relevance if path_to_dll is not None

    Returns
    -------
    return_dict : dict
        Dictionary containing the meta data and time series data read from the specified file

    Warnings
    --------
    * Users should use ASCII encoded strings for file name, path, procedure name and description only! This means that
      German umlauts and special characters are not permitted!
    * Files created under the old Maccor Test Software (version 1 before ) can not be opened with the present DLL.

    Notes
    -----

    References
    ----------
    [1] https://stackoverflow.com/questions/27127413/converting-python-string-object-to-c-char-using-ctypes
    [2] https://stackoverflow.com/questions/55768057/using-dll-on-delphi-in-python
    """
    # check and eventually replace optional parameters
    if path_to_dll is None:
        ddl_paths = {
            '32bit': r'maccor_dll/MacReadDataFileLIB32bit.dll',
            '64bit': r'maccor_dll/MacReadDataFileLIB64bit.dll'
        }
        path_to_dll = ddl_paths.get(dll_architecture)
        if path_to_dll is None:
            raise KeyError(f'Architecture {dll_architecture} is not one of the specified options!')
    # the Maccor dll
    md = ctypes.WinDLL(str(pathlib.Path(path_to_dll).resolve()))
    # specify the path to the file, make the path absolute
    p2f_path = str(pathlib.Path(path_to_file).resolve())
    # we actually need a reference to an ascii encoded buffer of the string - more or less try-and-error without the dll
    # source code - see reference [1] and [2]
    p2f_enc = p2f_path.encode('ascii')  # eventually the chosen
    p2f_enc_buff = ctypes.create_string_buffer(p2f_enc)
    p2f = ctypes.byref(p2f_enc_buff)
    # creating the file handle
    hdl = md.OpenDataFileASCII(p2f)
    # preparing reading of the header
    hdr_obj = TDLLHeaderData()
    hdr_field_strings = [field_tpl[0] for field_tpl in hdr_obj.fields_]
    # reading meta data from header
    md.GetDataFileHeader(hdl, ctypes.byref(hdr_obj))
    data_file_header = hdr_obj
    # dictionary to store the key (field): value pairs of the header
    hdr_dict = dict()
    for field in hdr_field_strings:
        attr = getattr(hdr_obj, field)
        hdr_dict[field] = attr
    # some attributes are asked explicitly for later access
    start_date_time = datetime_fromdelphi(getattr(hdr_obj, 'StartDateTime'))
    file_type = getattr(hdr_obj, 'FileType')
    test_ch = getattr(hdr_obj, 'TestChan')
    mass = getattr(hdr_obj, 'Mass')
    volume = getattr(hdr_obj, 'Volume')
    c_rate = getattr(hdr_obj, 'C_Rate')
    # number of aux/smb/can channels/entries
    aux_tot = getattr(hdr_obj, 'AUXtot')  # DLLHeaderData.AUXtot
    smb_tot = getattr(hdr_obj, 'SMBtot')  # DLLHeaderData.SMBtot
    can_tot = getattr(hdr_obj, 'CANtot')  # DLLHeaderData.CANtot
    # The number of variables depends on the file type
    if file_type == 4:
        var_cnt = 50
    elif file_type == (1 or 2):
        var_cnt = 15
    # test name
    test_nm_len = getattr(hdr_obj, 'TestNameLen')
    test_nm_obj = ctypes.create_string_buffer(test_nm_len)
    md.GetTestNameASCII(hdl, ctypes.byref(test_nm_obj), test_nm_len)
    test_nm_str = test_nm_obj.value.decode('cp1252')  # the employees often use non 'ascii' chars
    # test info
    # todo: test with a file containing a test info
    test_info_len = getattr(hdr_obj, 'TestInfoLen')
    test_info_obj = ctypes.create_string_buffer(test_info_len)
    md.GetTestInfoASCII(hdl, ctypes.byref(test_info_obj), test_info_len)
    test_info_str = test_info_obj.value.decode('cp1252')  # the employees often use non 'ascii' chars
    # system id
    sys_id_len = getattr(hdr_obj, 'SystemIDLen')
    sys_id_obj = ctypes.create_string_buffer(sys_id_len)
    md.GetSystemIDASCII(hdl, ctypes.byref(sys_id_obj), sys_id_len)
    sys_id_str = sys_id_obj.value.decode('ascii')
    # procedure name
    proc_nm_len = getattr(hdr_obj, 'ProcNameLen')
    proc_nm_obj = ctypes.create_string_buffer(proc_nm_len)
    md.GetProcNameASCII(hdl, ctypes.byref(proc_nm_obj), proc_nm_len)
    proc_nm_str = proc_nm_obj.value.decode('cp1252')  # the employees often use non 'ascii' chars
    # procedure description
    proc_desc_len = getattr(hdr_obj, 'ProcDescLen')
    proc_desc_obj = ctypes.create_string_buffer(proc_nm_len)
    md.GetProcDescASCII(hdl, ctypes.byref(proc_desc_obj), proc_desc_len)
    proc_desc_str = proc_desc_obj.value.decode('cp1252')  # the employees often use non 'ascii' chars
    # aux units
    aux_units = dict()
    if aux_tot > 0:
        for aux_num in range(0, aux_tot):
            aux_u_obj = ctypes.c_char()
            md.GetAuxUnitsASCII(hdl, aux_num, ctypes.byref(aux_u_obj))
            aux_u_val = aux_u_obj.value.decode('ascii')
            aux_units[f'AUX{aux_num+1}'] = aux_u_val  # todo: check with other files and Viewer to see if indexing
    # smb units - not tested
    smb_units = dict()
    if smb_tot > 0:
        for smb_num in range(0, smb_tot):
            smb_u_obj = ctypes.c_char()
            md.GetAuxUnitsASCII(hdl, smb_num, smb_u_obj)
            smb_u_val = smb_u_obj.value.decode('ascii')
            aux_units[f'SMB{smb_num}'] = smb_u_val
    # read time data
    time_dt_obj = TDLLTimeData()
    # list of lists to append the data to - an efficient way to read data into a structure prior to converting to a
    # pandas.DataFrame
    lol = list()
    field_strs = [field_tpl[0] for field_tpl in time_dt_obj.fields_]
    while md.LoadAndGetNextTimeData(hdl, ctypes.byref(time_dt_obj)) == 0:
        sub_list = list()
        # time series data
        for field in field_strs:
            attr = getattr(time_dt_obj, field)
            if field == 'MainMode':
                sub_list.append(attr.decode('ascii'))
            else:
                sub_list.append(attr)
        # aux data
        if aux_tot > 0:
            for aux_num in range(0, aux_tot):
                aux_obj = ctypes.c_float(1.0)
                md.GetAuxData(hdl, aux_num, ctypes.byref(aux_obj))
                aux_val = aux_obj.value
            sub_list.append(aux_val)
        # var data
        has_var_data = getattr(time_dt_obj, 'HasVarData')
        if has_var_data == 0:
            sub_list.extend([0] * var_cnt)
        else:
            for var_num in range(1, var_cnt+1):
                var_obj = ctypes.c_float(1.0)
                md.GetVARData(hdl, var_num, ctypes.byref(var_obj))
                var_val = var_obj.value
                sub_list.append(var_val)
        # global flags
        has_glob_flags = getattr(time_dt_obj, 'HasGlobFlags')
        # read over global flag bits and store 0/1 in a variable each
        if has_glob_flags == 0:
            sub_list.extend([False] * 64)  # better options: 0 or np.nan?
        else:
            global_flags_bitfield = ctypes.c_uint64(time_dt_obj.GlobFlags)
            global_flags_array = \
                get_bool_array_from_bit_field(global_flags_bitfield, {'most_significant_bit_first': False})
            # if time_dt_obj.GlobFlags != 0:
            #     print("GlobalFlags value {} = {}".format(time_dt_obj.GlobFlags, global_flags_array))
            sub_list.extend(global_flags_array)
        # SMB data
        # todo: read SMB data - don't forget to provide column names below
        # FRA data
        # todo: read FRA data - don't forget to provide column names below
        # if DLLTimeData.HasFRAData > 0 then
        #   for FRAnum := 0 to DLLTimeData.HasFRAData-1 do
        #      GetFRAData(FileHandle, FRAnum, @FRAData)
        # //Use GetSMBData if you just need the numeric values
        # //Use GetSMBDataWideChar or GetSMBDataASCII if string data are present        #
        # //GetSMBData(FileHandle, SMBNum, SMBval, SMBvalFloat);        #
        # GetSMBDataWideChar(FileHandle, SMBNum, SMBval, SMBvalFloat, @SArray[1], 255);
        # SMBStr:=String(PChar(@SArray[1]));
        # EV data
        # todo: get EV data - don't forget to provide column names below
        # if DLLHeaderData.EVChamberNum > 0 then
        # GetEVData(FileHandle, Chamber, Temp, Hum)
        # Scope Readout probably never used
        # todo: read Scope - don't forget to provide column names below
        # Only available for FileType 4
        # if DLLHeaderData.FileType=4 then
        #    GetScopeTrace

        # when all data at a point in time is read, append the sub_list to the list of lists
        lol.append(sub_list)

    # finalize time data to transfer it to a pandas.DataFrame
    # complete the list of column names - its important to maintain the same order as above
    cols = copy.deepcopy(field_strs)
    # cols for aux channel data - is not always required
    if aux_tot > 0:
        # indexing of aux channels starts at 1 when adding them in the Maccor test control pane
        aux_col_names = [f'AUX{aux_num+1}' for aux_num in range(0, aux_tot)]
        cols.extend(aux_col_names)
    # cols for var data
    var_col_names = [f'VAR{var_num}' for var_num in range(1, var_cnt + 1)]
    cols.extend(var_col_names)
    # cols for global flags
    glob_flags_col_names = [f'GlobFlag{glob_flag_num}' for glob_flag_num in range(1, 64 + 1)]
    cols.extend(glob_flags_col_names)
    # cols for smb data - SMB read out not implemented yet
    # if smb_tot > 0:
    #     smb_col_names = [f'SMB{smb_num}' for smb_num in range(0, smb_tot)]
    #     cols.extend(smb_col_names)
    # cols for fra data - FRA read out not implemented yet
    # cols for ev data - EV read out not implemented yet
    # cols for scope - scope read out not implemented yet
    time_dt_df = pd.DataFrame(data=lol, columns=cols)
    # close the file when you are done
    md.CloseDataFile(hdl)
    # specify the return dictionary
    return_dict = {
        'Meta data': {
            'Description': {
                'Header dict': 'Dictionary containing the the fields of the header as keys and the associated values',
                'Header data': 'The header object as received by the function called from the MacReadDataFileLIB.dll',
                'Parameters': 'Selected parameters, as read from the header of the binary Maccor data file'
            },
            'Parameters': {
                'System ID': sys_id_str,
                'Test name': test_nm_str,
                'Test info': test_info_str,
                'Test channel': test_ch,
                'Procedure name': proc_nm_str,
                'Procedure description': proc_desc_str,
                'Mass / g': mass,
                'Volume': volume,
                'C-rate / A': c_rate,
                'Start date time': start_date_time,
                'Aux units': aux_units,
                'SMB units': smb_units
            },
            'Header dict': hdr_dict,
            'Header data': data_file_header
        },
        'Time series data': time_dt_df,
        'Description': {
            'Meta data': 'Information read from the header of the binary Maccor data file',
            'Time series data': 'The tabular time series data from the Maccor file as pandas.DataFrame'
        }
    }
    return return_dict


def read_maccor_data(file, option, decimal=None, thousands=None, header=None, encoding=None, remove_nan_cols=True):
    # todo: implement translation of column names according to set standard for every case below
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
        0 denotes the first line of the file (if skip_blank_lines == False), as the lines of the file are 0 indexed
    encoding : str


    Returns
    -------

    """
    def rename_columns(df):
        replacements = {
            'RecNum': 'Rec',
            'Rec#': 'Rec',
            'CycleNumProc': 'Cycle P',
            'Cyc#': 'Cycle P',
            'StepNum': 'Step',
            'Step#': 'Step',
            'Full Step #': 'Full Step',
            'DPtTime': 'DPT Time',
            'DPt Time': 'DPT Time',
            'TestTime': 'Test Time (s)',
            'StepTime': 'Step Time (s)',
            'Capacity': 'Capacity (Ah)',
            'Amp-hr': 'Capacity (Ah)',
            'Energy': 'Energy (Wh)',
            'Watt-hr': 'Energy (Wh)',
            'Current': 'Current (A)',
            'Amps': 'Current (A)',
            'Voltage': 'Voltage (V)',
            'Volts': 'Voltage (V)',
            'ACZ': 'ACImp (Ohms)',
            'ACR': 'ACImp (Ohms)',
            'DCIR': 'DCIR (Ohms)',
            'MainMode': 'MD',
            'State': 'MD',
            'EndCode': 'ES',
            'Range': 'I Range',
            'Resistance': 'Resistance (Ohms)'
        }
        for ii in range(0, 65):
            replacements[f'VARx{ii}'] = f'VAR{ii}'
            replacements[f'FLGx{ii}'] = f'GlobFlag{ii}'
            # aux
        # potentially use rename() with a function with regular expression
        # todo: define regex function and pass to rename()
        df.rename(columns=replacements, inplace=True, errors='ignore')
        return df

    def read_maccor_raw(file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_):
        data_dict = read_maccor_raw_data_file(path_to_file=file_)  # already packed in a dictionary
        data_ = data_dict['Time series data']
        if remove_nan_cols_:
            data_.dropna(axis='columns', how='all', inplace=True)
        data_.dropna(axis='index', how='all', inplace=True)
        data = rename_columns(data_)
        data_dict['Time series data'] = data
        return data_dict

    def read_maccor_export1(file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_):
        data_ = pd.read_table(filepath_or_buffer=file_, header=header_, decimal=decimal_, thousands=thousands_,
                              index_col=False, encoding=encoding_)
        if remove_nan_cols_:
            data_.dropna(axis='columns', how='all', inplace=True)
        data_.dropna(axis='index', how='all', inplace=True)
        data = rename_columns(data_)
        return {'Time series data': data}

    def read_maccor_export2(file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_):
        data_ = pd.read_table(filepath_or_buffer=file_, header=header_, decimal=decimal_, thousands=thousands_,
                              index_col=False, encoding=encoding_)
        if remove_nan_cols_:
            data_.dropna(axis='columns', how='all', inplace=True)
        data_.dropna(axis='index', how='all', inplace=True)
        data = rename_columns(data_)
        return {'Time series data': data}

    def read_mims_server2(file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_):
        data_ = pd.read_table(filepath_or_buffer=file_, header=header_, decimal=decimal_, thousands=thousands_,
                              index_col=False, encoding=encoding_)
        if remove_nan_cols_:
            data_.dropna(axis='columns', how='all', inplace=True)
        data_.dropna(axis='index', how='all', inplace=True)
        data = rename_columns(data_)
        return {'Time series data': data}

    def read_mims_client1(file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_):
        # issue: number of columns in header not matching number of columns in the rest of the file
        # this can be solved by reading the first line of data from the file and estimate its number of columns
        columns = hf.read_specific_line_from_file(file_, header_).split('\t')
        first_row_with_data = hf.read_specific_line_from_file(file_, header_+2)
        number_of_data_columns = len(first_row_with_data.split('\t'))
        cntr = 0
        while number_of_data_columns > len(columns):
            columns.append(f'dummy_col{cntr}')
            cntr += 1
        while number_of_data_columns < len(columns):
            columns = columns[:len(columns) - 1]
        try:
            data_ = pd.read_table(filepath_or_buffer=file_, names=columns, skiprows=header_+1, decimal=decimal_,
                                  thousands=thousands_, index_col=False, encoding=encoding_, skip_blank_lines=False)
            if remove_nan_cols_:
                data_.dropna(axis='columns', how='all', inplace=True)
            data_.dropna(axis='index', how='all', inplace=True)
        except Exception as e:
            raise e
        data = rename_columns(data_)
        return {'Time series data': data}

    def read_mims_client2(file_, decimal_, thousands_, header_, encoding_, remove_nan_cols_):
        data_ = pd.read_table(filepath_or_buffer=file_, header=header_, decimal=decimal_, thousands=thousands_,
                              index_col=False, encoding=encoding_)
        if remove_nan_cols_:
            data_.dropna(axis='columns', how='all', inplace=True)
        data_.dropna(axis='index', how='all', inplace=True)
        data = rename_columns(data_)
        return {'Time series data': data}

    switcher = {
        'raw':             {'decimal': '.', 'encoding': None, 'header': None, 'thousands': ',',
                            'function': read_maccor_raw},
        'Maccor Export 1': {'decimal': ',', 'encoding': 'utf-8', 'header': 2, 'thousands': '.',
                            'function': read_maccor_export1},
        'Maccor Export 2': {'decimal': ',', 'encoding': 'utf-8', 'header': 2, 'thousands': '.',
                            'function': read_maccor_export2},
        'MIMS Server 2':   {'decimal': '.', 'encoding': 'utf-8', 'header': 1, 'thousands': ',',
                            'function': read_mims_server2},
        'MIMS Client 1':   {'decimal': '.', 'encoding': 'utf-8', 'header': 13, 'thousands': None,
                            'function': read_mims_client1},
        'MIMS Client 2':   {'decimal': ',', 'encoding': 'cp1252', 'header': 3, 'thousands': '.',
                            'function': read_mims_client2}
    }
    # 'MIMS Client 1 and MIMS Export 1 should be identical
    switcher['View Data 1'] = switcher['MIMS Client 1']
    switcher['View Data 2'] = switcher['MIMS Client 2']
    # Get the function from switcher dictionary, if key is not found in the dictionary, the default (None) is returned
    func = switcher.get(option).get('function')
    if type(func) is type(None):
        raise KeyError("The selected option for the source to read from is not a defined case!")
    decimal = decimal if decimal is not None else switcher.get(option).get('decimal')
    thousands = thousands if thousands is not None else switcher.get(option).get('thousands')
    header = header if header is not None else switcher.get(option).get('header')
    encoding = encoding if encoding is not None else switcher.get(option).get('encoding')

    return func(file, decimal, thousands, header, encoding, remove_nan_cols)


def import_maccor_cycling_data(file):
    data = pd.read_table(filepath_or_buffer=file, header=1, decimal='.', thousands=',', index_col=False)
    return data


def import_maccor_cycling_stats(file):
    # Attention: the header line is actually in line 7 (indexed from 0), but an empty line with a new line statement
    # is ignored
    data = pd.read_table(filepath_or_buffer=file, header=6, decimal=',', index_col=False, encoding='windows-1252')
    return data


if __name__ == '__main__':
    # Simon's implementation:
    """
    # according to the documentation, this call might be needed before opening a file
    pythoncom.CoInitializeEx(3)

    # 32 bit option
    path_to_dll = r'maccor_dll/MacReadDataFileLIB32bit.dll'
    # 64 bit option
    path_to_dll = r'maccor_dll/MacReadDataFileLIB64bit.dll'

    maccor_dll = ctypes.WinDLL(path_to_dll)

    # file from Maccor#2 (rolled back version of MacTest)
    path_to_file = r'test_data/FN_El-Cell_E88_ECM80_Graphite_2.023'
    # file from Maccor#2 (rolled back verison of MacTest, Procedure written with most recent BuildTest version)
    path_to_file = r'test_data/gron_KI_220210-gron-0100-d2.041'
    # file from Maccor#3 (most recent MacTest version)
    #path_to_file = r'test_data/dau_coorage_Q85_2_cycling.058'

    # we actually need a reference to an ascii encoded buffer of the string - more or less try-and-error without the 
    # dll source code
    # https://stackoverflow.com/questions/27127413/converting-python-string-object-to-c-char-using-ctypes
    # https://stackoverflow.com/questions/55768057/using-dll-on-delphi-in-python
    path_to_file_enc = path_to_file.encode('ascii')
    path_to_file_enc_buff = ctypes.create_string_buffer(path_to_file_enc)
    path_to_file_enc_buff_reference = ctypes.byref(path_to_file_enc_buff)

    # Open file
    print("Open file: {}".format(path_to_file))
    handle = maccor_dll.OpenDataFileASCII(path_to_file_enc_buff_reference)
    print("File Handle: {}".format(handle))

    # Get Header
    header = TDLLHeaderData()

    res = maccor_dll.GetDataFileHeader(handle, ctypes.byref(header))
    print("File Read result: {}".format(res))

    for field in header._fields_:
        print("{}: {}".format(field[0], eval("header.{}".format(field[0]))))  # print all fields
    print("Start time converted: {}".format(datetime_fromdelphi(header.StartDateTime)))

    # get ProcName
    proc_name = ctypes.create_string_buffer(header.ProcNameLen)
    maccor_dll.GetProcNameASCII(handle, ctypes.byref(proc_name), header.ProcNameLen)
    print("ProcName: {}".format(proc_name.value))

    # read actual data / records
    time_data = TDLLTimeData()
    while maccor_dll.LoadAndGetNextTimeData(handle, ctypes.byref(time_data)) == 0:
        #print("Read RecNum: {}: V={}, I={}".format(time_data.RecNum, time_data.Voltage, time_data.Current))
        var = ctypes.c_float(1.0)  # ctypes.c_float

        # we can load vars and this point in time, e. g. var#1
        maccor_dll.GetVARData(handle, 1, ctypes.byref(var))
        #print("Var Read result: {}".format(var.value))

    # print all fields of first record
    for field in time_data._fields_:
        print("{}: {}".format(field[0], eval("time_data.{}".format(field[0]))))  # print all fields

    # Close file
    print("Finished, close file")
    maccor_dll.CloseDataFile(handle);
    """
    # End of Simon's implementation

    test_data_path = pathlib.Path(r'test_data')
    # some test cases for the raw file read
    # -------------------------------------
    test_raw_direct_read = False
    if test_raw_direct_read:
        # path2file = r'test_data/211223_nagl_Sldfy_FN_E84d_Alu_50_pro_kalandriert_4_neu2_raw.039'
        # path2file = r'test_data/madlu_KI_220107-madlu-2000-d_raw.061'
        # path2file = r'test_data/dau_MP_LFP2.0_LP57_0.5MPa_300ul_1_raw.021'
        path2file = r'test_data/220404_go_KI_none_dashboard_test_raw.055'
        maccor_data_dict = read_maccor_raw_data_file(path2file)
        # line before the last line of the file
        save_proc_to = r'C:\Users\gold\Desktop\Files\proc.000'
        get_top_lvl_procedure(path2file, save_proc_to)

    # some test cases for all kinds of file read
    # ------------------------------------------
    test_all_cases = True
    if test_all_cases:
        file_name_com = 'dau_coorage_Q86_5m'
        raw_path = test_data_path / (file_name_com + '_raw.058')
        mims_client1_path = test_data_path / (file_name_com + '_mims_client1.058.txt')
        mims_client2_path = test_data_path / (file_name_com + '_mims_client2.058.txt')
        export1_path = test_data_path / (file_name_com + '_export1.058.txt')
        export2_path = test_data_path / (file_name_com + '_export2.058.txt')
        mims_server2_path = test_data_path / (file_name_com + '_mims_server2.058.txt')

        results = dict()

        options = {
            'raw': raw_path,
            'Maccor Export 1': export1_path,
            'Maccor Export 2': export2_path,
            'MIMS Server 2': mims_server2_path,
            'MIMS Client 1': mims_client1_path,
            'MIMS Client 2': mims_client2_path,
        }

        for (key, value) in options.items():
            results[key] = read_maccor_data(value, key)


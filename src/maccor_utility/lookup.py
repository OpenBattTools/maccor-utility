#!/usr/bin/env python
# -*- coding: utf-8 -*-

__docformat__ = "NumPy"
__author__ = "Lukas Gold, Simon Stier"

import ctypes
import os  # Required
import time  # Required!

# modules as in readmacfile.py
from warnings import warn

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

# Do something to make packages required by the DLL used (to avoid linting error)
_ = type(os)
try:
    _ = type(pythoncom)
except NameError:
    warn("Pythoncom not available.")
_ = type(time)


# Constants
MACCOR_HEADER_UNITS = {  # As in the raw file
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
}

MACCOR_COLUMN_UNITS = {  # As in the raw file
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
}

TO_EXPORT1 = {
    # Column names - raw: [export1]
    "RecNum": ["Rec#"],
    "CycleNumProc": ["Cyc#"],
    "HalfCycleNumCalc": [],
    "StepNum": ["Step"],
    "DPtTime": ["DPt Time"],
    "TestTime": ["TestTime"],
    "StepTime": ["StepTime"],
    "Capacity": ["Amp-hr"],
    "Energy": ["Watt-hr"],
    "Current": ["Amps"],
    "Voltage": ["Volts"],
    "ACZ": ["ACR"],
    "DCIR": ["DCIR"],
    "MainMode": [],
    "Mode": [],
    "EndCode": [],
    "Range": [],
    "GlobFlags": [],
    "HasVarData": [],
    "HasGlobFlags": [],
    "HasFRAData": [],
    "DigIO": [],
    "FRAStartTime": [],
    "FRAExpNum": [],
    # missing: State, ES, EV Temp, EV Hum
}
for ii in range(0, 65):
    TO_EXPORT1[f"VAR{ii}"] = [f"VARx{ii}"]
    TO_EXPORT1[f"GlobFlag{ii}"] = [f"FLGx{ii}"]

TO_RAW = {key: key for key in TO_EXPORT1.keys()}

TO_EXPORT2 = {
    # Column names - raw: [export2]
    "RecNum": ["Rec"],
    "CycleNumProc": ["Cycle P"],
    "HalfCycleNumCalc": ["Cycle C"],
    "StepNum": ["Step"],
    "DPtTime": ["DPT Time"],
    "TestTime": ["Test Time (s)"],
    "StepTime": ["Step Time (s)"],
    "Capacity": ["Capacity (Ah)"],
    "Energy": ["Energy (Wh)"],
    "Current": ["Current (A)"],
    "Voltage": ["Voltage (V)"],
    "ACZ": [],
    "DCIR": ["DCIR (Ohms)"],
    "MainMode": [],
    "Mode": ["MD"],  # todo: check
    "EndCode": ["ES"],
    "Range": ["I Range"],
    "GlobFlags": [],
    "HasVarData": [],
    "HasGlobFlags": [],
    "HasFRAData": [],
    "DigIO": [],
    "FRAStartTime": [],
    "FRAExpNum": [],
    # missing: DIG, I/O, EVTemp (C), EVHum (%), SubR, S.Capacity (Ah/g), Power (W),
    # WF Chg Cap, WF Dis Cap, WF Chg E, WF Dis E, Loop1, Loop2, Loop3, Loop4,
    # Resistance,
}
for ii in range(0, 65):
    TO_EXPORT2[f"VAR{ii}"] = [f"VAR{ii}"]
    TO_EXPORT2[f"GlobFlag{ii}"] = [f"GlobFlag{ii}"]

TO_MIMS_CLIENT1 = {
    # Column names - raw: [mims_client1]
    "RecNum": ["Rec"],
    "CycleNumProc": ["Cycle P"],
    "HalfCycleNumCalc": ["Cycle C"],
    "StepNum": ["Step"],
    "DPtTime": ["DPT Time"],
    "TestTime": ["TestTime"],
    "StepTime": ["StepTime"],
    "Capacity": ["Cap. [Ah]"],
    "Energy": ["Ener. [Wh]"],
    "Current": ["Current [A]"],
    "Voltage": ["Voltage [V]"],
    "ACZ": [],
    "DCIR": [],
    "MainMode": [],
    "Mode": ["Md"],  # todo: check
    "EndCode": ["ES"],
    "Range": [],
    "GlobFlags": [],
    "HasVarData": [],
    "HasGlobFlags": [],
    "HasFRAData": [],
    "DigIO": [],
    "FRAStartTime": [],
    "FRAExpNum": [],
    # missing:
}
for ii in range(0, 65):
    TO_MIMS_CLIENT1[f"VAR{ii}"] = [f"VAR{ii}"]
    TO_MIMS_CLIENT1[f"GlobFlag{ii}"] = [f"GlobFlag{ii}"]

TO_MIMS_CLIENT2 = {
    # Column names - raw: [mims_client2]
    "RecNum": ["Rec"],
    "CycleNumProc": ["Cycle P"],
    "HalfCycleNumCalc": ["Cycle C"],
    "StepNum": ["Step"],
    "DPtTime": ["DPT Time"],
    "TestTime": ["Test Time"],
    "StepTime": ["Step Time"],
    "Capacity": ["Capacity"],
    "Energy": ["Energy"],
    "Current": ["Current"],
    "Voltage": ["Voltage"],
    "ACZ": [],
    "DCIR": [],
    "MainMode": [],
    "Mode": ["MD"],  # todo: check
    "EndCode": ["ES"],
    "Range": [],
    "GlobFlags": [],
    "HasVarData": [],
    "HasGlobFlags": [],
    "HasFRAData": [],
    "DigIO": [],
    "FRAStartTime": [],
    "FRAExpNum": [],
    # missing:
}
for ii in range(0, 65):
    TO_MIMS_CLIENT2[f"VAR{ii}"] = [f"VAR{ii}"]
    TO_MIMS_CLIENT2[f"GlobFlag{ii}"] = [f"GlobFlag{ii}"]

TO_MIMS_SERVER2 = {
    # Column names - raw: [mims_server2]
    "RecNum": ["Rec#"],
    "CycleNumProc": ["Cycle P"],
    "HalfCycleNumCalc": ["Cycle C"],
    "StepNum": ["Step"],
    "DPtTime": ["DPT Time"],
    "TestTime": ["Test Time (s)"],
    "StepTime": ["Step Time (s)"],
    "Capacity": ["Capacity (Ah)"],
    "Energy": ["Energy (Wh)"],
    "Current": ["Current (A)"],
    "Voltage": ["Voltage (V)"],
    "ACZ": ["ACImp (Ohms)"],
    "DCIR": ["DCIR (Ohms)"],
    "MainMode": [],
    "Mode": ["MD"],  # todo: check
    "EndCode": ["ES"],
    "Range": ["I Range"],
    "GlobFlags": [],
    "HasVarData": [],
    "HasGlobFlags": [],
    "HasFRAData": [],
    "DigIO": [],
    "FRAStartTime": [],
    "FRAExpNum": [],
    # missing: EVTemp (C), EVHum (%), Loop1, Loop2, Loop3, Loop4
    # WF Chg Cap, WF Dis Cap, WF Chg E, WF Dis E, Full Step #, S. Capacity (Ah/g)
    # VAR1 - VAR50, GlobFlag1 - GlobFlag64
}
for ii in range(0, 65):
    TO_MIMS_SERVER2[f"VAR{ii}"] = [f"VAR{ii}"]
    TO_MIMS_SERVER2[f"GlobFlag{ii}"] = [f"GlobFlag{ii}"]


# Classes
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

#!/usr/bin/env python
# PurelyPDB - PDB parsing library

from io import BytesIO

from .struct_parser import (
    Container, ListContainer, read_uint32, read_uint16, read_uint8,
    read_bytes, read_cstring, read_guid, enum_value_to_name
)
from .pe import parse_image_section_header

DEBUG_DIRECTORY_TYPES = {
    0: "IMAGE_DEBUG_TYPE_UNKNOWN",
    1: "IMAGE_DEBUG_TYPE_COFF",
    2: "IMAGE_DEBUG_TYPE_CODEVIEW",
    3: "IMAGE_DEBUG_TYPE_FPO",
    4: "IMAGE_DEBUG_TYPE_MISC",
    5: "IMAGE_DEBUG_TYPE_EXCEPTION",
    6: "IMAGE_DEBUG_TYPE_FIXUP",
    7: "IMAGE_DEBUG_TYPE_OMAP_TO_SRC",
    8: "IMAGE_DEBUG_TYPE_OMAP_FROM_SRC",
    9: "IMAGE_DEBUG_TYPE_BORLAND",
    10: "IMAGE_DEBUG_TYPE_RESERVED",
}

DEBUG_MISC_TYPES = {
    1: "IMAGE_DEBUG_MISC_EXENAME",
}


def parse_cv_rsds_header(stream):
    header = Container()
    
    signature = read_bytes(stream, 4)
    if signature != b"RSDS":
        raise ValueError("Invalid CV_RSDS signature")
    
    header.Signature = signature
    header.GUID = read_guid(stream)
    header.Age = read_uint32(stream)
    header.Filename = read_cstring(stream, 'utf-8')
    
    return header


def parse_cv_nb10_header(stream):
    header = Container()
    
    signature = read_bytes(stream, 4)
    if signature != b"NB10":
        raise ValueError("Invalid CV_NB10 signature")
    
    header.Signature = signature
    header.Offset = read_uint32(stream)
    header.Timestamp = read_uint32(stream)
    header.Age = read_uint32(stream)
    header.Filename = read_cstring(stream, 'utf-8')
    
    return header


def parse_image_separate_debug_header(stream):
    header = Container()
    
    signature = read_bytes(stream, 2)
    if signature != b"DI":
        raise ValueError("Invalid IMAGE_SEPARATE_DEBUG_HEADER signature")
    
    header.Signature = signature
    header.Flags = read_uint16(stream)
    header.Machine = read_uint16(stream)
    header.Characteristics = read_uint16(stream)
    header.TimeDateStamp = read_uint16(stream)
    header.CheckSum = read_uint16(stream)
    header.ImageBase = read_uint16(stream)
    header.SizeOfImage = read_uint16(stream)
    header.NumberOfSections = read_uint16(stream)
    header.ExportedNamesSize = read_uint16(stream)
    header.DebugDirectorySize = read_uint16(stream)
    header.SectionAlignment = read_uint16(stream)
    header.Reserved = [read_uint32(stream), read_uint32(stream)]
    
    return header


def parse_image_debug_directory(stream, file_data=None):
    directory = Container()
    
    directory.Characteristics = read_uint32(stream)
    directory.TimeDateStamp = read_uint32(stream)
    directory.MajorVersion = read_uint16(stream)
    directory.MinorVersion = read_uint16(stream)
    
    debug_type = read_uint32(stream)
    directory.Type = enum_value_to_name(debug_type, DEBUG_DIRECTORY_TYPES)
    
    directory.SizeOfData = read_uint32(stream)
    directory.AddressOfRawData = read_uint32(stream)
    directory.PointerToRawData = read_uint32(stream)
    
    if file_data and directory.PointerToRawData < len(file_data):
        directory.Data = file_data[directory.PointerToRawData:directory.PointerToRawData + directory.SizeOfData]
    else:
        directory.Data = None
    
    return directory


def parse_image_debug_misc(stream):
    misc = Container()
    
    misc_type = read_uint32(stream)
    misc.Type = enum_value_to_name(misc_type, DEBUG_MISC_TYPES)
    
    misc.Length = read_uint32(stream)
    misc.Unicode = read_uint8(stream)
    misc.Reserved = [read_uint8(stream) for _ in range(3)]
    
    string_data_len = misc.Length - 12
    string_data = read_bytes(stream, string_data_len)
    
    strings_stream = BytesIO(string_data)
    strings = []
    while strings_stream.tell() < len(string_data):
        try:
            s = read_cstring(strings_stream, 'utf-8')
            if s:
                strings.append(s)
        except:
            break
    misc.Strings = strings
    
    return misc


def parse_image_function_entry(stream):
    entry = Container()
    
    entry.StartingAddress = read_uint32(stream)
    entry.EndingAddress = read_uint32(stream)
    entry.EndOfPrologue = read_uint32(stream)
    
    return entry


class CV_RSDS_HEADER:
    @staticmethod
    def parse(data):
        return parse_cv_rsds_header(BytesIO(data))
    
    @staticmethod
    def parse_stream(stream):
        return parse_cv_rsds_header(stream)


class CV_NB10_HEADER:
    @staticmethod
    def parse(data):
        return parse_cv_nb10_header(BytesIO(data))
    
    @staticmethod
    def parse_stream(stream):
        return parse_cv_nb10_header(stream)

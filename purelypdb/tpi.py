#!/usr/bin/env python
# PurelyPDB - PDB parsing library

from io import BytesIO
import struct

from .struct_parser import (
    Container, ListContainer, read_uint32, read_uint16, read_int16,
    read_int32, read_uint8, read_int8, read_int64, read_uint64,
    read_bytes, read_cstring, read_pascal_string, peek_uint8, align_stream
)

type_refs = {
    "LF_ARGLIST": ["arg_type"],
    "LF_ARRAY": ["element_type", "index_type"],
    "LF_ARRAY_ST": ["element_type", "index_type"],
    "LF_BITFIELD": ["base_type"],
    "LF_CLASS": ["fieldlist", "derived", "vshape"],
    "LF_ENUM": ["utype", "fieldlist"],
    "LF_FIELDLIST": [],
    "LF_MFUNCTION": ["return_type", "class_type", "this_type", "arglist"],
    "LF_MODIFIER": ["modified_type"],
    "LF_POINTER": ["utype"],
    "LF_PROCEDURE": ["return_type", "arglist"],
    "LF_STRUCTURE": ["fieldlist", "derived", "vshape"],
    "LF_STRUCTURE_ST": ["fieldlist", "derived", "vshape"],
    "LF_UNION": ["fieldlist"],
    "LF_UNION_ST": ["fieldlist"],
    "LF_VTSHAPE": [],
    "LF_METHODLIST": [],
}

type_refs_fieldlist = {
    "LF_BCLASS": ["index"],
    "LF_ENUMERATE": [],
    "LF_MEMBER": ["index"],
    "LF_MEMBER_ST": ["index"],
    "LF_METHOD": ["mlist"],
    "LF_NESTTYPE": ["index"],
    "LF_ONEMETHOD": ["index"],
    "LF_VFUNCTAB": ["type"],
}

base_types = {
    "T_NOTYPE": 0x0000,
    "T_VOID": 0x0003,
    "T_CHAR": 0x0010,
    "T_SHORT": 0x0011,
    "T_LONG": 0x0012,
    "T_QUAD": 0x0013,
    "T_UCHAR": 0x0020,
    "T_USHORT": 0x0021,
    "T_ULONG": 0x0022,
    "T_UQUAD": 0x0023,
    "T_REAL32": 0x0040,
    "T_REAL64": 0x0041,
    "T_REAL80": 0x0042,
    "T_INT4": 0x0074,
    "T_UINT4": 0x0075,
    "T_INT8": 0x0076,
    "T_UINT8": 0x0077,
}

leaf_types = {
    0x0001: "LF_MODIFIER_16t",
    0x0002: "LF_POINTER_16t",
    0x0003: "LF_ARRAY_16t",
    0x0004: "LF_CLASS_16t",
    0x0005: "LF_STRUCTURE_16t",
    0x0006: "LF_UNION_16t",
    0x0007: "LF_ENUM_16t",
    0x0008: "LF_PROCEDURE_16t",
    0x0009: "LF_MFUNCTION_16t",
    0x000a: "LF_VTSHAPE",
    0x1001: "LF_MODIFIER",
    0x1002: "LF_POINTER",
    0x1003: "LF_ARRAY_ST",
    0x1004: "LF_CLASS_ST",
    0x1005: "LF_STRUCTURE_ST",
    0x1006: "LF_UNION_ST",
    0x1007: "LF_ENUM_ST",
    0x1008: "LF_PROCEDURE",
    0x1009: "LF_MFUNCTION",
    0x1201: "LF_ARGLIST",
    0x1203: "LF_FIELDLIST",
    0x1204: "LF_DERIVED",
    0x1205: "LF_BITFIELD",
    0x1206: "LF_METHODLIST",
    0x1400: "LF_BCLASS",
    0x1401: "LF_VBCLASS",
    0x1402: "LF_IVBCLASS",
    0x1404: "LF_INDEX",
    0x1405: "LF_MEMBER_ST",
    0x1407: "LF_METHOD_ST",
    0x1408: "LF_NESTTYPE_ST",
    0x1409: "LF_VFUNCTAB",
    0x140a: "LF_FRIENDCLS",
    0x140b: "LF_ONEMETHOD_ST",
    0x1502: "LF_ENUMERATE",
    0x1503: "LF_ARRAY",
    0x1504: "LF_CLASS",
    0x1505: "LF_STRUCTURE",
    0x1506: "LF_UNION",
    0x1507: "LF_ENUM",
    0x150d: "LF_MEMBER",
    0x150e: "LF_STMEMBER",
    0x150f: "LF_METHOD",
    0x1510: "LF_NESTTYPE",
    0x1511: "LF_ONEMETHOD",
    0x8000: "LF_CHAR",
    0x8001: "LF_SHORT",
    0x8002: "LF_USHORT",
    0x8003: "LF_LONG",
    0x8004: "LF_ULONG",
    0x8009: "LF_QUADWORD",
    0x800a: "LF_UQUADWORD",
}


def get_leaf_type_name(value):
    return leaf_types.get(value, value)


def get_base_type_name(value):
    for name, val in base_types.items():
        if val == value:
            return name
    return value


def parse_numeric_leaf(stream):
    leaf_value = read_uint16(stream)
    
    if leaf_value < 0x8000:
        return leaf_value, None
    
    leaf_name = get_leaf_type_name(leaf_value)
    
    if leaf_name == "LF_CHAR":
        value = read_int8(stream)
    elif leaf_name == "LF_SHORT":
        value = read_int16(stream)
    elif leaf_name == "LF_USHORT":
        value = read_uint16(stream)
    elif leaf_name == "LF_LONG":
        value = read_int32(stream)
    elif leaf_name == "LF_ULONG":
        value = read_uint32(stream)
    elif leaf_name == "LF_QUADWORD":
        value = read_int64(stream)
    elif leaf_name == "LF_UQUADWORD":
        value = read_uint64(stream)
    else:
        value = leaf_value
    
    return value, leaf_name


def parse_tpi_header(stream):
    header = Container()
    
    header.version = read_uint32(stream)
    header.hdr_size = read_int32(stream)
    header.ti_min = read_uint32(stream)
    header.ti_max = read_uint32(stream)
    header.follow_size = read_uint32(stream)
    
    # TPIHash
    hash_info = Container()
    hash_info.sn = read_uint16(stream)
    stream.read(2)  # padding
    hash_info.HashKey = read_int32(stream)
    hash_info.Buckets = read_int32(stream)
    
    # OffCb structures
    hash_info.HashVals_off = read_int32(stream)
    hash_info.HashVals_cb = read_int32(stream)
    hash_info.TiOff_off = read_int32(stream)
    hash_info.TiOff_cb = read_int32(stream)
    hash_info.HashAdj_off = read_int32(stream)
    hash_info.HashAdj_cb = read_int32(stream)
    
    header.TPIHash = hash_info
    
    return header


def parse_type_record(stream, length):
    type_data = read_bytes(stream, length)
    type_stream = BytesIO(type_data)
    
    leaf_type_val = read_uint16(type_stream)
    leaf_type = get_leaf_type_name(leaf_type_val)
    
    record = Container()
    record.leaf_type = leaf_type
    record.raw_data = type_data
    
    try:
        if leaf_type == "LF_STRUCTURE" or leaf_type == "LF_CLASS":
            record.count = read_uint16(type_stream)
            prop = read_uint16(type_stream)
            record.fieldlist = read_uint32(type_stream)
            record.derived = read_uint32(type_stream)
            record.vshape = read_uint32(type_stream)
            size_val, _ = parse_numeric_leaf(type_stream)
            record.size = size_val
            record.name = read_cstring(type_stream, 'utf-8')
            
        elif leaf_type == "LF_STRUCTURE_ST":
            record.count = read_uint16(type_stream)
            prop = read_uint16(type_stream)
            record.fieldlist = read_uint32(type_stream)
            record.derived = read_uint32(type_stream)
            record.vshape = read_uint32(type_stream)
            record.size = read_uint16(type_stream)
            record.name = read_pascal_string(type_stream, 'utf-8')
            
        elif leaf_type == "LF_ENUM":
            record.count = read_uint16(type_stream)
            prop = read_uint16(type_stream)
            record.utype = read_uint32(type_stream)
            record.fieldlist = read_uint32(type_stream)
            record.name = read_cstring(type_stream, 'utf-8')
            
        elif leaf_type == "LF_POINTER":
            record.utype = read_uint32(type_stream)
            record.ptr_attr = read_uint32(type_stream)
            
        elif leaf_type == "LF_PROCEDURE":
            record.return_type = read_uint32(type_stream)
            record.call_conv = read_uint8(type_stream)
            record.reserved = read_uint8(type_stream)
            record.parm_count = read_uint16(type_stream)
            record.arglist = read_uint32(type_stream)
            
        elif leaf_type == "LF_ARGLIST":
            record.count = read_uint32(type_stream)
            record.arg_type = []
            for _ in range(record.count):
                record.arg_type.append(read_uint32(type_stream))
                
        elif leaf_type == "LF_FIELDLIST":
            record.substructs = []
            while type_stream.tell() < len(type_data):
                try:
                    substruct = parse_fieldlist_substruct(type_stream)
                    if substruct:
                        record.substructs.append(substruct)
                except:
                    break
                    
    except:
        pass
    
    return record


def parse_fieldlist_substruct(stream):
    try:
        leaf_type_val = read_uint16(stream)
        leaf_type = get_leaf_type_name(leaf_type_val)
        
        substruct = Container()
        substruct.leaf_type = leaf_type
        
        if leaf_type == "LF_MEMBER":
            attr = read_uint16(stream)
            substruct.index = read_uint32(stream)
            offset_val, _ = parse_numeric_leaf(stream)
            substruct.offset = offset_val
            substruct.name = read_cstring(stream, 'utf-8')
            
        elif leaf_type == "LF_MEMBER_ST":
            attr = read_uint16(stream)
            substruct.index = read_uint32(stream)
            substruct.offset = read_uint16(stream)
            substruct.name = read_pascal_string(stream, 'utf-8')
            
        elif leaf_type == "LF_ENUMERATE":
            attr = read_uint16(stream)
            enum_val, _ = parse_numeric_leaf(stream)
            substruct.enum_value = enum_val
            substruct.name = read_cstring(stream, 'utf-8')
            
        elif leaf_type == "LF_NESTTYPE":
            stream.read(2)  # padding
            substruct.index = read_uint32(stream)
            substruct.name = read_cstring(stream, 'utf-8')
            
        elif leaf_type == "LF_METHOD":
            substruct.count = read_uint16(stream)
            substruct.mlist = read_uint32(stream)
            substruct.name = read_cstring(stream, 'utf-8')
        
        pad = peek_uint8(stream)
        if pad >= 0xF0:
            stream.read(pad & 0x0F)
        
        return substruct
    except:
        return None


def parse_stream(fp, unnamed_hack=True, elim_fwdrefs=True):
    header = parse_tpi_header(fp)
    
    types = {}
    for i in range(header.ti_min, header.ti_max):
        try:
            length = read_uint16(fp)
            type_record = parse_type_record(fp, length)
            type_record.tpi_idx = i
            types[i] = type_record
        except:
            break
    
    result = Container()
    result.TPIHeader = header
    result.types = types
    
    if unnamed_hack:
        for i in types:
            if hasattr(types[i], 'name') and types[i].name in ["__unnamed", "<unnamed-tag>", "<anonymous-tag>"]:
                types[i].name = ("__unnamed_%x" % types[i].tpi_idx)
    
    return result


def parse(data, unnamed_hack=True, elim_fwdrefs=True):
    return parse_stream(BytesIO(data), unnamed_hack, elim_fwdrefs)


# PDB built-in type size mapping
# Based on CV type index: https://llvm.org/docs/PDB/TpiStream.html
BUILTIN_TYPE_SIZES = {
    # Special types
    0x0000: 0,    # T_NOTYPE
    0x0003: 0,    # T_VOID
    0x0103: 4,    # T_PVOID (32-bit pointer)
    0x0603: 8,    # T_64PVOID (64-bit pointer)
    
    # Signed integers
    0x0010: 1,    # T_CHAR
    0x0011: 2,    # T_SHORT
    0x0012: 4,    # T_LONG
    0x0013: 8,    # T_QUAD (int64)
    0x0068: 1,    # T_INT1
    0x0072: 2,    # T_INT2
    0x0074: 4,    # T_INT4
    0x0076: 8,    # T_INT8
    
    # Unsigned integers
    0x0020: 1,    # T_UCHAR
    0x0021: 2,    # T_USHORT
    0x0022: 4,    # T_ULONG
    0x0023: 8,    # T_UQUAD (uint64)
    0x0069: 1,    # T_UINT1
    0x0073: 2,    # T_UINT2
    0x0075: 4,    # T_UINT4
    0x0077: 8,    # T_UINT8
    
    # Boolean
    0x0030: 1,    # T_BOOL08
    0x0031: 2,    # T_BOOL16
    0x0032: 4,    # T_BOOL32
    0x0033: 8,    # T_BOOL64
    
    # Real (floating point)
    0x0040: 4,    # T_REAL32
    0x0041: 8,    # T_REAL64
    0x0042: 10,   # T_REAL80
    
    # Wide char
    0x0071: 2,    # T_WCHAR
    0x007A: 1,    # T_CHAR8
    0x007B: 2,    # T_CHAR16
    0x007C: 4,    # T_CHAR32
}


def get_type_size(tpi_types, typind):
    """
    Get the size of a type by its type index.
    
    Args:
        tpi_types: The types dictionary from STREAM_TPI.types
        typind: The type index to look up
        
    Returns:
        The size in bytes, or 0 if unknown
    """
    # Built-in types (typind < 0x1000)
    if typind < 0x1000:
        return BUILTIN_TYPE_SIZES.get(typind, 0)
    
    # Look up in TPI types
    if tpi_types and typind in tpi_types:
        t = tpi_types[typind]
        if hasattr(t, 'size'):
            return t.size
    
    return 0


if __name__ == "__main__":
    import sys
    import time
    
    st = time.time()
    
    with open(sys.argv[1], 'rb') as stream:
        tpi_stream = parse_stream(stream)
    
    ed = time.time()
    print("Parsed %d types in %f seconds" % (len(tpi_stream.types), ed - st))

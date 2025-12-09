# PurelyPDB - PDB parsing library

from io import BytesIO
import struct

from .struct_parser import (
    Container, ListContainer, read_uint32, read_uint16,
    read_bytes, read_cstring, parse_bitfield_uint16
)


def parse_fpo_data(stream):
    entry = Container()
    
    entry.ulOffStart = read_uint32(stream)
    entry.cbProcSize = read_uint32(stream)
    entry.cdwLocals = read_uint32(stream)
    entry.cdwParams = read_uint16(stream)
    
    bit_values = read_uint16(stream)
    # cbProlog: 8 bits (0-7)
    # cbRegs: 3 bits (8-10)
    # fHasSEH: 1 bit (11)
    # fUseBP: 1 bit (12)
    # reserved: 1 bit (13)
    # cbFrame: 2 bits (14-15)
    entry.cbProlog = bit_values & 0xFF
    entry.cbRegs = (bit_values >> 8) & 0x07
    entry.fHasSEH = bool((bit_values >> 11) & 0x01)
    entry.fUseBP = bool((bit_values >> 12) & 0x01)
    entry.reserved = bool((bit_values >> 13) & 0x01)
    entry.cbFrame = (bit_values >> 14) & 0x03
    
    return entry


def parse_fpo_data_v2(stream):
    entry = Container()
    
    entry.ulOffStart = read_uint32(stream)
    entry.cbProcSize = read_uint32(stream)
    entry.cbLocals = read_uint32(stream)
    entry.cbParams = read_uint32(stream)
    entry.maxStack = read_uint32(stream)
    entry.ProgramStringOffset = read_uint32(stream)
    entry.cbProlog = read_uint16(stream)
    entry.cbSavedRegs = read_uint16(stream)
    entry.flags = read_uint32(stream)
    
    return entry


def parse_FPO_DATA_LIST(data):
    stream = BytesIO(data)
    entries = []
    
    while stream.tell() < len(data):
        try:
            entry = parse_fpo_data(stream)
            entries.append(entry)
        except:
            break
    
    return ListContainer(entries)


class FPO_DATA_LIST_V2:
    @staticmethod
    def parse(data):
        stream = BytesIO(data)
        entries = []
        
        while stream.tell() < len(data):
            try:
                entry = parse_fpo_data_v2(stream)
                entries.append(entry)
            except:
                break
        
        return ListContainer(entries)


class FPO_STRING_DATA:
    @staticmethod
    def parse(data):
        stream = BytesIO(data)
        result = Container()
        
        signature = read_bytes(stream, 4)
        if signature != b"\xFE\xEF\xFE\xEF":
            raise ValueError("Invalid FPO_STRING_DATA signature")
        
        result.Signature = signature
        result.Unk1 = read_uint32(stream)
        result.szDataLen = read_uint32(stream)
        
        string_data = read_bytes(stream, result.szDataLen)
        result.StringData = Container(Data=string_data)
        
        result.lastDwIndex = read_uint32(stream)
        unk_data_len = (result.lastDwIndex + 1) * 4
        result.UnkData = read_bytes(stream, unk_data_len)
        
        return result

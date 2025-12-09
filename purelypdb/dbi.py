#!/usr/bin/env python
# PurelyPDB - PDB parsing library

from io import BytesIO
import struct

from .struct_parser import (
    Container, ListContainer, read_uint32, read_uint16, read_int16,
    read_int32, read_bytes, read_cstring, align_stream, enum_value_to_name
)

_ALIGN = 4


MACHINE_TYPES = {
    0x0000: "IMAGE_FILE_MACHINE_UNKNOWN",
    0x014c: "IMAGE_FILE_MACHINE_I386",
    0x0162: "IMAGE_FILE_MACHINE_R3000",
    0x0166: "IMAGE_FILE_MACHINE_R4000",
    0x0168: "IMAGE_FILE_MACHINE_R10000",
    0x0169: "IMAGE_FILE_MACHINE_WCEMIPSV2",
    0x0184: "IMAGE_FILE_MACHINE_ALPHA",
    0x01a2: "IMAGE_FILE_MACHINE_SH3",
    0x01a3: "IMAGE_FILE_MACHINE_SH3DSP",
    0x01a4: "IMAGE_FILE_MACHINE_SH3E",
    0x01a6: "IMAGE_FILE_MACHINE_SH4",
    0x01a8: "IMAGE_FILE_MACHINE_SH5",
    0x01c0: "IMAGE_FILE_MACHINE_ARM",
    0x01c2: "IMAGE_FILE_MACHINE_THUMB",
    0x01c4: "IMAGE_FILE_MACHINE_ARMNT",
    0x01d3: "IMAGE_FILE_MACHINE_AM33",
    0x01f0: "IMAGE_FILE_MACHINE_POWERPC",
    0x01f1: "IMAGE_FILE_MACHINE_POWERPCFP",
    0x0200: "IMAGE_FILE_MACHINE_IA64",
    0x0266: "IMAGE_FILE_MACHINE_MIPS16",
    0x0284: "IMAGE_FILE_MACHINE_ALPHA64",
    0x0366: "IMAGE_FILE_MACHINE_MIPSFPU",
    0x0466: "IMAGE_FILE_MACHINE_MIPSFPU16",
    0x0520: "IMAGE_FILE_MACHINE_TRICORE",
    0x0cef: "IMAGE_FILE_MACHINE_CEF",
    0x0ebc: "IMAGE_FILE_MACHINE_EBC",
    0x8664: "IMAGE_FILE_MACHINE_AMD64",
    0x9041: "IMAGE_FILE_MACHINE_M32R",
    0xc0ee: "IMAGE_FILE_MACHINE_CEE",
}


def parse_symbol_range(stream):
    sr = Container()
    sr.section = read_int16(stream)
    stream.read(2)  # padding
    sr.offset = read_int32(stream)
    sr.size = read_int32(stream)
    sr.flags = read_uint32(stream)
    sr.module = read_int16(stream)
    stream.read(2)  # padding
    sr.dataCRC = read_uint32(stream)
    sr.relocCRC = read_uint32(stream)
    return sr


def parse_dbi_header(stream):
    header = Container()
    
    magic = read_bytes(stream, 4)
    if magic != b"\xFF\xFF\xFF\xFF":
        raise ValueError("Invalid DBI header magic")
    
    header.magic = magic
    header.version = read_uint32(stream)
    header.age = read_uint32(stream)
    header.gssymStream = read_int16(stream)
    header.vers = read_uint16(stream)
    header.pssymStream = read_int16(stream)
    header.pdbver = read_uint16(stream)
    header.symrecStream = read_int16(stream)
    header.pdbver2 = read_uint16(stream)
    header.module_size = read_uint32(stream)
    header.secconSize = read_uint32(stream)
    header.secmapSize = read_uint32(stream)
    header.filinfSize = read_uint32(stream)
    header.tsmapSize = read_uint32(stream)
    header.mfcIndex = read_uint32(stream)
    header.dbghdrSize = read_uint32(stream)
    header.ecinfoSize = read_uint32(stream)
    header.flags = read_uint16(stream)
    
    machine = read_uint16(stream)
    header.Machine = enum_value_to_name(machine, MACHINE_TYPES)
    
    header.resvd = read_uint32(stream)
    
    return header


def parse_dbi_ex_header(stream):
    hdr = Container()
    
    hdr.opened = read_uint32(stream)
    hdr.range = parse_symbol_range(stream)
    hdr.flags = read_uint16(stream)
    hdr.stream = read_int16(stream)
    hdr.symSize = read_uint32(stream)
    hdr.oldLineSize = read_uint32(stream)
    hdr.lineSize = read_uint32(stream)
    hdr.nSrcFiles = read_int16(stream)
    stream.read(2)  # padding
    hdr.offsets = read_uint32(stream)
    hdr.niSource = read_uint32(stream)
    hdr.niCompiler = read_uint32(stream)
    hdr.modName = read_cstring(stream, 'utf-8')
    hdr.objName = read_cstring(stream, 'utf-8')
    
    return hdr


def parse_dbi_dbg_header(stream):
    header = Container()
    
    header.snFPO = read_int16(stream)
    header.snException = read_int16(stream)
    header.snFixup = read_int16(stream)
    header.snOmapToSrc = read_int16(stream)
    header.snOmapFromSrc = read_int16(stream)
    header.snSectionHdr = read_int16(stream)
    header.snTokenRidMap = read_int16(stream)
    header.snXdata = read_int16(stream)
    header.snPdata = read_int16(stream)
    header.snNewFPO = read_int16(stream)
    header.snSectionHdrOrig = read_int16(stream)
    
    return header


def parse_file_index(stream):
    index = Container()
    index.cMod = read_uint16(stream)
    index.cRef = read_uint16(stream)
    return index


class DBIHeader:
    @staticmethod
    def parse_stream(stream):
        return parse_dbi_header(stream)


class DBIExHeader:
    @staticmethod
    def parse(data):
        return parse_dbi_ex_header(BytesIO(data))


class DbiDbgHeader:
    @staticmethod
    def parse_stream(stream):
        return parse_dbi_dbg_header(stream)


class sstFileIndex:
    @staticmethod
    def parse_stream(stream):
        return parse_file_index(stream)


def get_dbi_ex_header_size(header):
    # Fixed fields: opened(4) + range(28) + flags(2) + stream(2) + symSize(4) + 
    #               oldLineSize(4) + lineSize(4) + nSrcFiles(2) + pad(2) + 
    #               offsets(4) + niSource(4) + niCompiler(4) = 64
    size = 4 + 28 + 2 + 2 + 4 + 4 + 4 + 2 + 2 + 4 + 4 + 4
    size += len(header.modName.encode('utf-8')) + 1
    size += len(header.objName.encode('utf-8')) + 1
    return size


def parse_stream(stream):
    pos = 0
    dbihdr = DBIHeader.parse_stream(stream)

    dbiexhdr_data = read_bytes(stream, dbihdr.module_size)

    dbiexhdrs = []
    offset = 0
    while offset < len(dbiexhdr_data):
        ex_stream = BytesIO(dbiexhdr_data[offset:])
        ex_header = parse_dbi_ex_header(ex_stream)
        dbiexhdrs.append(ex_header)

        sz = get_dbi_ex_header_size(ex_header)
        if sz % _ALIGN != 0:
            sz = sz + (_ALIGN - (sz % _ALIGN))
        offset += sz

    # "Section Contribution"
    stream.seek(dbihdr.secconSize, 1)
    # "Section Map"
    stream.seek(dbihdr.secmapSize, 1)
    
    # "File Info"
    end = stream.tell() + dbihdr.filinfSize
    fileIndex = sstFileIndex.parse_stream(stream)

    modStart = []
    for _ in range(fileIndex.cMod):
        modStart.append(read_uint16(stream))

    cRefCnt = []
    for _ in range(fileIndex.cMod):
        cRefCnt.append(read_uint16(stream))

    NameRef = []
    for _ in range(fileIndex.cRef):
        NameRef.append(read_uint32(stream))
    
    modules = []  # array of arrays of files
    files = []  # array of files (non unique)
    Names = stream.read(end - stream.tell())
    
    for i in range(0, fileIndex.cMod):
        these = []
        for j in range(modStart[i], modStart[i] + cRefCnt[i]):
            name_stream = BytesIO(Names[NameRef[j]:])
            Name = read_cstring(name_stream, 'utf-8')
            files.append(Name)
            these.append(Name)
        modules.append(these)

    # "TSM"
    stream.seek(dbihdr.tsmapSize, 1)
    # "EC"
    stream.seek(dbihdr.ecinfoSize, 1)
    # The data we really want
    dbghdr = DbiDbgHeader.parse_stream(stream)

    return Container(
        DBIHeader = dbihdr,
        DBIExHeaders = ListContainer(dbiexhdrs),
        DBIDbgHeader = dbghdr,
        modules = modules,
        files = files)


def parse(data):
    return parse_stream(BytesIO(data))

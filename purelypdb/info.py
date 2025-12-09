# PurelyPDB - PDB parsing library

from io import BytesIO

from .struct_parser import (
    Container, ListContainer, read_uint32, read_uint16, 
    read_bytes, read_cstring, read_guid
)


def parse_string_array(data):
    stream = BytesIO(data)
    names = []
    while stream.tell() < len(data):
        name = read_cstring(stream, 'utf-8')
        if name:
            names.append(name)
    return names


def parse_stream(stream):
    info = Container()
    
    info.Version = read_uint32(stream)
    info.TimeDateStamp = read_uint32(stream)
    info.Age = read_uint32(stream)
    info.GUID = read_guid(stream)
    info.cbNames = read_uint32(stream)
    
    names_data = read_bytes(stream, info.cbNames)
    info.names = parse_string_array(names_data)
    
    return info


def parse(data):
    return parse_stream(BytesIO(data))

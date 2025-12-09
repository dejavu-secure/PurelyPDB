#!/usr/bin/env python

import struct
from io import BytesIO


class Container(dict):
    def __init__(self, **kw):
        dict.__init__(self, kw)
        self.__dict__.update(kw)
    
    def __setattr__(self, name, value):
        self[name] = value
        dict.__setattr__(self, name, value)
    
    def __delattr__(self, name):
        del self[name]
        dict.__delattr__(self, name)


class ListContainer(list):
    pass


def read_cstring(stream, encoding='utf-8'):
    chars = []
    while True:
        b = stream.read(1)
        if not b or b == b'\x00':
            break
        chars.append(b)
    return b''.join(chars).decode(encoding)


def read_pascal_string(stream, encoding='utf-8'):
    length = struct.unpack('<B', stream.read(1))[0]
    if length == 0:
        return ""
    return stream.read(length).decode(encoding)


def read_bytes(stream, count):
    return stream.read(count)


def read_int8(stream):
    return struct.unpack('<b', stream.read(1))[0]


def read_uint8(stream):
    return struct.unpack('<B', stream.read(1))[0]


def read_int16(stream):
    return struct.unpack('<h', stream.read(2))[0]


def read_uint16(stream):
    return struct.unpack('<H', stream.read(2))[0]


def read_int32(stream):
    return struct.unpack('<i', stream.read(4))[0]


def read_uint32(stream):
    return struct.unpack('<I', stream.read(4))[0]


def read_int64(stream):
    return struct.unpack('<q', stream.read(8))[0]


def read_uint64(stream):
    return struct.unpack('<Q', stream.read(8))[0]


def read_float32(stream):
    return struct.unpack('<f', stream.read(4))[0]


def read_float64(stream):
    return struct.unpack('<d', stream.read(8))[0]


def peek_uint8(stream):
    pos = stream.tell()
    val = read_uint8(stream)
    stream.seek(pos)
    return val


def skip_padding(stream, alignment):
    pos = stream.tell()
    remainder = pos % alignment
    if remainder != 0:
        stream.seek(alignment - remainder, 1)


def align_stream(stream, alignment):
    pos = stream.tell()
    remainder = pos % alignment
    if remainder != 0:
        stream.seek(alignment - remainder, 1)


def read_guid(stream):
    data1 = read_uint32(stream)
    data2 = read_uint16(stream)
    data3 = read_uint16(stream)
    data4 = read_bytes(stream, 8)
    
    return Container(
        Data1=data1,
        Data2=data2,
        Data3=data3,
        Data4=data4
    )


def read_padded_string(stream, length, encoding='utf-8'):
    data = stream.read(length)
    end = data.find(b'\x00')
    if end != -1:
        data = data[:end]
    return data.decode(encoding, errors='ignore')


class BitReader:
    def __init__(self, data):
        self.data = data
        self.pos = 0
    
    def read_bits(self, count):
        result = 0
        for i in range(count):
            byte_pos = self.pos // 8
            bit_pos = self.pos % 8
            if byte_pos < len(self.data):
                bit = (self.data[byte_pos] >> bit_pos) & 1
                result |= (bit << i)
            self.pos += 1
        return result
    
    def read_flag(self):
        return self.read_bits(1) != 0


def parse_bitfield_uint16(value, bit_definitions):
    result = Container()
    for name, start_bit, bit_count in bit_definitions:
        mask = (1 << bit_count) - 1
        result[name] = (value >> start_bit) & mask
    return result


def parse_bitfield_uint32(value, bit_definitions):
    result = Container()
    for name, start_bit, bit_count in bit_definitions:
        mask = (1 << bit_count) - 1
        result[name] = (value >> start_bit) & mask
    return result


def enum_value_to_name(val, mapping):
    for name, value in mapping.items():
        if value == val:
            return name
    return val


class EnumType:
    def __init__(self, **kwargs):
        self.mapping = kwargs
        self.reverse_mapping = {v: k for k, v in kwargs.items()}
    
    def encode(self, name):
        return self.mapping.get(name)
    
    def decode(self, value):
        return self.reverse_mapping.get(value, value)

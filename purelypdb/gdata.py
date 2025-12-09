# PurelyPDB - PDB parsing library

from io import BytesIO
from .struct_parser import (
    Container, ListContainer, read_uint16, read_uint32,
    read_cstring, read_pascal_string, read_bytes, read_uint8
)


S_GPROC32 = 0x1110
S_LPROC32 = 0x110F
S_GDATA32 = 0x110D
S_LDATA32 = 0x110C
S_PUB32 = 0x110E
S_GPROC32_ID = 0x1127
S_LPROC32_ID = 0x1128
S_GDATA32_ST = 0x1009
S_LDATA32_ST = 0x1008
S_GPROC32_ST = 0x100A
S_LPROC32_ST = 0x100B

# Reference symbols (used in GSYM for S_GPROC32_ID/S_LPROC32_ID)
S_PROCREF = 0x1125
S_LPROCREF = 0x1126


def parse_gsym_data(stream, leaf_type, data_len=0, is_module_stream=False):
    data = Container()
    
    if leaf_type == S_PUB32:
        data.pubsymflags = read_uint32(stream)
        data.offset = read_uint32(stream)
        data.segment = read_uint16(stream)
        data.name = read_cstring(stream, 'utf-8')
        data.symtype = data.pubsymflags & 0x02
        data.size = 0
    elif leaf_type in (S_GDATA32, S_LDATA32):
        data.symtype = read_uint32(stream)
        data.offset = read_uint32(stream)
        data.segment = read_uint16(stream)
        data.name = read_cstring(stream, 'utf-8')
        data.size = 0
    elif leaf_type in (S_GDATA32_ST, S_LDATA32_ST):
        data.symtype = read_uint32(stream)
        data.offset = read_uint32(stream)
        data.segment = read_uint16(stream)
        data.name = read_pascal_string(stream, 'utf-8')
        data.size = 0
    elif leaf_type in (S_GPROC32_ID, S_LPROC32_ID):
        if is_module_stream:
            # Full format in module streams
            data.pParent = read_uint32(stream)
            data.pEnd = read_uint32(stream)
            data.pNext = read_uint32(stream)
            data.size = read_uint32(stream)
            data.dbgStart = read_uint32(stream)
            data.dbgEnd = read_uint32(stream)
            data.symtype = read_uint32(stream)
            data.offset = read_uint32(stream)
            data.segment = read_uint16(stream)
            data.flags = read_uint8(stream)
            data.name = read_cstring(stream, 'utf-8')
        else:
            # Simplified reference format in GSYM stream
            # Format: typind(4) + offset(4) + segment(2) + name
            data.symtype = read_uint32(stream)
            data.offset = read_uint32(stream)
            data.segment = read_uint16(stream)
            data.name = read_cstring(stream, 'utf-8')
            data.size = 0
    elif leaf_type in (S_GPROC32, S_LPROC32):
        data.pParent = read_uint32(stream)
        data.pEnd = read_uint32(stream)
        data.pNext = read_uint32(stream)
        data.size = read_uint32(stream)
        data.dbgStart = read_uint32(stream)
        data.dbgEnd = read_uint32(stream)
        data.symtype = read_uint32(stream)
        data.offset = read_uint32(stream)
        data.segment = read_uint16(stream)
        data.flags = read_uint8(stream)
        data.name = read_cstring(stream, 'utf-8')
    elif leaf_type in (S_GPROC32_ST, S_LPROC32_ST):
        data.pParent = read_uint32(stream)
        data.pEnd = read_uint32(stream)
        data.pNext = read_uint32(stream)
        data.size = read_uint32(stream)
        data.dbgStart = read_uint32(stream)
        data.dbgEnd = read_uint32(stream)
        data.symtype = read_uint32(stream)
        data.offset = read_uint32(stream)
        data.segment = read_uint16(stream)
        data.flags = read_uint8(stream)
        data.name = read_pascal_string(stream, 'utf-8')
    else:
        data = None
    
    return data


def parse_global_symbol(stream, is_module_stream=False):
    length = read_uint16(stream)
    symbol_data = read_bytes(stream, length)
    
    sym_stream = BytesIO(symbol_data)
    leaf_type = read_uint16(sym_stream)
    data = parse_gsym_data(sym_stream, leaf_type, length - 2, is_module_stream)
    
    return Container(
        length=length,
        leaf_type=leaf_type,
        data=data
    )


def parse(data, is_module_stream=False):
    return parse_stream(BytesIO(data), is_module_stream)


def parse_stream(stream, is_module_stream=False):
    symbols = []
    
    while True:
        try:
            if hasattr(stream, 'read'):
                pos = stream.tell()
                test = stream.read(2)
                if len(test) < 2:
                    break
                stream.seek(pos)
            else:
                break
            
            symbol = parse_global_symbol(stream, is_module_stream)
            symbols.append(symbol)
        except:
            break
    
    return merge_structures(symbols)


def merge_structures(symbols):
    new_cons = []
    for sym in symbols:
        sym_dict = {'length': sym.length, 'leaf_type': sym.leaf_type}
        if sym.data:
            sym_dict.update({
                'symtype': getattr(sym.data, 'symtype', 0),
                'offset': sym.data.offset,
                'segment': sym.data.segment,
                'name': sym.data.name,
                'size': getattr(sym.data, 'size', 0)
            })
        new_cons.append(Container(**sym_dict))
    return ListContainer(new_cons)

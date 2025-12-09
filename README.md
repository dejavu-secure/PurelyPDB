# PurelyPDB

Cross-platform Python parser for Microsoft PDB files with no external dependencies.

Based on [pdbparse](https://github.com/moyix/pdbparse) with modifications and additional code.

Provides more complete parsing support, primarily supporting 3.7-latest, with secondary support for 2.7+.

## Features

- Parse PDB files without external dependencies
- Extract function symbols with addresses and sizes
- Extract global variables with types and sizes
- Extract segment/section information
- Support for both PDB 2.0 and PDB 7.0 formats

## Installation

```bash
pip install purelypdb
```

Or install from source:

```bash
pip install -e .
```

## Usage

```python
from purelypdb import parse, get_type_size

# Parse a PDB file
pdb = parse("example.pdb")

# Access global symbols
for sym in pdb.STREAM_GSYM.globals:
    print(sym.name, sym.offset)

# Access section headers
for sec in pdb.STREAM_SECT_HDR.sections:
    print(sec.Name, sec.VirtualAddress)

# Get type size
size = get_type_size(pdb.STREAM_TPI.types, typind)
```

## API

| Function | Parameters | Returns | Description |
|----------|-----------|---------|-------------|
| `parse(filename, fast_load=False)` | `filename`: PDB file path<br>`fast_load`: Skip some streams | PDB object | Parse PDB file (auto-detect version) |
| `get_type_size(tpi_types, typind)` | `tpi_types`: Types from STREAM_TPI<br>`typind`: Type index | int | Get type size in bytes |

### PDB Object Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `STREAM_GSYM` | Stream | Global symbols |
| `STREAM_GSYM.globals` | List | List of symbol objects |
| `STREAM_SECT_HDR` | Stream | Section headers |
| `STREAM_SECT_HDR.sections` | List | List of section objects |
| `STREAM_TPI` | Stream | Type information |
| `STREAM_TPI.types` | Dict | Type index to type mapping |

## Symbol Types

| Type | Value | Description |
|------|-------|-------------|
| S_PUB32 | 0x110E | Public symbol |
| S_GDATA32 | 0x110D | Global data |
| S_LDATA32 | 0x110C | Local (file static) data |
| S_GPROC32 | 0x1110 | Global procedure |
| S_LPROC32 | 0x110F | Local procedure |
| S_GPROC32_ID | 0x1127 | Global procedure (ID version) |
| S_LPROC32_ID | 0x1128 | Local procedure (ID version) |
| S_GDATA32_ST | 0x1009 | Global data (ST version) |
| S_LDATA32_ST | 0x1008 | Local data (ST version) |
| S_GPROC32_ST | 0x100A | Global procedure (ST version) |
| S_LPROC32_ST | 0x100B | Local procedure (ST version) |
| S_PROCREF | 0x1125 | Procedure reference |
| S_LPROCREF | 0x1126 | Local procedure reference |

## License

GPL v2
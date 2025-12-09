# PurelyPDB

A pure Python library for parsing Microsoft PDB (Program Database) files.

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

## Quick Start

### Parse Functions

```python
from purelypdb import parse

pdb = parse("example.pdb")

# Get section headers for address calculation
sections = pdb.STREAM_SECT_HDR.sections if hasattr(pdb, 'STREAM_SECT_HDR') else []

# Get function sizes
func_sizes = pdb.STREAM_GSYM.func_sizes if hasattr(pdb, 'STREAM_GSYM') else {}

# Iterate over global symbols
for sym in pdb.STREAM_GSYM.globals:
    # Check if it's a function (S_PUB32 with function flag)
    if sym.leaf_type == 0x110E and (sym.symtype & 0x02):
        seg = sym.segment
        off = sym.offset
        
        # Calculate virtual address
        if sections and 0 < seg <= len(sections):
            va = sections[seg-1].VirtualAddress + off
        else:
            va = off
        
        # Get function size
        size = func_sizes.get((seg, off), 0)
        
        print(f"{sym.name} VA=0x{va:08X} Size={size}")
```

### Parse Variables

```python
from purelypdb import parse

pdb = parse("example.pdb")

# Data symbol types
S_GDATA32 = 0x110D
S_LDATA32 = 0x110C

for sym in pdb.STREAM_GSYM.globals:
    if sym.leaf_type in (S_GDATA32, S_LDATA32):
        # Get type size from TPI stream
        typind = sym.symtype
        size = 0
        
        if hasattr(pdb, 'STREAM_TPI') and typind in pdb.STREAM_TPI.types:
            t = pdb.STREAM_TPI.types[typind]
            size = getattr(t, 'size', 0)
        
        print(f"{sym.name} typind=0x{typind:X} Size={size}")
```

### Parse Segments

```python
from purelypdb import parse

pdb = parse("example.pdb")

if hasattr(pdb, 'STREAM_SECT_HDR'):
    for i, sec in enumerate(pdb.STREAM_SECT_HDR.sections):
        print(f"Section {i+1}: {sec.Name}")
        print(f"  VirtualAddress: 0x{sec.VirtualAddress:08X}")
        print(f"  VirtualSize: 0x{sec.VirtualSize:08X}")
        print(f"  PointerToRawData: 0x{sec.PointerToRawData:08X}")
```

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

## License

MIT License

#!/usr/bin/env python
"""
Example: Parse functions from a PDB file.

Usage:
    python parse_functions.py <pdb_file>
"""
import sys
import os

from purelypdb import parse

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_functions.py <pdb_file>")
        sys.exit(1)
    
    pdb_file = sys.argv[1]
    if not os.path.exists(pdb_file):
        print(f"Error: File not found - {pdb_file}")
        sys.exit(1)
    
    pdb = parse(pdb_file)
    
    sections = []
    if hasattr(pdb, 'STREAM_SECT_HDR'):
        sections = pdb.STREAM_SECT_HDR.sections
    
    # Get function sizes from DBI module streams
    func_sizes = {}
    if hasattr(pdb, 'STREAM_GSYM'):
        func_sizes = getattr(pdb.STREAM_GSYM, 'func_sizes', {})
    
    # Symbol types
    S_PUB32 = 0x110E
    
    if hasattr(pdb, 'STREAM_GSYM') and pdb.STREAM_GSYM.size > 0:
        for sym in pdb.STREAM_GSYM.globals:
            if not hasattr(sym, 'name') or not hasattr(sym, 'offset'):
                continue
            
            leaf_type = getattr(sym, 'leaf_type', 0)
            
            # Only process S_PUB32 function symbols (pubsymflags & 0x02 means function)
            if leaf_type != S_PUB32:
                continue
            
            symtype = getattr(sym, 'symtype', 0)
            if (symtype & 0x02) == 0:
                continue
            
            seg = getattr(sym, 'segment', 0)
            off = sym.offset
            rva = off
            file_addr = off
            if sections and 0 < seg <= len(sections):
                sec = sections[seg-1]
                rva = sec.VirtualAddress + off
                file_addr = sec.PointerToRawData + off
            
            # Get size from func_sizes
            size = func_sizes.get((seg, off), 0)
            
            print(f"{sym.name} VA=0x{rva:08X} FileAddr=0x{file_addr:08X} Size={size}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

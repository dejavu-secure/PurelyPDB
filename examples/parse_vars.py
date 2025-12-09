#!/usr/bin/env python
"""
Example: Parse global variables from a PDB file.

Usage:
    python parse_vars.py <pdb_file>
"""
import sys
import os

from purelypdb import parse, get_type_size

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_vars.py <pdb_file>")
        sys.exit(1)
    
    pdb_file = sys.argv[1]
    if not os.path.exists(pdb_file):
        print(f"Error: File not found - {pdb_file}")
        sys.exit(1)
    
    pdb = parse(pdb_file)
    
    sections = []
    if hasattr(pdb, 'STREAM_SECT_HDR'):
        sections = pdb.STREAM_SECT_HDR.sections
    
    if hasattr(pdb, 'STREAM_GSYM') and pdb.STREAM_GSYM.size > 0:
        # Get TPI types for size lookup
        tpi_types = None
        if hasattr(pdb, 'STREAM_TPI') and hasattr(pdb.STREAM_TPI, 'types'):
            tpi_types = pdb.STREAM_TPI.types
        
        for sym in pdb.STREAM_GSYM.globals:
            leaf_type = getattr(sym, 'leaf_type', 0)
            
            # S_GDATA32 (0x110D) and S_LDATA32 (0x110C) - have type info
            if leaf_type in (0x110D, 0x110C):
                if hasattr(sym, 'symtype') and hasattr(sym, 'offset'):
                    typind = sym.symtype
                    seg = getattr(sym, 'segment', 0)
                    off = sym.offset
                    rva = off
                    file_addr = off
                    if sections and 0 < seg <= len(sections):
                        sec = sections[seg-1]
                        rva = sec.VirtualAddress + off
                        file_addr = sec.PointerToRawData + off
                    
                    size = get_type_size(tpi_types, typind)
                    print(f"{sym.name} VA=0x{rva:08X} FileAddr=0x{file_addr:08X} Size={size}")
            
            # S_PUB32 (0x110E) - public symbols, check if it's data (not function)
            elif leaf_type == 0x110E:
                # symtype is pubsymflags for S_PUB32: bit 1 (0x02) = function
                pubsymflags = getattr(sym, 'symtype', 0)
                if pubsymflags & 0x02:  # Skip functions
                    continue
                
                seg = getattr(sym, 'segment', 0)
                off = getattr(sym, 'offset', 0)
                rva = off
                file_addr = off
                if sections and 0 < seg <= len(sections):
                    sec = sections[seg-1]
                    rva = sec.VirtualAddress + off
                    file_addr = sec.PointerToRawData + off
                
                # Try to get type from module symbols (typind attribute added by library)
                typind = getattr(sym, 'typind', None)
                if typind is not None:
                    size = get_type_size(tpi_types, typind)
                    print(f"{sym.name} VA=0x{rva:08X} FileAddr=0x{file_addr:08X} Size={size}")
                else:
                    print(f"{sym.name} VA=0x{rva:08X} FileAddr=0x{file_addr:08X} Size=?")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

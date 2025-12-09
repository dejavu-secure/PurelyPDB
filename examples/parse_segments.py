#!/usr/bin/env python
"""
Example: Parse section headers from a PDB file.

Usage:
    python parse_segments.py <pdb_file>
"""
import sys
import os

from purelypdb import parse

def main():
    if len(sys.argv) < 2:
        print("Usage: python parse_segments.py <pdb_file>")
        sys.exit(1)
    
    pdb_file = sys.argv[1]
    if not os.path.exists(pdb_file):
        print(f"Error: File not found - {pdb_file}")
        sys.exit(1)
    
    pdb = parse(pdb_file)
    
    if hasattr(pdb, 'STREAM_SECT_HDR'):
        sections = pdb.STREAM_SECT_HDR.sections
        for s in sections:
            print(f"{s.Name} VA=0x{s.VirtualAddress:08X} FileAddr=0x{s.PointerToRawData:08X} Size=0x{s.VirtualSize:08X}")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

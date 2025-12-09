#!/usr/bin/env python
# PurelyPDB - PDB parsing library

from io import BytesIO

from .struct_parser import (
    Container, ListContainer, read_padded_string,
    read_uint32, read_uint16
)


def parse_image_section_header(stream):
    section = Container()
    
    section.Name = read_padded_string(stream, 8, 'utf-8')
    section.VirtualSize = read_uint32(stream)
    section.PhysicalAddress = section.VirtualSize
    section.VirtualAddress = read_uint32(stream)
    section.SizeOfRawData = read_uint32(stream)
    section.PointerToRawData = read_uint32(stream)
    section.PointerToRelocations = read_uint32(stream)
    section.PointerToLinenumbers = read_uint32(stream)
    section.NumberOfRelocations = read_uint16(stream)
    section.NumberOfLinenumbers = read_uint16(stream)
    section.Characteristics = read_uint32(stream)
    
    return section


class Sections:
    @staticmethod
    def parse(data):
        stream = BytesIO(data)
        sections = []
        while stream.tell() < len(data):
            try:
                section = parse_image_section_header(stream)
                sections.append(section)
            except:
                break
        return ListContainer(sections)

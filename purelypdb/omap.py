#!/usr/bin/env python
# PurelyPDB - PDB parsing library

from io import BytesIO
from bisect import bisect

from .struct_parser import Container, ListContainer, read_uint32


def parse_omap_entry(stream):
    entry = Container()
    entry.From = read_uint32(stream)
    entry.To = read_uint32(stream)
    return entry


def parse_omap_entries(data):
    stream = BytesIO(data)
    entries = []
    while stream.tell() < len(data):
        try:
            entry = parse_omap_entry(stream)
            entries.append(entry)
        except:
            break
    return ListContainer(entries)


class Omap(object):

    def __init__(self, omapstream):
        if isinstance(omapstream, bytes):
            self.omap = parse_omap_entries(omapstream)
        else:
            data = omapstream.read() if hasattr(omapstream, 'read') else omapstream
            self.omap = parse_omap_entries(data)

        self._froms = None

    def remap(self, address):
        if not self._froms:
            self._froms = [o.From for o in self.omap]

        pos = bisect(self._froms, address)
        if self._froms[pos] != address:
            pos = pos - 1

        if self.omap[pos].To == 0:
            return self.omap[pos].To
        else:
            return self.omap[pos].To + (address - self.omap[pos].From)

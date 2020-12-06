#!/usr/bin/env python3

############################################################################
#                                                                          #
#  PyTCP - Python TCP/IP stack                                             #
#  Copyright (C) 2020  Sebastian Majewski                                  #
#                                                                          #
#  This program is free software: you can redistribute it and/or modify    #
#  it under the terms of the GNU General Public License as published by    #
#  the Free Software Foundation, either version 3 of the License, or       #
#  (at your option) any later version.                                     #
#                                                                          #
#  This program is distributed in the hope that it will be useful,         #
#  but WITHOUT ANY WARRANTY; without even the implied warranty of          #
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the           #
#  GNU General Public License for more details.                            #
#                                                                          #
#  You should have received a copy of the GNU General Public License       #
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.  #
#                                                                          #
#  Author's email: ccie18643@gmail.com                                     #
#  Github repository: https://github.com/ccie18643/PyTCP                   #
#                                                                          #
############################################################################

##############################################################################################
#                                                                                            #
#  This program is a work in progress and it changes on daily basis due to new features      #
#  being implemented, changes being made to already implemented features, bug fixes, etc.    #
#  Therefore if the current version is not working as expected try to clone it again the     #
#  next day or shoot me an email describing the problem. Any input is appreciated. Also      #
#  keep in mind that some features may be implemented only partially (as needed for stack    #
#  operation) or they may be implemented in sub-optimal or not 100% RFC compliant way (due   #
#  to lack of time) or last but not least they may contain bug(s) that i didn't notice yet.  #
#                                                                                            #
##############################################################################################


#
# fpp_udp.py - Fast Packet Parser class for UDP protocol
#


import struct

import config
from ip_helper import inet_cksum

# UDP packet header (RFC 768)

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |          Source port          |        Destination port       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |         Packet length         |            Checksum           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


UDP_HEADER_LEN = 8


class UdpPacket:
    """ UDP packet support class """

    def __init__(self, frame, hptr, pseudo_header):
        """ Class constructor """

        self._frame = frame
        self._hptr = hptr

        self.packet_parse_failed = self._packet_integrity_check(pseudo_header) or self._packet_sanity_check()
        if self.packet_parse_failed:
            return

        self.dptr = self._hptr + UDP_HEADER_LEN

    def __str__(self):
        """ Packet log string """

        return f"UDP {self.sport} > {self.dport}, len {self.plen}"

    def __len__(self):
        """ Packet length """

        return len(self._frame) - self._hptr

    @property
    def sport(self):
        """ Read 'Source port' field """

        if not hasattr(self, "_sport"):
            self._sport = struct.unpack("!H", self._frame[self._hptr + 0 : self._hptr + 2])[0]
        return self._sport

    @property
    def dport(self):
        """ Read 'Destianation port' field """

        if not hasattr(self, "_dport"):
            self._dport = struct.unpack("!H", self._frame[self._hptr + 2 : self._hptr + 4])[0]
        return self._dport

    @property
    def plen(self):
        """ Read 'Packet length' field """

        if not hasattr(self, "_plen"):
            self._plen = struct.unpack("!H", self._frame[self._hptr + 4 : self._hptr + 6])[0]
        return self._plen

    @property
    def cksum(self):
        """ Read 'Checksum' field """

        if not hasattr(self, "_cksum"):
            self._cksum = struct.unpack("!H", self._frame[self._hptr + 6 : self._hptr + 8])[0]
        return self._cksum

    @property
    def data(self):
        """ Read the data packet carries """

        if not hasattr(self, "_data"):
            self._data = self._frame[self._hptr + UDP_HEADER_LEN :]
        return self._data

    @property
    def packet(self):
        """ Read the whole packet """

        if not hasattr(self, "_packet"):
            self._packet = self._frame[self._hptr :]
        return self._packet

    def _packet_integrity_check(self, pseudo_header):
        """ Packet integrity check to be run on raw frame prior to parsing to make sure parsing is safe """

        if not config.packet_integrity_check:
            return False

        if inet_cksum(pseudo_header + self._frame[self._hptr :]):
            return "UDP sanity - wrong packet checksum"

        if len(self._frame) < UDP_HEADER_LEN:
            return "UDP sanity - wrong packet length (I)"

        plen = struct.unpack("!H", self._frame[self._hptr + 4 : self._hptr + 6])[0]
        if not 8 <= plen == len(self._frame) - self._hptr:
            return "UDP sanity - wrong packet length (II)"

        return False

    def _packet_sanity_check(self):
        """ Packet sanity check to be run on parsed packet to make sure frame's fields contain sane values """

        if not config.packet_sanity_check:
            return False

        if self.sport == 0:
            return "UDP sanity fail - 'udp_sport' must be greater than 0"

        if self.dport == 0:
            return "UDP sanity fail - 'udp_dport' must be greater then 0"

        return False

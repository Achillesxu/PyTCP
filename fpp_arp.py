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
# fpp_arp.py - Fast Packet Parser class for ARP protocol
#


import struct

import config
from ipv4_address import IPv4Address

# ARP packet header - IPv4 stack version only

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |         Hardware type         |         Protocol type         |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |  Hard length  |  Proto length |           Operation           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               >
# +        Sender MAC address     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# >                               |       Sender IP address       >
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# >                               |                               >
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+       Target MAC address      |
# >                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                       Target IP address                       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


ARP_HEADER_LEN = 28

ARP_OP_REQUEST = 1
ARP_OP_REPLY = 2


class ArpPacket:
    """ ARP packet support class """

    def __init__(self, frame, hptr):
        """ Class constructor """

        self._frame = frame
        self._hptr = hptr

        self.packet_parse_failed = self._packet_integrity_check() or self._packet_sanity_check()

    def __str__(self):
        """ Packet log string """

        if self.oper == ARP_OP_REQUEST:
            return f"ARP request {self.spa} / {self.sha} > {self.tpa} / {self.tha}"
        if self.oper == ARP_OP_REPLY:
            return f"ARP reply {self.spa} / {self.sha} > {self.tpa} / {self.tha}"
        return f"ARP unknown operation {self.oper}"

    def __len__(self):
        """ Packet length """

        return len(self._frame) - self._hptr

    @property
    def hrtype(self):
        """ Read 'Hardware address type' field """

        if not hasattr(self, "_hrtype"):
            self._hrtype = struct.unpack("!H", self._frame[self._hptr + 0 : self._hptr + 2])[0]
        return self._hrtype

    @property
    def prtype(self):
        """ Read 'Protocol address type' field """

        if not hasattr(self, "_prtype"):
            self._prtype = struct.unpack("!H", self._frame[self._hptr + 2 : self._hptr + 4])[0]
        return self._prtype

    @property
    def hrlen(self):
        """ Read 'Hardware address length' field """

        return self._frame[self._hptr + 4]

    @property
    def prlen(self):
        """ Read 'Protocol address length' field """

        return self._frame[self._hptr + 5]

    @property
    def oper(self):
        """ Read 'Operation' field """

        if not hasattr(self, "_oper"):
            self._oper = struct.unpack("!H", self._frame[self._hptr + 6 : self._hptr + 8])[0]
        return self._oper

    @property
    def sha(self):
        """ Read 'Sender hardware address' field """

        if not hasattr(self, "_sha"):
            self._sha = ":".join([f"{_:0>2x}" for _ in self._frame[self._hptr + 8 : self._hptr + 14]])
        return self._sha

    @property
    def spa(self):
        """ Read 'Sender protocol address' field """

        if not hasattr(self, "_spa"):
            self._spa = IPv4Address(self._frame[self._hptr + 14 : self._hptr + 18])
        return self._spa

    @property
    def tha(self):
        """ Read 'Target hardware address' field """

        if not hasattr(self, "_tha"):
            self._tha = ":".join([f"{_:0>2x}" for _ in self._frame[self._hptr + 18 : self._hptr + 24]])
        return self._tha

    @property
    def tpa(self):
        """ Read 'Target protocol address' field """

        if not hasattr(self, "_tpa"):
            self._tpa = IPv4Address(self._frame[self._hptr + 24 : self._hptr + 28])
        return self._tpa

    @property
    def packet(self):
        """ Read the whole packet """

        if not hasattr(self, "_packet"):
            self._packet = self._frame[self._hptr :]
        return self._packet

    def _packet_integrity_check(self):
        """ Packet integrity check to be run on raw packet prior to parsing to make sure parsing is safe """

        if not config.packet_integrity_check:
            return False

        if len(self) < ARP_HEADER_LEN:
            return "ARP integrity - wrong packet length (I)"

        return False

    def _packet_sanity_check(self):
        """ Packet sanity check to be run on parsed packet to make sure packet's fields contain sane values """

        if not config.packet_sanity_check:
            return False

        if not self.hrtype == 1:
            return "ARP sanity - 'arp_hrtype' must be 1"

        if not self.prtype == 0x0800:
            return "ARP sanity - 'arp_prtype' must be 0x0800"

        if not self.hrlen == 6:
            return "ARP sanity - 'arp_hrlen' must be 6"

        if not self.prlen == 4:
            return "ARP sanity - 'arp_prlen' must be 4"

        if self.oper not in {1, 2}:
            return "ARP sanity - 'oper' must be [1-2]"

        return False

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
# ps_arp.py - protocol support library for ARP
#


import struct

import loguru

import config
from ipv4_address import IPv4Address
from tracker import Tracker

# ARP packet header - IPv4 stack version only

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |         Hardware Type         |         Protocol Type         |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |  Hard Length  |  Proto Length |           Operation           |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                                                               >
# +        Sender Mac Address     +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# >                               |       Sender IP Address       >
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# >                               |                               >
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+       Target MAC Address      |
# >                                                               |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                       Target IP Address                       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


ARP_HEADER_LEN = 28

ARP_OP_REQUEST = 1
ARP_OP_REPLY = 2


class ArpPacket:
    """ ARP packet support class """

    protocol = "ARP"

    def __init__(self, arp_sha=None, arp_spa=None, arp_tpa=None, arp_tha="00:00:00:00:00:00", arp_oper=ARP_OP_REQUEST, echo_tracker=None):
        """ Class constructor """

        self.tracker = Tracker("TX", echo_tracker)

        self.arp_hrtype = 1
        self.arp_prtype = 0x0800
        self.arp_hrlen = 6
        self.arp_prlen = 4
        self.arp_oper = arp_oper
        self.arp_sha = arp_sha
        self.arp_spa = IPv4Address(arp_spa)
        self.arp_tha = arp_tha
        self.arp_tpa = IPv4Address(arp_tpa)

    def __str__(self):
        """ Short packet log string """

        if self.arp_oper == ARP_OP_REQUEST:
            return f"ARP request {self.arp_spa} / {self.arp_sha} > {self.arp_tpa} / {self.arp_tha}"
        if self.arp_oper == ARP_OP_REPLY:
            return f"ARP reply {self.arp_spa} / {self.arp_sha} > {self.arp_tpa} / {self.arp_tha}"
        return f"ARP unknown operation {self.arp_oper}"

    def __len__(self):
        """ Length of the packet """

        return len(self.raw_packet)

    @property
    def raw_header(self):
        """ Packet header in raw format """

        return struct.pack(
            "!HH BBH 6s 4s 6s 4s",
            self.arp_hrtype,
            self.arp_prtype,
            self.arp_hrlen,
            self.arp_prlen,
            self.arp_oper,
            bytes.fromhex(self.arp_sha.replace(":", "")),
            IPv4Address(self.arp_spa).packed,
            bytes.fromhex(self.arp_tha.replace(":", "")),
            IPv4Address(self.arp_tpa).packed,
        )

    @property
    def raw_packet(self):
        """ Get packet in raw format """

        return self.raw_header

    def get_raw_packet(self):
        """ Get packet in raw format ready to be processed by lower level protocol """

        return self.raw_packet


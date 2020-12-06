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
# fpp_ip4.py - Fast Packet Parser support class for IPv4 protocol
#


import struct

import config
from ip_helper import inet_cksum
from ipv4_address import IPv4Address

# IPv4 protocol header

# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |Version|  IHL  |   DSCP    |ECN|          Packet length        |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |         Identification        |Flags|      Fragment offset    |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |  Time to live |    Protocol   |         Header checksum       |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                       Source address                          |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# |                    Destination address                        |
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
# ~                    Options                    ~    Padding    ~
# +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


IP4_HEADER_LEN = 20

IP4_PROTO_ICMP4 = 1
IP4_PROTO_TCP = 6
IP4_PROTO_UDP = 17


IP4_PROTO_TABLE = {IP4_PROTO_ICMP4: "ICMPv4", IP4_PROTO_TCP: "TCP", IP4_PROTO_UDP: "UDP"}


DSCP_CS0 = 0b000000
DSCP_CS1 = 0b001000
DSCP_AF11 = 0b001010
DSCP_AF12 = 0b001100
DSCP_AF13 = 0b001110
DSCP_CS2 = 0b010000
DSCP_AF21 = 0b010010
DSCP_AF22 = 0b010100
DSCP_AF23 = 0b010110
DSCP_CS3 = 0b011000
DSCP_AF31 = 0b011010
DSCP_AF32 = 0b011100
DSCP_AF33 = 0b011110
DSCP_CS4 = 0b100000
DSCP_AF41 = 0b100010
DSCP_AF42 = 0b100100
DSCP_AF43 = 0b100110
DSCP_CS5 = 0b101000
DSCP_EF = 0b101110
DSCP_CS6 = 0b110000
DSCP_CS7 = 0b111000

DSCP_TABLE = {
    DSCP_CS0: "CS0",
    DSCP_CS1: "CS1",
    DSCP_AF11: "AF11",
    DSCP_AF12: "AF12",
    DSCP_AF13: "AF13",
    DSCP_CS2: "CS2",
    DSCP_AF21: "AF21",
    DSCP_AF22: "AF22",
    DSCP_AF23: "AF23",
    DSCP_CS3: "CS3",
    DSCP_AF31: "AF31",
    DSCP_AF32: "AF32",
    DSCP_AF33: "AF33",
    DSCP_CS4: "CS4",
    DSCP_AF41: "AF41",
    DSCP_AF42: "AF42",
    DSCP_AF43: "AF43",
    DSCP_CS5: "CS5",
    DSCP_EF: "EF",
    DSCP_CS6: "CS6",
    DSCP_CS7: "CS7",
}

ECN_TABLE = {0b00: "Non-ECT", 0b10: "ECT(0)", 0b01: "ECT(1)", 0b11: "CE"}


class Ip4Packet:
    """ IPv4 packet support class """

    def __init__(self, frame, hptr):
        """ Class constructor """

        self._frame = frame
        self._hptr = hptr

        self.packet_parse_failed = self._packet_integrity_check() or self._packet_sanity_check()
        if self.packet_parse_failed:
            return

        self.dptr = self._hptr + self.hlen

    def __str__(self):
        """ Short packet log string """

        return (
            f"IPv4 {self.src} > {self.dst}, proto {self.proto} ({IP4_PROTO_TABLE.get(self.proto, '???')}), id {self.id}"
            + f"{', DF' if self.flag_df else ''}{', MF' if self.flag_mf else ''}, offset {self.offset}, plen {self.plen}"
            + f", ttl {self.ttl}"
        )

    def __len__(self):
        """ Packet length """

        return len(self._frame) - self._hptr

    @property
    def ver(self):
        """ Read 'Version' field """

        if not hasattr(self, "_ver"):
            self._ver = self._frame[self._hptr + 0] >> 4
        return self._ver

    @property
    def hlen(self):
        """ Read 'Header length' field """

        if not hasattr(self, "_hlen"):
            self._hlen = (self._frame[self._hptr + 0] & 0b00001111) << 2
        return self._hlen

    @property
    def dscp(self):
        """ Read 'DSCP' field """

        if not hasattr(self, "_dscp"):
            self._dscp = (self._frame[self._hptr + 1] & 0b11111100) >> 2
        return self._dscp

    @property
    def ecn(self):
        """ Read 'ECN' field """

        if not hasattr(self, "_ecn"):
            self._ecn = self._frame[self._hptr + 1] & 0b00000011
        return self._ecn

    @property
    def plen(self):
        """ Read 'Packet length' field """

        if not hasattr(self, "_plen"):
            self._plen = struct.unpack("!H", self._frame[self._hptr + 2 : self._hptr + 4])[0]
        return self._plen

    @property
    def id(self):
        """ Read 'Identification' field """

        if not hasattr(self, "_id"):
            self._id = struct.unpack("!H", self._frame[self._hptr + 4 : self._hptr + 6])[0]
        return self._id

    @property
    def flag_df(self):
        """ Read 'DF flag' field """

        if not hasattr(self, "_flag_df"):
            self._flag_df = bool(struct.unpack("!H", self._frame[self._hptr + 6 : self._hptr + 8])[0] & 0b0100000000000000)
        return self._flag_df

    @property
    def flag_mf(self):
        """ Read 'MF flag' field """

        if not hasattr(self, "_flag_mf"):
            self._flag_mf = bool(struct.unpack("!H", self._frame[self._hptr + 6 : self._hptr + 8])[0] & 0b0010000000000000)
        return self._flag_mf

    @property
    def offset(self):
        """ Read 'Fragment offset' field """

        if not hasattr(self, "_offset"):
            self._offset = (struct.unpack("!H", self._frame[self._hptr + 6 : self._hptr + 8])[0] & 0b0001111111111111) << 3
        return self._offset

    @property
    def ttl(self):
        """ Read 'TTL' field """

        return self._frame[self._hptr + 8]

    @property
    def proto(self):
        """ Read 'Protocol' field """

        return self._frame[self._hptr + 9]

    @property
    def cksum(self):
        """ Read 'Checksum' field """

        if not hasattr(self, "_cksum"):
            self._cksum = struct.unpack("!H", self._frame[self._hptr + 10 : self._hptr + 12])[0]
        return self._cksum

    @property
    def src(self):
        """ Read 'Source address' field """

        if not hasattr(self, "_src"):
            self._src = IPv4Address(self._frame[self._hptr + 12 : self._hptr + 16])
        return self._src

    @property
    def dst(self):
        """ Read 'Destination address' field """

        if not hasattr(self, "_dst"):
            self._dst = IPv4Address(self._frame[self._hptr + 16 : self._hptr + 20])
        return self._dst

    @property
    def options(self):
        """ Read list of options """

        if not hasattr(self, "_options"):
            self._options = []
            switch = {}
            optr = self._hptr + IP4_HEADER_LEN

            while optr < self._hptr + self.hlen:
                if self._frame[optr] == IP4_OPT_EOL:
                    self.options.append(Ip4OptEol())
                    break
                if self._frame[optr] == IP4_OPT_NOP:
                    self.options.append(Ip4OptNop())
                    optr += IP4_OPT_NOP_LEN
                    continue
                self.options.append(switch.get(self._frame[optr], Ip4OptUnk)(self._frame, optr))
                optr += self._frame[optr + 1]

        return self._options

    @property
    def data(self):
        """ Read the data packet carries """

        if not hasattr(self, "_data"):
            self._data = self._frame[self._hptr + self.hlen :]
        return self._data

    @property
    def olen(self):
        """ Calculate options length """

        if not hasattr(self, "_plen"):
            self._plen = self.hlen - IP4_HEADER_LEN
        return self._plen

    @property
    def dlen(self):
        """ Calculate data length """

        if not hasattr(self, "_dlen"):
            self._dlen = len(self) - self.hlen
        return self._dlen

    @property
    def packet(self):
        """ Read the whole packet """

        if not hasattr(self, "_packet"):
            self._packet = self._frame[self._hptr :]
        return self._packet

    @property
    def pseudo_header(self):
        """ Create IPv4 pseudo header used by TCP and UDP to compute their checksums """

        if not hasattr(self, "_pseudo_header"):
            self._pseudo_header = struct.pack("! 4s 4s BBH", self.src.packed, self.dst.packed, 0, self.proto, self.plen - self.hlen)
        return self._pseudo_header

    def _packet_integrity_check(self):
        """ Packet integrity check to be run on raw packet prior to parsing to make sure parsing is safe """

        if not config.packet_integrity_check:
            return False

        if len(self) < IP4_HEADER_LEN:
            return "IPv4 integrity - wrong packet length (I)"

        hlen = (self._frame[self._hptr + 0] & 0b00001111) << 2
        plen = struct.unpack("!H", self._frame[self._hptr + 2 : self._hptr + 4])[0]
        if not IP4_HEADER_LEN <= hlen <= plen == len(self):
            return "IPv4 integrity - wrong packet length (II)"

        # Cannot compute checksum earlier because it depends on sanity of hlen field
        if inet_cksum(self._frame[self._hptr : self._hptr + hlen]):
            return "IPv4 integriy - wrong packet checksum"

        optr = self._hptr + IP4_HEADER_LEN
        while optr < self._hptr + hlen:
            if self._frame[optr] == IP4_OPT_EOL:
                break
            if self._frame[optr] == IP4_OPT_NOP:
                optr += 1
                if optr > self._hptr + hlen:
                    return "IPv4 integrity - wrong option length (I)"
                continue
            if optr + 1 > self._hptr + hlen:
                return "IPv4 integrity - wrong option length (II)"
            if self._frame[optr + 1] == 0:
                return "IPv4 integrity - wrong option length (III)"
            optr += self._frame[optr + 1]
            if optr > self._hptr + hlen:
                return "IPv4 integrity - wrong option length (IV)"

        return False

    def _packet_sanity_check(self):
        """ Packet sanity check to be run on parsed packet to make sure packet's fields contain sane values """

        if not config.post_parse_sanity_check:
            return False

        if not self.ver == 4:
            return "IP sanityi - 'ver' must be 4"

        if self.ver == 0:
            return "IP sanity - 'ttl' must be greater than 0"

        if self.src.is_multicast:
            return "IP sanity - 'src' must not be multicast"

        if self.src.is_reserved:
            return "IP sanity - 'src' must not be reserved"

        if self.src.is_limited_broadcast:
            return "IP sanity - 'src' must not be limited broadcast"

        if self.flag_df and self.flag_mf:
            return "IP sanity - 'flag_df' and 'flag_mf' must not be set simultaneously"

        if self.offset and self.flag_df:
            return "IP sanity - 'offset' must be 0 when 'df_flag' is set"

        if self.options and config.ip4_option_packet_drop:
            return "IP sanity - packet must not contain options"

        return False


#
#   IPv4 options
#


# IPv4 option - End of Option Linst

IP4_OPT_EOL = 0
IP4_OPT_EOL_LEN = 1


class Ip4OptEol:
    """ IP option - End of Option List """

    def __init__(self):
        self.kind = IP4_OPT_EOL

    def __str__(self):
        return "eol"


# IPv4 option - No Operation (1)

IP4_OPT_NOP = 1
IP4_OPT_NOP_LEN = 1


class Ip4OptNop:
    """ IP option - No Operation """

    def __init__(self):
        self.kind = IP4_OPT_NOP

    def __str__(self):
        return "nop"


# IPv4 option not supported by this stack


class Ip4OptUnk:
    """ IP option not supported by this stack """

    def __init__(self, frame, optr):
        self.kind = frame[optr + 0]
        self.len = frame[optr + 1]
        self.data = frame[optr + 2 : optr + self.len]

    def __str__(self):
        return f"unk-{self.kind}-{self.len}"

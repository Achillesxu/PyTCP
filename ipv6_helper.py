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


#
# ipv6_helper.py - module contains IPv6 helper functions
#


from ipaddress import IPv6Address, IPv6Interface, IPv6Network
from re import sub


def ipv6_eui64(mac, prefix=IPv6Network("fe80::/64")):
    """ Create IPv6 EUI64 address """

    assert prefix.prefixlen == 64

    eui64 = sub(r"[.:-]", "", mac).lower()
    eui64 = eui64[0:6] + "fffe" + eui64[6:]
    eui64 = hex(int(eui64[0:2], 16) ^ 2)[2:].zfill(2) + eui64[2:]
    eui64 = ":".join(eui64[_ : _ + 4] for _ in range(0, 16, 4))
    return IPv6Interface(prefix.network_address.exploded[0:20] + eui64 + "/" + str(prefix.prefixlen))


def ipv6_solicited_node_multicast(ipv6_address):
    """ Create IPv6 solicited node multicast address """

    return IPv6Address("ff02::1:ff" + ipv6_address.exploded[-7:])


def ipv6_multicast_mac(ipv6_multicast_address):
    """ Create IPv6 multicast MAC address """

    return "33:33:" + ":".join(["".join(ipv6_multicast_address.exploded[-9:].split(":"))[_ : _ + 2] for _ in range(0, 8, 2)])

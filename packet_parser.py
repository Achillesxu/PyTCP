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
# packet_parser.py - module contains packet parser support class
#

import loguru

import pp_arp
import pp_ether
import pp_icmp4
import pp_icmp6
import pp_ip4
import pp_ip6
import pp_tcp
import pp_udp
from tracker import Tracker


class PacketParser:
    """ Packet parser support class """

    def __init__(self, raw_packet):
        """ Class constructor """

        self.logger = loguru.logger.bind(object_name="packet_parser.")

        self.tracker = Tracker("RX")

        self.raw_packet = raw_packet

        # Ethernet packet parsing
        self.ether = pp_ether.EtherPacket(raw_packet, 0)
        if self.ether.sanity_check_failed:
            self.logger.critical(f"{self.tracker} - {self.ether.sanity_check_failed}")
            return
        self.logger.debug(f"{self.tracker} - {self.ether}")

        # ARP packet parsing
        if self.ether.type == pp_ether.ETHER_TYPE_ARP:
            self.arp = pp_arp.ArpPacket(raw_packet, self.ether.dptr)
            if self.arp.sanity_check_failed:
                self.logger.critical(f"{self.tracker} - {self.arp.sanity_check_failed}")
                return
            self.logger.debug(f"{self.tracker} - {self.arp}")
            return

        # IPv4 packet parsing
        if self.ether.type == pp_ether.ETHER_TYPE_IP4:
            self.ip = self.ip4 = pp_ip4.Ip4Packet(raw_packet, self.ether.dptr)
            if self.ip4.sanity_check_failed:
                self.logger.critical(f"{self.tracker} - {self.ip4.sanity_check_failed}")
                return
            self.logger.debug(f"{self.tracker} - {self.ip4}")

            # ICMPv4 packet parsing
            if self.ip4.proto == pp_ip4.IP4_PROTO_ICMP4:
                self.icmp4 = pp_icmp4.Icmp4Packet(raw_packet, self.ip4.dptr)
                if self.icmp4.sanity_check_failed:
                    self.logger.critical(f"{self.tracker} - {self.icmp4.sanity_check_failed}")
                    return
                self.logger.debug(f"{self.tracker} - {self.icmp4}")
                return

            # UDP packet parsing
            if self.ip4.proto == pp_ip4.IP4_PROTO_UDP:
                self.udp = pp_udp.UdpPacket(raw_packet, self.ip4.dptr, self.ip4.pseudo_header)
                if self.udp.sanity_check_failed:
                    self.logger.critical(f"{self.tracker} - {self.udp.sanity_check_failed}")
                    return
                self.logger.debug(f"{self.tracker} - {self.udp}")
                return

            # TCP packet parsing
            if self.ip4.proto == pp_ip4.IP4_PROTO_TCP:
                self.tcp = pp_tcp.TcpPacket(raw_packet, self.ip4.dptr, self.ip4.pseudo_header)
                if self.tcp.sanity_check_failed:
                    self.logger.critical(f"{self.tracker} - {self.tcp.sanity_check_failed}")
                    return
                self.logger.debug(f"{self.tracker} - {self.tcp}")
                return

        # IPv6 packet parsing
        if self.ether.type == pp_ether.ETHER_TYPE_IP6:
            self.ip = self.ip6 = pp_ip6.Ip6Packet(raw_packet, self.ether.dptr)
            if self.ip6.sanity_check_failed:
                self.logger.critical(f"{self.tracker} - {self.ip6.sanity_check_failed}")
                return
            self.logger.debug(f"{self.tracker} - {self.ip6}")

            # ICMPv6 packet parsing
            if self.ip6.next == pp_ip6.IP6_NEXT_HEADER_ICMP6:
                self.icmp6 = pp_icmp6.Icmp6Packet(raw_packet, self.ip6.dptr, self.ip6.pseudo_header, self.ip6.src, self.ip6.dst, self.ip6.hop)
                if self.icmp6.sanity_check_failed:
                    self.logger.critical(f"{self.tracker} - {self.icmp6.sanity_check_failed}")
                    return
                self.logger.debug(f"{self.tracker} - {self.icmp6}")
                return

            # UDP packet parsing
            if self.ip6.next == pp_ip6.IP6_NEXT_HEADER_UDP:
                self.udp = pp_udp.UdpPacket(raw_packet, self.ip6.dptr, self.ip6.pseudo_header)
                if self.udp.sanity_check_failed:
                    self.logger.critical(f"{self.tracker} - {self.udp.sanity_check_failed}")
                    return
                self.logger.debug(f"{self.tracker} - {self.udp}")
                return

            # TCP packet parsing
            if self.ip6.next == pp_ip6.IP6_NEXT_HEADER_TCP:
                self.tcp = pp_tcp.TcpPacket(raw_packet, self.ip6.dptr, self.ip6.pseudo_header)
                if self.tcp.sanity_check_failed:
                    self.logger.critical(f"{self.tracker} - {self.tcp.sanity_check_failed}")
                    return
                self.logger.debug(f"{self.tracker} - {self.tcp}")
                return

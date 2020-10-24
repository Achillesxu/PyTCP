#!/usr/bin/env python3

"""

PyTCP, Python TCP/IP stack simulation version 0.1 - 2020, Sebastian Majewski
phrx_icmp.py - packet handler for inbound ICMP packets

"""

import ps_icmp


def phrx_icmp(self, ip_packet_rx, icmp_packet_rx):
    """ Handle inbound ICMP packets """

    self.logger.opt(ansi=True).info(f"<green>{icmp_packet_rx.tracker}</green> - {icmp_packet_rx}")

    # Respond to ICMP Echo Request packet
    if icmp_packet_rx.hdr_type == ps_icmp.ICMP_ECHOREQUEST and icmp_packet_rx.hdr_code == 0:
        self.logger.debug(f"Received ICMP echo packet from {ip_packet_rx.hdr_src}, sending reply")

        self.phtx_icmp(
            ip_dst=ip_packet_rx.hdr_src,
            icmp_type=ps_icmp.ICMP_ECHOREPLY,
            icmp_msg_id=icmp_packet_rx.msg_id,
            icmp_msg_seq=icmp_packet_rx.msg_seq,
            icmp_msg_data=icmp_packet_rx.msg_data,
            echo_tracker=icmp_packet_rx.tracker,
        )
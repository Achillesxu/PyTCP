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
# service_tcp_echo.py - 'user space' service TCP Echo (RFC 862)
#


import threading

import tcp_socket

malpka = (
    "                                       \n"
    + "                                       \n"
    + "                                       \n"
    + "                                       \n"
    + '               .="=.                   \n'
    + "             _/.-.-.\_    _            \n"
    + "            ( ( o o ) )   ))           \n"
    + '             |/  "  \|   //            \n'
    + "              \\'---'/   //             \n"
    + "              /`---`\\  ((              \n"
    + "             / /_,_\ \\  \\\\             \n"
    + "             \_\\_'__/ \  ))            \n"
    + "             /`  /`~\  |//             \n"
    + "            /   /    \  /              \n"
    + "        ,--`,--'\/\    /               \n"
    + "         '-- \"--'  '--'                \n"
    + "                                       \n"
    + "                                       \n"
    + "                                       \n"
    + "                                       \n"
    + "                                       \n"
)

malpa = (
    "______AAAA_______________AAAA______\n"
    + "      VVVV               VVVV       \n"
    + "      (__)               (__)       \n"
    + "       \ \               / /        \n"
    + "        \ \              / /         \n"
    + '         > \   .="=.   / <          \n'
    + "          > \ /     \ / <           \n"
    + "           > \\\_o_o_// <            \n"
    + "            > ( (_) ) <             \n"
    + "             >|     |<              \n"
    + "            / |\\___/| \\             \n"
    + "            / \_____/ \\             \n"
    + "            /         \\             \n"
    + "             /   o   \\              \n"
    + "              ) ___ (               \n"
    + "             / /   \ \              \n"
    + "            ( /     \ )             \n"
    + "            ><       ><             \n"
    + "           ///\     /\\\\\\            \n"
    + "           '''       '''            \n"
)


class ServiceTcpEcho:
    """ TCP Echo service support class """

    def __init__(self, local_ip_address="0.0.0.0", local_port=7):
        """ Class constructor """

        threading.Thread(target=self.__thread_service, args=(local_ip_address, local_port)).start()

    def __thread_service(self, local_ip_address, local_port):
        """ Service initialization """

        socket = tcp_socket.TcpSocket()
        socket.bind(local_ip_address, local_port)
        socket.listen()
        print(f"Service TCP Echo: Socket created, bound to {local_ip_address}, port {local_port} and set to listening mode")

        while True:
            new_socket = socket.accept()
            print(f"Service TCP Echo: Inbound connection received from {new_socket.remote_ip_address}, port {new_socket.remote_port}")

            threading.Thread(target=self.__thread_connection, args=(new_socket,)).start()

    def __thread_connection(self, socket):
        """ Inbound connection handler """

        print(f"Service TCP Echo: Sending first message to {socket.remote_ip_address}, port {socket.remote_port}")
        socket.send(b"***CLIENT OPEN / SERVICE OPEN***\n")

        while True:
            message = socket.receive()

            if message is None:
                print(f"Service TCP Echo: Connection to {socket.remote_ip_address}, port {socket.remote_port} has been closed by peer")
                print(f"Service TCP Echo: Sending last message to {socket.remote_ip_address}, port {socket.remote_port}")
                socket.send(b"***CLIENT CLOSED, SERVICE CLOSING***\n")
                print(f"Service TCP Echo: Closng connection to {socket.remote_ip_address}, port {socket.remote_port}")
                socket.close()
                break

            if message in {b"CLOSE\n", b"CLOSE\r\n", b"close\n", b"close\r\n"}:
                print(f"Service TCP Echo: Sending last message to {socket.remote_ip_address}, port {socket.remote_port}")
                socket.send(b"***CLIENT OPEN, SERVICE CLOSING***\n")
                print(f"Service TCP Echo: Closng connection to {socket.remote_ip_address}, port {socket.remote_port}")
                socket.close()
                continue

            if "malpka" in str(message, "utf-8").strip().lower():
                print(f"Service TCP Echo: Sending '***END***' message to {socket.remote_ip_address}, port {socket.remote_port}")
                socket.send(bytes(malpka, "utf-8"))
                continue

            if "malpa" in str(message, "utf-8").strip().lower():
                print(f"Service TCP Echo: Sending '***END***' message to {socket.remote_ip_address}, port {socket.remote_port}")
                socket.send(bytes(malpa, "utf-8"))
                continue

            if "malpi" in str(message, "utf-8").strip().lower():
                print(f"Service TCP Echo: Sending '***END***' message to {socket.remote_ip_address}, port {socket.remote_port}")
                for malpka_line, malpa_line in zip(malpka.split("\n"), malpa.split("\n")):
                    socket.send(bytes(malpka_line + malpa_line + "\n", "utf-8"))
                continue

            print(f"Service TCP Echo: Received message from {socket.remote_ip_address}, port {socket.remote_port} -", message)
            if socket.send(message):
                print(f"Service TCP Echo: Echo'ed message back to {socket.remote_ip_address}, port {socket.remote_port} -", message)

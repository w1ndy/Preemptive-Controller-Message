#!/usr/bin/python2

# UDP Client
# Send udp packets with timestamp to server

import socket
import random
import sys
import os
import time

from scapy.all import *

controller_hwaddr = '32:a4:04:30:c0:fd'

server_hwaddr = '7a:4e:18:bf:a3:24'
client_hwaddr = '1a:b6:49:59:92:aa'

interface   = "h1-eth0"
custom_type = 0x0801

rate        = 0.0
pkt_count   = 0
pkt_size    = 1024
delay       = 0.002

ether_size  = 14
control_pkt = 0
server_pkt  = 0

def construct_message():
    timestamp = str(long(round(time.time() * 1000)))
    return timestamp + '#' + os.urandom(pkt_size - len(timestamp) - 1)

def construct_packet():
    global control_pkt
    global server_pkt

    msg = construct_message()
    if random.random() < rate:
        control_pkt += 1
        return '\x32\xa4\x04\x30\xc0\xfd\x1a\xb6\x49\x59\x92\xaa\x08\x01' + msg
    else:
        server_pkt += 1
        return '\x7a\x4e\x18\xbf\xa3\x24\x1a\xb6\x49\x59\x92\xaa\x08\x01' + msg

def send_pkt():
    s = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
    s.bind((interface, 0))
    for i in xrange(pkt_count):
        s.send(construct_packet())
        if (i + 1) % 1000 == 0:
            print '%s: %d packets sent, %d for controller, %d for server' % (time.ctime(), i + 1, control_pkt, server_pkt)
        time.sleep(delay)
    s.close()

if __name__ == '__main__':
    if not len(sys.argv) in [3, 4]:
        print "Usage: "     + sys.argv[0] + " FLOW_MISS_RATE PACKET_COUNT PACKET_SIZE"
        print "Example: "   + sys.argv[0] + " 0.4 10000"
        print "Example: "   + sys.argv[0] + " 0.4 10000 1024"
        exit()

    rate        = float(sys.argv[1])
    pkt_count   = int(sys.argv[2])
    if len(sys.argv) >= 4:
        pkt_size = int(sys.argv[3])

    datf = open('server.dat', 'a')
    datf.write("%.1f%% %d bpp: " % (rate * 100, pkt_size))
    datf.close()

    send_pkt()

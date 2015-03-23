#!/usr/bin/python2

# UDP Server
# Receive udp packets sent from client and sample network performance

import socket
import random
import sys
import os
import time

from scapy.all import *

server_ip   = "0.0.0.0"
server_port = 8090

custom_type = 0x0801
interface   = "h2-eth0"
timeout     = 3

peek_max    = 0
peek_min    = 9999.99
total       = 0
count       = 0

logf = open('server.log', 'w')

def time_diff(t):
    now = long(round((time.time() * 1000)))
    return now - t

def process(pkt):
    global peek_max
    global peek_min
    global total
    global count
    global exit_timer

    if Raw not in pkt:
        return
    count += 1
    diff = time_diff(long(str(pkt[Raw]).split('#')[0]))
    total += diff
    peek_max = max(diff, peek_max)
    peek_min = min(diff, peek_min)
    if count and count % 1000 == 0:
        logf.write("%s: received %d packets, avg %.3f ms\n" % (time.ctime(), count, float(total) / float(count)))
        logf.flush()

def recv_pkt():
    logf.write("start sniffing...\n")
    try:
        sniff(
            filter      = "ether proto %s" % custom_type,
            iface       = interface,
            prn         = lambda x: process(x),
            store       = False)
    except KeyboardInterrupt:
        logf.write("keyboard interrupted\n")
    except Exception as e:
        logf.write("sniffing exited unexpectedly: %s\n" % str(e))
    logf.write("exiting...")
    if count != 0:
        dats = 'Recv: %d, Total cost: %d, Avg cost: %.3f, Max: %.3f, Min: %.3f\n' % (count, total, float(total) / float(count), peek_max, peek_min)
        logf.write(dats)
        datf = open('server.dat', 'a')
        datf.write(dats)
        datf.close()
    logf.close()


if __name__ == '__main__':
    pidf = open('server.pid', 'w')
    pidf.write(str(os.getpid()))
    pidf.close()

    recv_pkt()

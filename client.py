#!/usr/bin/python2

# UDP Client
# Send udp packets with timestamp to server

import socket
import random
import sys
import time

server_addr = "10.0.0.2"
server_port = 8090

rate        = 0.0
pkt_count   = 0
delay       = 0.002

def construct_ip_address():
    if random.random() < rate:
        # fake a ip address in 10.100-199.x.x space
        return "10.%d.%d.%d" % (
            random.randint(100, 199),
            random.randint(0, 254),
            random.randint(0, 254))
    else:
        return server_addr

def construct_message():
    return "%ld" % long(round(time.time() * 1000))

def send_pkt():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    for i in xrange(pkt_count):
        ipaddr  = construct_ip_address();
        msg     = construct_message();

        print 'sending: ' + ipaddr + ' / ' + msg
        sock.sendto(construct_message(), (ipaddr, server_port))
        time.sleep(delay)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "Usage: "     + sys.argv[0] + " FLOW_MISS_RATE PACKET_COUNT"
        print "Example: "   + sys.argv[0] + " 0.4 10000"
        exit()

    rate        = float(sys.argv[1])
    pkt_count   = int(sys.argv[2])

    datf = open('server.dat', 'a')
    datf.write("%.1f%%: " % (rate * 100))
    datf.close()

    send_pkt()

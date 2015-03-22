#!/usr/bin/python2

# UDP Server
# Receive udp packets sent from client and sample network performance

import socket
import random
import sys
import os
import time

server_ip   = "0.0.0.0"
server_port = 8090

def time_diff(t):
    now = long(round((time.time() * 1000)))
    return now - t

def recv_pkt():
    peek_max    = 0
    peek_min    = 9999.99
    total       = 0
    count       = 0

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((server_ip, server_port))
    sock.settimeout(3)

    try:
        while True:
            data, addr = sock.recvfrom(1024)
            count += 1
            delta = time_diff(long(data))
            if delta < peek_min:
                peek_min = delta
            if delta > peek_max:
                peek_max = delta
            print "%d ms spent / %d packets received" % (delta, count)
            total += delta
    except KeyboardInterrupt:
        pass
    except Exception, e:
        pass
    finally:
        print "exiting"
        if total != 0:
            datf = open('server.dat', 'a')
            datf.write('Recv: %d, Total cost: %d, Avg cost: %.2f, Max: %.2f, Min: %.2f\n' % (count, total, float(total) / float(count), peek_max, peek_min))
            datf.close()


if __name__ == '__main__':
    pidf = open('server.pid', 'w')
    pidf.write(str(os.getpid()))
    pidf.close()

    recv_pkt()

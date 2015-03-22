#!/bin/bash

cd linux
KCFLAGS=-DPREEMPTIVE_ACTION make modules SUBDIRS=net/openvswitch
cp net/openvswitch/openvswitch.ko ../ovs-preemptive.ko
make modules SUBDIRS=net/openvswitch
cp net/openvswitch/openvswitch.ko ../ovs-nonpreemptive.ko

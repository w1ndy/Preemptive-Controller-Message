#!/bin/bash

set -e

echo -e "\n >> Initializing..."
modprobe libcrc32c
mkdir -p /var/run/openvswitch
mn -c

echo -e "\n >> Running tests for preemptive behavior..."
echo -e "\n >> Cleaning up..."
rm server.dat || true
rmmod openvswitch || true
killall ovsdb-server ovs-vswitchd ryu-manager || true

echo -e "\n >> Injecting kernel module..."
insmod ovs-preemptive.ko

echo -e "\n >> Starting Open vSwitch..."
ovsdb-server --remote=punix:/var/run/openvswitch/db.sock --remote=db:Open_vSwitch,Open_vSwitch,manager_options --pidfile --detach
ovs-vswitchd --pidfile --detach --log-file=/var/log/ovs.log

echo -e "\n >> Starting controller..."
ryu-manager controller.py &
echo -e "\n >> Waiting controller to be ready..."
sleep 5

echo -e "\n >> Starting Mininet..."
python2 topo.py

echo -e "\n >> Parsing data..."
cp server.dat preemptive_full.dat
python2 parser.py preemptive.dat

echo -e "\n >> Running tests for non-preemptive behavior..."
echo -e "\n >> Cleaning up..."
rm server.dat || true
rmmod openvswitch || true
killall ovsdb-server ovs-vswitchd ryu-manager || true

echo -e "\n >> Injecting kernel module..."
insmod ovs-nonpreemptive.ko

echo -e "\n >> Starting Open vSwitch..."
ovsdb-server --remote=punix:/var/run/openvswitch/db.sock --remote=db:Open_vSwitch,Open_vSwitch,manager_options --pidfile --detach
ovs-vswitchd --pidfile --detach --log-file=/var/log/ovs.log

echo -e "\n >> Starting controller..."
ryu-manager controller.py &
echo -e "\n >> Waiting controller to be ready..."
sleep 5

echo -e "\n >> Starting Mininet..."
python2 topo.py

echo -e "\n >> Parsing data..."
cp server.dat nonpreemptive_full.dat
python2 parser.py nonpreemptive.dat

echo -e "\n >> Plotting graph..."
python2 plotter.py preemptive.dat nonpreemptive.dat

from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3
from ryu.lib.packet import packet
from ryu.lib.packet import ethernet
from ryu.lib.packet import arp
from ryu.lib.ip import ipv4_to_bin

class Controller(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(Controller, self).__init__(*args, **kwargs)
        self.mac_to_port    = {}
        self.server_mac     = '7a:4e:18:bf:a3:24'
        self.server_ip      = '10.0.0.2'
        self.server_dp_port = 2
        self.rule_timeout   = 15

    def add_flow(self, datapath, priority, match, actions, buffer_id = None):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        inst    = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]

        if buffer_id:
            mod = parser.OFPFlowMod(
                datapath        = datapath,
                buffer_id       = buffer_id,
                priority        = priority,
                match           = match,
                instructions    = inst)
        else:
            mod = parser.OFPFlowMod(
                datapath        = datapath,
                priority        = priority,
                match           = match,
                instructions    = inst)

        datapath.send_msg(mod)
        self.logger.info("%s: flow rules installed.", datapath.id)

    def install_arp_tracker(self, datapath):
        "Capture arp request packet"

        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        match   = parser.OFPMatch(arp_op = arp.ARP_REQUEST)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath        = datapath,
            priority        = 1,
            match           = match,
            instructions    = inst)

        datapath.send_msg(mod)
        self.logger.info("arp tracker installed for %s", datapath.id)

    def fix_ip(self, datapath, fake_ip):
        "Redirect packets with fake ip to server"

        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch(
            eth_type    = 0x0800,
            ipv4_dst    = fake_ip)
        actions = [
            parser.OFPActionSetField(ipv4_dst = self.server_ip),
            parser.OFPActionOutput(self.server_dp_port)]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath        = datapath,
            priority        = 100,
            match           = match,
            instructions    = inst,
            hard_timeout    = self.rule_timeout)

        datapath.send_msg(mod)

    def send_packet(self, datapath, port, pkt):
        "Deliver packet using PACKET OUT message"

        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        pkt.serialize()
        data    = pkt.data

        actions = [parser.OFPActionOutput(port=port)]
        out     = parser.OFPPacketOut(
            datapath    = datapath,
            buffer_id   = ofproto.OFP_NO_BUFFER,
            in_port     = ofproto.OFPP_CONTROLLER,
            actions     = actions,
            data        = data)

        datapath.send_msg(out)

    def arp_spoof(self, pkt_eth, pkt_arp, datapath, port):
        "Spoof a fake arp response"

        if pkt_arp.opcode != arp.ARP_REQUEST:
            return ;
        pkt = packet.Packet()

        pkt.add_protocol(ethernet.ethernet(
            ethertype   = pkt_eth.ethertype,
            dst         = pkt_eth.src,
            src         = self.server_mac))
        pkt.add_protocol(arp.arp(
            opcode      = arp.ARP_REPLY,
            src_mac     = self.server_mac,
            src_ip      = pkt_arp.dst_ip,
            dst_mac     = pkt_arp.src_mac,
            dst_ip      = pkt_arp.src_ip))

        self.fix_ip(datapath, pkt_arp.dst_ip)
        self.send_packet(datapath, port, pkt)

        #self.logger.info("arp spoofed %s to %s",
        #    pkt_arp.dst_ip, self.server_ip)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath    = ev.msg.datapath
        ofproto     = datapath.ofproto
        parser      = datapath.ofproto_parser

        self.install_arp_tracker(datapath)

        # flow-miss rule
        match   = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]
        self.add_flow(datapath, 0, match, actions)

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        pkt_eth = pkt.get_protocol(ethernet.ethernet)
        pkt_arp = pkt.get_protocol(arp.arp)

        dst = pkt_eth.dst
        src = pkt_eth.src
        dpid = datapath.id

        if pkt_arp and pkt_arp.opcode == arp.ARP_REQUEST:
            if str(pkt_arp.dst_ip).split('.')[1].startswith('1'):
                self.arp_spoof(pkt_eth, pkt_arp, datapath, in_port)
                return
            self.logger.info("%s: uncaptured arp request for ip %s",
                dpid, pkt_arp.dst_ip)

        self.logger.info("%s: packet in from %s to %s at port %s",
            dpid, src, dst, in_port)

        self.mac_to_port.setdefault(dpid, {})
        self.mac_to_port[dpid][src] = in_port

        if dst in self.mac_to_port[dpid]:
            out_port = self.mac_to_port[dpid][dst]
        else:
            out_port = ofproto.OFPP_FLOOD

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_dst=dst)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
                return
            else:
                self.add_flow(datapath, 1, match, actions)
        data = None
        if msg.buffer_id == ofproto.OFP_NO_BUFFER:
            data = msg.data

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                  in_port=in_port, actions=actions, data=data)
        datapath.send_msg(out)

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
        self.mac_to_port        = {}

        self.server_hwaddr      = '7a:4e:18:bf:a3:24'
        self.client_hwaddr      = '1a:b6:49:59:92:aa'
        self.controller_hwaddr  = '32:a4:04:30:c0:fd'
        self.custom_type        = 0x0801
        self.server_dp_port     = 2

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

    def install_forwarder(self, datapath):
        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        # Forward packets to server
        match   = parser.OFPMatch(eth_dst = self.server_hwaddr)
        actions = [parser.OFPActionOutput(self.server_dp_port)]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath        = datapath,
            priority        = 1,
            match           = match,
            instructions    = inst)

        datapath.send_msg(mod)

        #Capture packets sent to controller
        match   = parser.OFPMatch(eth_dst = self.controller_hwaddr)
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER)]

        inst = [parser.OFPInstructionActions(
            ofproto.OFPIT_APPLY_ACTIONS, actions)]
        mod = parser.OFPFlowMod(
            datapath        = datapath,
            priority        = 1,
            match           = match,
            instructions    = inst)

        datapath.send_msg(mod)

        self.logger.info("forwarder installed for %s", datapath.id)

    def redirect(self, datapath, buffer_id):
        #print "Redirecting packets to server..."

        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        if buffer_id == ofproto.OFP_NO_BUFFER:
            print "error: buffer id absent"
            return

        ofproto = datapath.ofproto
        parser  = datapath.ofproto_parser

        actions = [parser.OFPActionOutput(self.server_dp_port)]
        out     = parser.OFPPacketOut(
            datapath    = datapath,
            buffer_id   = buffer_id,
            in_port     = ofproto.OFPP_CONTROLLER,
            actions     = actions)

        datapath.send_msg(out)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath    = ev.msg.datapath
        ofproto     = datapath.ofproto
        parser      = datapath.ofproto_parser

        self.install_forwarder(datapath)

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

        dst = pkt_eth.dst
        src = pkt_eth.src
        dpid = datapath.id

        if pkt_eth.dst == self.controller_hwaddr and pkt_eth.ethertype == self.custom_type:
            self.redirect(datapath, msg.buffer_id)
            return

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
            match = parser.OFPMatch(
                in_port     = in_port,
                eth_dst     = dst)
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

'''
This file implements communication between the AWS network and the functions offered in the C2server.py
in order to provide an interface for the RL agent to interact and perform defense actions in AWS.

Function design - each function, in necessary, takes node as a parameter, which refers to the agent's decided machine index -- (e.g, 0 for PublicWeb1). 
For example, if an RL agent wanted to add a honeypot service on WEB (index 2), the function addFakeNode(node) would be called with node equating to the
index of the machine, 2. This is because we initialize all the machines as gRPC clients, but we must know which machine to take which action on. The RL
agent will provide an action in a set type e.g. (0, 1) in cybergym.py, where the first index will be the input for node in each network.py function.

Reference Machine Index:
0 - PublicWeb1
1 - PublicWeb2
2 - WEB
3 - PC1
4 - PC2
5 - PC3
6 - NTP
7 - DB
'''
import logging
from time import sleep
from concurrent import futures
import sys
sys.path.insert(0, './pb')
import grpc
import pb.c2_pb2 as pb
import pb.c2_pb2_grpc as pbg

# TODO: integrate fake data as a defensive action to perform and observe. This file only automates Cowrie (Fake Node) and SUID (Fake Edge)

class Network():
    def __init__(self):
        self.nodes = { 
                0: {"subnet": "public", "ip": "10.0.15.134", "value": 10, "manipulated_value": 10, 
                     "cowrie": False, "fake_edge_deployed": False, "fake_data": False, "attacker_percieved_state": 0},
                1: {"subnet": "public", "ip": "10.0.15.134", "value": 10, "manipulated_value": 10, 
                     "cowrie": False, "fake_edge_deployed": False, "fake_data": False, "attacker_percieved_state": 0},
                2: {"subnet": "public", "ip": "10.0.15.134", "value": 10, "manipulated_value": 10, 
                     "cowrie": False, "fake_edge_deployed": False, "fake_data": False, "attacker_percieved_state": 0} 
                     } 
        
        self.suid_history = []


        self.clients = self.initialize_clients()
        return


    # untimed 
    def observeNode(self, node):
        req = pb.GetPositionsReq()
        client = self.clients[node]
        logs = {}
        res = client.GetPositions(req)
        for position in res.positions:
            logs[position.position] = {
                "time": position.time, 
                "state": position.state,
                "cowrie": self.nodes[node]['cowrie'],
                "suid": self.nodes[node]['suid'],
                "fake_data": self.nodes[node]['fake_data'],
                "manipulated_value": self.nodes[node]['manipulated_value'],
                "attacker_percieved_state": self.nodes[node]['attacker_percieved_state']
            }
        return logs
    
    # This function returns an observation dictionary of the entire network, in contrast to the previous function where only one machine is observed. 
    def observeNetwork(self):
        req = pb.GetPositionsReq()

        # save index, i, of client to record past actions -- this is to act like our "node", a numerical representation of each machine
        # so that we correctly save to the correct past_action key.
        logs = {}
        for i, client in enumerate(self.clients):
            res = client.GetPositions(req)
            for position in res.positions:
                logs[i] = {
                "time": position.time, 
                "state": position.state,
                "cowrie": self.nodes[i]['cowrie'],
                "fake_edge_deployed": self.nodes[i]['fake_edge_deployed'],
                "fake_data": self.nodes[i]['fake_data'],
                "attacker_percieved_state": self.nodes[i]['attacker_percieved_state'],
                "manipulated_value": self.nodes[i]['manipulated_value'],
            }
        return logs

    # TODO: modify SUID and modify attacker's perceived state (2)
    def addFakeEdge(self, node):
        # PushActions expects a list for action
        action = [pb.Action(suid=pb.SUIDAction(start=True))]
        req = pb.PushActionsReq(actions=action)
        print(self.clients[node].PushActions(req))
        self.modify_past_actions(node, "fake_edge_deployed", True)
        return 

    # identical to previous function but logs SUID action as False
    def removeFakeEdge(self, node):
        action = [pb.Action(suid=pb.SUIDAction(start=False))]
        req = pb.PushActionsReq(actions=action)
        print(self.clients[node].PushActions(req))
        self.modify_past_actions(node, "fake_edge_deployed", False)
        return 

    # iterate through all clients and reset.
    def eradicate(self):
        for client in self.clients:
           client.Eradicate(pb.EradicateReq)
        return

    def addFakeNode(self, node):
        action = [pb.Action(cowrie=pb.CowrieAction(start=True))]
        req = pb.PushActionsReq(actions=action)
        print(self.clients[node].PushActions(req))
        self.modify_past_actions(node, "cowrie", True)
        return 

    # identical to addFakeNode but logs Cowrie action as false
    def removeFakeNode(self, node):
        action = [pb.Action(cowrie=pb.CowrieAction(start=False))]
        req = pb.PushActionsReq(actions=action)
        print(self.clients[node].PushActions(req))
        self.modify_past_actions(node, "cowrie", False)
        return 
    
    def addFakeData(self, node):
        # action = [pb.Action(cowrie=pb.CowrieAction(start=True))]
        # req = pb.PushActionsReq(actions=action)
        # print(self.clients[node].PushActions(req))
        self.modify_past_actions(node, "fake_data", True)
        return 

    def removeFakeData(self, node):
        # action = [pb.Action(cowrie=pb.CowrieAction(start=False))]
        # req = pb.PushActionsReq(actions=action)
        # print(self.clients[node].PushActions(req))
        self.modify_past_actions(node, "fake_data", False)
        return 
    
    
    # modify the node's past_actions taken by defender from previous round
    # In this function, we edit "past_actions" key in self.nodes to log what previous
    # action the defender has taken. We provide three parameters: 
    #   1) node -- at which machine is the action being taken
    #   2) action -- what was the action? (0 - SUID, 1 - Cowrie)
    #   3) active -- was the action being added or removed? (True or False) 
    def modify_past_actions(self, node, action, active):
        self.nodes[node][action] = active
        return 

    # This function initializes all clients for the nodes defined in self.nodes. 
    # It also inherently assigns an index to each machine node (e.g, 0 for PublicWeb1)
    # in the order the nodes were defined in self.nodes.
    # Note that all servers must be running on port 17737 for this function
    # to work properly
    def initialize_clients(self):
        server_ips = [values.get("ip") for values in self.nodes.values()]
        channels = [grpc.insecure_channel(f"{ip}:17737") for ip in server_ips]
        clients = [pbg.C2Stub(channel) for channel in channels]
        return clients


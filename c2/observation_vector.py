'''
This file handles the observation translation from the network into a format the RL agent understands

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
import numpy as np
from time import sleep
from concurrent import futures
import sys
sys.path.insert(0, './pb')
import time

from network import Network

class NetworkState():
    def __init__(self, clients):
        self.nodes = { 
                0: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                1: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                2: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                3: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                4: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                5: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                6: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                },
                7: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv.esc, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    'fake_edge_deployed': False,
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': 0
                }
        }

        self.attacker_percieved_state = 0 # 0 - not tricked, 1 - fake foothold, 2 - fake priv es, 3 - fake data. ex
        # TODO: higher dimensions
        self.suid_history = []

        self.clients = clients
        return

    # return observation vector of entire network for agent
    def observationVector(self):
        obsVector = {
                    'manipulated_values' : [],
                    'node_state': [],
                    'cowrie': [],
                    'fake_edge_deployed':[],
                    # 'suid_history':[],  
                    'fake_data': [],
                    'attacker_percieved_state': [] 
                }
        # iterate through each node
        for i, node in enumerate(self.nodes):
            # check manipulated value; 0 if unchanged
            obsVector['manipulated_values'].append(self.nodes[i]['manipulated_values'])
                        
            # check state of the node and one hot encode 
            state = self.nodes[i]['node_state']
            encoded_state = self.one_hot_encode(state, 3) # 3 possible states for attacker 
            obsVector['node_state'].append(encoded_state)

            # check if cowrie is true and add to binary vector
            if self.nodes[i]['cowrie']:
                obsVector['cowrie'].append(1)
            else: 
                obsVector['cowrie'].append(0)

            # check if fake edge added is true and add to binary vector
            if self.nodes[i]['fake_edge_deployed']:
                obsVector['fake_edge_deployed'].append(1)
            else: 
                obsVector['fake_edge_deployed'].append(0)


            # check where SUID has been activated and add to vector

            # check if fake data and add to binary vector
            if self.nodes[i]['fake_data']:
                obsVector['fake_data'].append(1)
            else: 
                obsVector['fake_data'].append(0)

            # check attacker's percieved state and one hot encode
            attacker_state = self.nodes[i]['attacker_percieved_state']
            encoded_attacker_state = self.one_hot_encode(attacker_state, 4)
            obsVector['attacker_percieved_state'].append(encoded_attacker_state)

        return obsVector

        # observation = np.concatenate([
        #     np.array(obsVector['manipulated_values']),
        #     np.array(obsVector['node_state']),
        #     np.array(obsVector['cowrie']),
        #     np.array(obsVector['fake_edge_deployed']),
        #     # np.array(obsVector['suid_history'])(),
        #     np.array(obsVector['fake_data']),
        #     np.array(obsVector['attacker_percieved_state']),
        # ])

        # return observation

    def one_hot_encode(self, state, num_classes):
        one_hot_vector = [0] * num_classes
        one_hot_vector[state] = 1
        return one_hot_vector
    
    # updates NetworkState nodes every second with observations from the network
    def updateNetwork(self, network):
        '''
        self.nodes = { 
                0: {
                    'manipulated_values' : 0, # starts as default 0 -- unchanged
                    'node_state': 0, # actual state of attacker, 0 - foothold, 1 - priv. es, 2 - data ex.
                    'cowrie': False,    # assumed that defender has not started Cowrie
                    # higher dimensions for connected nodes?
                    'suid_history':[],  # assumed no initial added SUID
                    'fake_data': False, # assumed no initial fake data added
                    'attacker_percieved_state': [] # 0 - not tricked, 1 - fake foothold, 2 - fake priv es, 3 - fake exfil
                }
        }'''
        current_state = network.observeNetwork()

        # attacker activity for each node

        attacker_activity = []
        for i, _ in enumerate(self.nodes):
            try:
                self.nodes[i]['manipulated_values'] = current_state[i]['manipulated_value']
                self.nodes[i]['node_state'] = self.translateState(current_state[i]['state'])    
                self.nodes[i]['cowrie'] = current_state[i]["cowrie"]
                self.nodes[i]['fake_edge_deployed'] = current_state[i]['fake_edge_deployed']
                self.nodes[i]['fake_data'] = current_state[i]["fake_data"]
                self.nodes[i]['attacker_percieved_state'] = current_state[i]['attacker_percieved_state']
                # self.nodes[i]['suid_history'] =  
                attacker_activity.append(True)
                continue
            
            # if current_state is empty -- indicates no attacker activity
            except KeyError:
                attacker_activity.append(False)
                continue
        
        return attacker_activity
            


    # change state  to numerical rep. (e.g foothold to 0, priv. esc to 1)
    def translateState(self, state):
        if state == "foothold":
            return 0
        if state == "privesc":
            return 1
        if state == "exfil":
            return 2
        else:
            return # no attacker activity detected

# demo of obtaining network observation
def stream_observation():
    # connect to the Network
    net = Network()
    
    # feed clients into NetworkState class
    state = NetworkState(net.clients)

    while True:
        state.updateNetwork(net)
        print(state.observationVector())
        sleep(1)

# test run 
if __name__ == "__main__":
    stream_observation()
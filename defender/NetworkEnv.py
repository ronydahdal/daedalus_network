'''
This environment provides an interface 
'''

class NetworkEnvInterface:
    def __init__(self, network, state):
        self.network = network
        self.state = state
        self.done = False

    def reset(self):
        # Reset the network to the initial state
        self.network.eradicate()
        self.done = False
        return self.state.observationVector()  # Return initial state observation

    def step(self, node, action):
        """
        takes action on a specific node and returns the next state, reward, and done flag.
        """
        self.state.updateNetwork(self.network)  # sync state with the network

        try:
            if action == 0 and self.state.nodes[node]["cowrie"] == False:
                self.network.addFakeNode(node)
                print(f"added fake node on machine {node}")
            elif action == 1 and self.state.nodes[node]["fake_edge_deployed"] == False:
                self.network.addFakeEdge(node)
                print(f"added fake edge on machine {node}")
            elif action == 2 and self.state.nodes[node]["fake_data"] == False:
                self.network.addFakeData(node)
                print(f"added fake data on machine {node}")
            elif action == 3 and self.state.nodes[node]["cowrie"] == True:
                self.network.removeFakeNode(node)
                print(f"removed fake node on machine {node}")
            elif action == 4 and self.state.nodes[node]["fake_edge_deployed"] == True:
                self.network.removeFakeEdge(node)
                print(f"removed fake edge on machine {node}")
            elif action == 5 and self.state.nodes[node]["fake_data"] == True:
                self.network.removeFakeData(node)
                print(f"removed fake data on machine {node}")
            elif action == 6:
                print("do nothing")
        except KeyError:
            print("no action taken")

        # update state with action
        self.network.modify_past_actions(node, action, True)
        
        # simulate reward based on action
        reward = self.calculate_reward(node, action)
        
        # get next observation
        next_state = self.state.observationVector()
        
        # check for termination condition (e.g., all attackers mitigated)
        self.done = self.check_termination()
        return next_state, reward, self.done

    def calculate_reward(self, node, action):
        '''
        What should reward look like?
        '''
        state = self.state.nodes[node]
        if action == 0 and state["cowrie"]:
            return 10  # ex: reward for honeypot service
        elif action == 6:
            return -1  # ex: negative reward for doing nothing
        return 0

    def check_termination(self):
        """
        check if no active attackers remain.
        """
        active_attackers = any(
            node["node_state"] > 0 for node in self.state.nodes.values()
        )
        return not active_attackers

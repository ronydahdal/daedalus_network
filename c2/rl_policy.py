'''
This file implements a randomly initialized policy that is made up of two NN:
    1) a NN that selects a host machine to take action on 
    2) a NN that selects an action to take on the chosen host (output of host NN is part of input for the action NN)
'''

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from time import sleep
from observation_vector import NetworkState
from network import Network

def create_host_selection_network(num_hosts, input_shape):
    model = models.Sequential()
    model.add(layers.Dense(64, activation='relu', input_shape=(input_shape,)))
    # model.add(layers.Input(shape=(input_shape,)))
    # model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(num_hosts, activation='softmax'))  # curently, we are outputting prob dist. of 3 hosts
    return model

def create_action_selection_network(input_shape):
    model = models.Sequential()
    model.add(layers.Dense(64, activation='relu', input_shape=(input_shape,)))
    # model.add(layers.Input(shape=(input_shape,)))
    # model.add(layers.Dense(64, activation='relu'))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(7, activation='softmax'))  # 6 actions (we count 7 as we include doing nothing as the 7th action)
    return model

# Combine the networks without action masking
class CombinedNetwork(tf.keras.Model):
    def __init__(self, num_hosts, host_input_shape, action_input_shape):
        super(CombinedNetwork, self).__init__()
        self.host_selection_network = create_host_selection_network(num_hosts, host_input_shape)
        self.action_selection_network = create_action_selection_network(action_input_shape)

    def call(self, inputs, training=False):
        # Process the input through the host selection network
        host_selection_output = self.host_selection_network(inputs)

        # Sample the output from the host selection network
        host_selection_sample = tf.random.categorical(tf.math.log(host_selection_output), 1)
        host_selection_sample = tf.squeeze(tf.one_hot(host_selection_sample, 8), axis=1)

        # Convert inputs to float32 for concatenation
        inputs = tf.cast(inputs, tf.float32)

        # Concatenate the host selection output with the original inputs
        action_inputs = tf.concat([inputs, host_selection_sample], axis=-1)

        # Process the concatenated inputs through the action selection network
        action_selection_output = self.action_selection_network(action_inputs)
        print(f"host selection: {host_selection_sample}")
        print(f"action selection: {action_selection_output}")
        return host_selection_output, host_selection_sample, action_selection_output

class DefenderPolicy:
    def __init__(self):
        self.network = Network()
        self.state = NetworkState(self.network.clients)
        
        # 1 manipulated value + 3 node states + 1 cowrie + 1 fake edge deployed + 1 fake data + 4 attacker perceived states, for each host in network
        num_hosts = len(self.network.clients)
        observation_shape = (num_hosts * 1) + (num_hosts * 3) + (num_hosts * 1) + (num_hosts * 1) + (num_hosts * 1) + (num_hosts * 4)
        
        # Host input shape is the observation vector shape
        # Action input shape is the observation vector shape + host selection output shape
        self.model = CombinedNetwork(num_hosts, observation_shape, observation_shape + num_hosts)
        
        self.model.compile(optimizer=optimizers.Adam(), 
                           loss=['categorical_crossentropy', 'categorical_crossentropy'],
                           metrics=['accuracy'])

    def get_vector_stream(self):
        # stream of observations over 5 seconds
        self.observations = []
        for i in range(5):
            # returns list of booleans if attacker is active on a node
            attacker_activity = self.state.updateNetwork(self.network)
            self.observations.append(self.state.observationVector())
            sleep(1)
        
            # if not self.state.updateNetwork(self.network):
            #     self.observations.append(self.state.observationVector())
            #     sleep(1)

        return self.observations, attacker_activity

    def flatten_observation(self, obs):
        flattened = np.concatenate([
            np.array(obs['manipulated_values']),
            np.array(obs['node_state']).flatten(),
            np.array(obs['cowrie']),
            np.array(obs['fake_edge_deployed']),
            np.array(obs['fake_data']),
            np.array(obs['attacker_percieved_state']).flatten()
        ])
        return flattened

    def execute(self, node, action):
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
            print("no attacker activity")
        

    def choose_action(self, observation_vector):
        # flatten input 
        flattened_vector = self.flatten_observation(observation_vector)
        flattened_vector = flattened_vector.reshape((1, -1))
        
        # get the probabilities from the model
        host_probs, host_selection_sample, action_probs = self.model(flattened_vector)
        
        # normalize the probabilities to sum to 1
        # host_probs = host_probs.numpy().flatten()
        action_probs = action_probs.numpy().flatten()
        
        # # host_probs /= host_probs.sum()
        # action_probs /= action_probs.sum()

        host_selection_sample = host_selection_sample.numpy().flatten()
        
        # Get the chosen host from the sampled host selection
        chosen_host = np.argmax(host_selection_sample)

        action_mask = self.create_action_mask(chosen_host)

        # apply mask to action probabilities
        masked_action_probs = action_probs * action_mask

        # Normalize the masked probabilities
        masked_action_probs /= masked_action_probs.sum()

        # choose based on prob. dist.
        chosen_action = np.random.choice(len(masked_action_probs), p=masked_action_probs)
        
        print(f"chosen host: {chosen_host}, chosen action: {chosen_action}")
        self.execute(chosen_host, chosen_action)
    
    def create_action_mask(self, node):
        """
        Create an action mask for a given node based on its current state.
        Returns a list where each entry corresponds to whether an action is valid (1) or not (0).
        """
        state = self.state.nodes[node]
        action_mask = [1] * 7  # Assuming 7 possible actions
        
        if state["cowrie"]:
            action_mask[0] = 0  # Add fake node not allowed if cowrie is already True
        if state["fake_edge_deployed"]:
            action_mask[1] = 0  # Add fake edge not allowed if fake_edge_deployed is already True
        if state["fake_data"]:
            action_mask[2] = 0  # Add fake data not allowed if fake_data is already True
        
        if not state["cowrie"]:
            action_mask[3] = 0  # Remove fake node not allowed if cowrie is False
        if not state["fake_edge_deployed"]:
            action_mask[4] = 0  # Remove fake edge not allowed if fake_edge_deployed is False
        if not state["fake_data"]:
            action_mask[5] = 0  # Remove fake data not allowed if fake_data is False

        return np.array(action_mask)
    
    def run(self):
        
        while True:
            # keep track of how many consectuve time steps the attacker is inactive for policy trigger logic
            consecutive_attacker_absence = 0

            while True:
                # grabbing observation vector every 5 seconds
                observation_vector, empty_bool = self.get_vector_stream()

                # if there is attacker activity, trigger the policy network to take action, and continue to next time step observation
                if True in empty_bool:
                    print(f"input observation vector: {observation_vector[-1]}")
                    self.choose_action(observation_vector[-1])
                    consecutive_attacker_absence = 0
                    continue

                else:
                    consecutive_attacker_absence += 1
                    print("no attacker activity")
                    # if there is no attacker activity for 4 time steps while policy network is running, then stop it
                    if consecutive_attacker_absence >= 4:
                        print("stopping RL policy")
                        break

            print("RL policy stopped due to consecutive inactivity")
            continue

        

if __name__ == "__main__":
    defender = DefenderPolicy()
    defender.run()

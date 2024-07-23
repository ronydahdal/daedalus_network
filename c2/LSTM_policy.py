'''
This file implements a randomly initialized policy that is made up of three NN:
    1) LSTM layer that is fed a concatenation of a sequence of past observations and the current observation
    2) a NN that selects a host machine to take action on 
    3) a NN that selects an action to take on the chosen host (output of host NN is part of input for the action NN)

every 5 seconds:
    - pull observation vector
    - feed observation vector into network if it's triggered
    - embed past observations into input for LSTM layer and policy network
    - take chosen action on chosen node 
    - add observation into the sequence vector to be embedded next time step

TODO: Embedding logic:
'''
import sys
import threading
import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models, optimizers
from time import sleep
from observation_vector import NetworkState
from network import Network

def create_host_selection_network(num_hosts, input_shape):
    model = models.Sequential()
    model.add(layers.Dense(64, activation='relu', input_shape=(input_shape,)))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(num_hosts, activation='softmax'))  # curently, we are outputting prob dist. of 3 hosts
    return model

def create_action_selection_network(input_shape):
    model = models.Sequential()
    model.add(layers.Dense(64, activation='relu', input_shape=(input_shape,)))
    model.add(layers.Dense(32, activation='relu'))
    model.add(layers.Dense(7, activation='softmax'))  # 6 actions (we count 7 as we include doing nothing as the 7th action)
    return model

# combine the host NN and action NN with a preceding LSTM layer
class CombinedNetwork(tf.keras.Model):
    def __init__(self, num_hosts, input_shape, lstm_units=32):
        super(CombinedNetwork, self).__init__()
        # LSTM layer that expects (time steps, features), our "features" is the input shape of the observation
        self.lstm = layers.LSTM(lstm_units, activation='relu', return_state=True, input_shape=(None, input_shape))
        
        # feed LSTM output into the host NN. The input shape is the number of LSTM units
        self.host_selection_network = create_host_selection_network(num_hosts, lstm_units)

        # the input shape of the action NN is the LSTM shape and num_hosts as we feed output of LSTM and Host into action NN
        self.action_selection_network = create_action_selection_network(lstm_units + num_hosts)

    # each time step, we take input vector and state of past LSTM layer
    def call(self, inputs, states=None, training=False):
        if states is None:
            states = self.lstm.get_initial_state(inputs)

        lstm_output, state_h, state_c = self.lstm(inputs, initial_state=states)

        host_selection_output = self.host_selection_network(lstm_output)

        # take log probabilies returned from softmax and sample to select host (define only 1 sample)
        host_selection_sample = tf.random.categorical(tf.math.log(host_selection_output), 1)
        
        # one-hot encode the sample with the length of the host_selection_output
        host_selection_sample = tf.squeeze(tf.one_hot(host_selection_sample, host_selection_output.shape[-1]), axis=1)
        
        # action input is LSTM output and host NN output, so we concatenate them
        action_inputs = tf.concat([lstm_output, host_selection_sample], axis=-1)
        action_selection_output = self.action_selection_network(action_inputs)
        print(f"host selection: {host_selection_sample}")
        # print(f"action selection: {action_selection_output}")
        
        return host_selection_output, host_selection_sample, action_selection_output, [state_h, state_c]

# initialize the defender with the CombinedNetwork policy network
class DefenderPolicy:
    def __init__(self):
        # network object to take actions on the network
        self.network = Network()
        
        # networkState to observe the network 
        self.state = NetworkState(self.network.clients)
        
        # define the shape of observation vector (for each host), for the CombinedNetwork
        # 1 manipulated value + 3 node states + 1 cowrie + 1 fake edge deployed + 1 fake data + 4 attacker perceived states, for each host in network
        num_hosts = len(self.network.clients)
        observation_shape = (num_hosts * 1) + (num_hosts * 3) + (num_hosts * 1) + (num_hosts * 1) + (num_hosts * 1) + (num_hosts * 4)
        
        # Host input shape is the observation vector shape
        # Action input shape is the observation vector shape + host selection output shape
        # there is a hidden third parameter here, lstm_units, which is defaulted to 32 units
        self.model = CombinedNetwork(num_hosts, observation_shape)
        
        self.model.compile(optimizer=optimizers.Adam(), 
                           loss=['categorical_crossentropy', 'categorical_crossentropy'],
                           metrics=['accuracy'])
        
        self.lstm_state = None

        self.stop_thread = False
        self.listener_thread = threading.Thread(target=self.listen_for_stop)
        self.listener_thread.start()

    def get_vector_stream(self):
        # stream of observations over 5 seconds for 10 observation vector
        self.observations = []
        for i in range(10):
            # returns list of booleans if attacker is active on a node
            attacker_activity = self.state.updateNetwork(self.network)
            self.observations.append(self.state.observationVector())
            sleep(5)
        return self.observations, attacker_activity

    # returns a single observation 
    def get_vector(self):
        attacker_activity = self.state.updateNetwork(self.network)
        observation = self.state.observationVector()
        return observation, attacker_activity

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
        

    def choose_action(self, current_observation):
        # flatten current observation vector 
        flattened_vector = self.flatten_observation(current_observation).reshape((1, 1, -1))

        # if len(self.observation_sequence) > 0:
        #     # reshape the sequence to the same shape as LSTM input, (batch_size, time_steps, features)
        #     # batch_size is 1, time_steps is length of sequence as that's how many time steps we've taken, and -1 tells numpy to infer size
        #     input_sequence = np.array(self.observation_sequence).reshape(1, len(self.observation_sequence), -1) 

        #     # LSTM requires 3D shape (batch_size, time_steps, features), so we add a new axis to current observation
        #     # and concatenate with input_sequence, which is already 3D 
        #     embedded_vector = np.concatenate((input_sequence, flattened_vector[np.newaxis, :]), axis=1)

        # # if observation sequence is empty, use only the current observation 
        # # reshape it to 3D so that the LSTM so that it's valid input to the LSTM layer
        # else:
        #     embedded_vector = flattened_vector[np.newaxis, :]

        # if we are starting the network and there is no saved state, we start with 2 zero vectors that are the same size as the LSTM_units (here it's 32)

        if self.lstm_state is None:
            self.lstm_state = [tf.zeros((1, 32)), tf.zeros((1, 32))]
        
        print(self.lstm_state)

        # get the probabilities and output from the model
        host_probs, host_selection_sample, action_probs, new_lstm_state = self.model(flattened_vector, states=self.lstm_state)
        
        # update LSTM state
        self.lstm_state = new_lstm_state

        print(self.lstm_state)
        
        # normalize the probabilities to sum to 1
        # host_probs = host_probs.numpy().flatten()
        action_probs = action_probs.numpy().flatten()
        
        host_selection_sample = host_selection_sample.numpy().flatten()
        
        # Get the chosen host from the sampled host selection
        chosen_host = np.argmax(host_selection_sample)

        # make action mask based on the chosen host (what actions are allowed)
        action_mask = self.create_action_mask(chosen_host)

        # apply mask to action probabilities
        masked_action_probs = action_probs * action_mask

        # for the sake of debug, this should never happen as once we start an action, we should be able to do it's counterpart
        if masked_action_probs.sum() == 0:
            print("all actions are masked out, defaulting to 'do nothing'.")
            masked_action_probs = action_mask

        # Normalize the masked probabilities
        masked_action_probs /= masked_action_probs.sum()

        print(f"masked_action_probs after normalization: {masked_action_probs}")

        # choose based on prob. dist.
        chosen_action = np.random.choice(len(masked_action_probs), p=masked_action_probs)
        
        print(f"chosen host: {chosen_host}, chosen action: {chosen_action}")
        self.execute(chosen_host, chosen_action)

        # # add current observation to sequence to be embedded for next iteration
        # self.update_observation_sequence(current_observation) 
    
    def update_observation_sequence(self, observation_vector):
        flattened_vector = self.flatten_observation(observation_vector)
        self.observation_sequence.append(flattened_vector)
        if len(self.observation_sequence) > 10:  # Keep only the last 10 observations
            self.observation_sequence.pop(0)
    
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
    
    # function to know when to stop the defensive agent and reset all the defensive actions
    def listen_for_stop(self):
        while True:
            user_input = input()
            if user_input == "stop":
                self.stop_thread = True
                break

    def run(self):
        # defender is initially off
        self.trigger = False

        # if user has not stopped -- this is to manually stop the defender from observing the network when "stop" is typed into command line
        while not self.stop_thread:
            # keep track of how many consectuve time steps the attacker is inactive for policy trigger logic
            self.consecutive_attacker_absence = 0

            # grab observation of network and check if it's empty
            observation_vector, empty_bool = self.get_vector()
            
            # if there is attacker activity in the observation, trigger the policy network to take action, and continue to next time step observation
            if True in empty_bool:
                self.consecutive_attacker_absence = 0
                self.trigger = True

            # if there is no attacker activity, check how many consecutive times it's been empty
            else:
                self.consecutive_attacker_absence += 1
                print(f"no attacker activity, consecutive attacker absences: {self.consecutive_attacker_absence}") 

                # if there is no attacker activity for 10 consecutive time steps, then don't send to policy
                if self.consecutive_attacker_absence >= 10:
                    self.trigger = False

                # if it's less than 10 consecutive time steps, still send empty observation to policy 
                else:
                    self.trigger = True
            
            # if trigger is on, send observastion to policy network
            if self.trigger == True:          
                print(f"input observation vector: {observation_vector}")
                # print(f"input observation sequence: {self.observation_sequence}")
                # print(f"length of observation sequence: {len(self.observation_sequence)}")
                self.choose_action(observation_vector)
            
            else: 
                print("RL policy network off, 10 or more consecutive empty vectors")

            # time step is 5 seconds
            sleep(5)
        
        # reset defensive actions when user interrupts
        self.network.eradicate()
        print("Defender stopping: machines defensive actions reset")
        self.listener_thread.join()

        return

        
if __name__ == "__main__":
    defender = DefenderPolicy()
    defender.run()

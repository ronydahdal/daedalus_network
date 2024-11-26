from c2.network import Network
from c2.observation_vector import NetworkState
from NetworkEnv import NetworkEnvInterface
from force.force.alg.mbpo import MBPO
from force.force.config import Config
import json
import numpy as np

# Load MBPO json configuration
# this loads in rollout schedule, hyperparameters, etc
with open("mbpo_config.json", "r") as f:
    config = Config(json.load(f))

# Initialize the network and state (for observations)
network = Network()
state = NetworkState(network.clients)

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

# Wrap network and state in the environment interface
env_interface = NetworkEnvInterface(network, state)

#  MBPO agent
agent = MBPO(
    cfg=config,
    obs_space=len(env_interface.reset()),  # Use observation vector length
    act_space=7,  # Total number of possible actions
    device="cuda"  # Use GPU if available
)

# Initialize the agent's replay buffer
agent.replay_buffer.extend({
    "observations": [],
    "actions": [],
    "next_observations": [],
    "rewards": [],
    "terminals": [],
})

# training 
# do we train only when attackers are present?
for epoch in range(100):  
    observation = env_interface.reset() # reset state, using eradicate function
    # flattened and reshaped observation vector (did something similar in our random LSTM policy)
    flat_observation = flatten_observation(observation) # collect intial observation
    reshaped_observation = flat_observation.reshape((1, -1))
    done = False
    
    # this while loop trains when attackers are present
    while not done:
        # select action from the agent
        host_selection, _, action_probs = agent.act(reshaped_observation, eval=False)
        action = action_probs.argmax()  # Choose the action with the highest probability
        
        # extract node selected
        node = host_selection.argmax()
        
        # take action in AWS (step) and tranform the following observation
        next_observation, reward, done = env_interface.step(node, action)
        flat_next_observation = flatten_observation(next_observation)
        reshaped_next_observation = flat_next_observation.reshape((1, -1))
        
        # store transition in the replay buffer
        agent.replay_buffer.add(
            observations=reshaped_observation,
            actions=action,
            next_observations=reshaped_next_observation,
            rewards=reward,
            terminals=done,
        )
        
        # update observation for the next step
        reshaped_observation = reshaped_next_observation
    
    # train/update agent
    agent.update(counters={"updates": epoch})
    print(f"Epoch {epoch} completed.")

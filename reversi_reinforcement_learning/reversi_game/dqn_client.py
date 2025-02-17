#!/usr/bin/env python3
import sys
import time
import json
import random
import collections

import zmq
import torch
import torch.nn as nn
import torch.optim as optim
import torch.nn.functional as F

# Constants for Reversi
EMPTY = 0
BLACK = 1
WHITE = 2
BOARD_SIZE = 8

SLEEP_TIME = 1e-2

# We'll define a pass action index as 64
PASS_IDX = 64
# So the total number of actions is 64 squares + 1 pass
NUM_ACTIONS = 65

def usage():
    print(f"Usage: python {sys.argv[0]} BLACK|WHITE")
    sys.exit(1)

# -----------------------------------------
#   Simple Replay Buffer
# -----------------------------------------
class ReplayBuffer:
    def __init__(self, capacity=10000):
        self.buffer = collections.deque(maxlen=capacity)

    def push(self, state, action, reward, next_state, done):
        self.buffer.append((state, action, reward, next_state, done))

    def sample(self, batch_size):
        batch = random.sample(self.buffer, batch_size)
        states, actions, rewards, next_states, dones = zip(*batch)
        return states, actions, rewards, next_states, dones

    def __len__(self):
        return len(self.buffer)

# -----------------------------------------
#   DQN Network
# -----------------------------------------
class DQN(nn.Module):
    """
    A simple feed-forward network that inputs a flattened 8x8 board (64 dims)
    and outputs Q-values for each of the 64 squares **plus 1 pass action**.
    So the output_dim = 65 => indices [0..63] = squares, 64 = pass.
    """
    def __init__(self, input_dim=64, hidden_dim=128, output_dim=NUM_ACTIONS):
        super(DQN, self).__init__()
        self.fc1 = nn.Linear(input_dim, hidden_dim)
        self.fc2 = nn.Linear(hidden_dim, hidden_dim)
        self.fc3 = nn.Linear(hidden_dim, output_dim)

    def forward(self, x):
        # x shape: [batch_size, 64]
        x = F.relu(self.fc1(x))
        x = F.relu(self.fc2(x))
        q_values = self.fc3(x)  # shape [batch_size, 65]
        return q_values

# -----------------------------------------
#  Helper Functions
# -----------------------------------------
def flatten_board(board_2d):
    """
    Flatten an 8x8 board into a list/tensor of length 64.
    We'll keep it simple: 0=EMPTY, 1=BLACK, 2=WHITE (or you can remap).
    """
    flat = []
    for row in board_2d:
        flat.extend(row)
    return flat

def get_valid_actions(board_2d, player):
    """
    Return a list of (row,col) squares that are valid moves for 'player'.
    If empty, the agent might pass.
    """
    opp = WHITE if player == BLACK else BLACK
    directions = [(-1,0),(1,0),(0,-1),(0,1),
                  (-1,-1),(-1,1),(1,-1),(1,1)]
    moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board_2d[r][c] != EMPTY:
                continue
            valid = False
            for (dr, dc) in directions:
                rr, cc = r+dr, c+dc
                found_opp = False
                while 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board_2d[rr][cc] == opp:
                    found_opp = True
                    rr += dr
                    cc += dc
                if found_opp and 0 <= rr < BOARD_SIZE and 0 <= cc < BOARD_SIZE and board_2d[rr][cc] == player:
                    valid = True
                    break
            if valid:
                moves.append((r, c))
    return moves

def to_tensor(board_flat):
    """
    Convert a list of 64 ints into a 1D FloatTensor for PyTorch.
    shape = (1, 64)
    """
    return torch.FloatTensor(board_flat).unsqueeze(0)

def action_to_rc(action_idx):
    """
    Convert a single integer 0..63 into (row,col).
    64 => pass
    """
    if action_idx == PASS_IDX:
        return (-1, -1)
    r = action_idx // BOARD_SIZE
    c = action_idx % BOARD_SIZE
    return (r, c)

def rc_to_action(r, c):
    """
    Convert (row,col) in [0..7] to single integer 0..63
    If r<0 => pass => action=64
    """
    if r < 0 or c < 0:
        return PASS_IDX
    return r * BOARD_SIZE + c

# -----------------------------------------
#  DQN Client
# -----------------------------------------
class DQNAgent:
    def __init__(self, color=BLACK, epsilon=0.2, lr=1e-3, gamma=0.99,
                 buffer_capacity=10000, batch_size=32):
        self.color = color
        self.epsilon = epsilon
        self.gamma = gamma
        self.batch_size = batch_size

        # We'll produce 65 Q-values => 64 squares + 1 pass
        self.policy_net = DQN()
        self.target_net = DQN()
        self.target_net.load_state_dict(self.policy_net.state_dict())
        self.target_net.eval()

        self.optimizer = optim.Adam(self.policy_net.parameters(), lr=lr)
        self.replay_buffer = ReplayBuffer(capacity=buffer_capacity)

        self.update_steps = 0
        self.update_target_every = 1000

    def select_action(self, board_2d, current_player):
        """
        Epsilon-greedy among 65 actions:
         - 0..63 => squares
         - 64 => pass
        We'll mask out squares not in valid_moves. Pass is always possible.
        """
        state_flat = flatten_board(board_2d)
        state_t = to_tensor(state_flat)  # shape (1,64)

        with torch.no_grad():
            q_values = self.policy_net(state_t)[0]  # shape (65,)

        valid = get_valid_actions(board_2d, current_player)
        valid_idxs = [r*BOARD_SIZE + c for (r,c) in valid]

        # pass is always an option
        valid_idxs.append(PASS_IDX)

        if random.random() < self.epsilon:
            # random from valid_idxs
            return random.choice(valid_idxs)
        else:
            # mask out invalid squares (not in valid_idxs)
            masked_q = q_values.clone()
            for i in range(NUM_ACTIONS):
                if i not in valid_idxs:
                    masked_q[i] = -999999.0
            best_idx = torch.argmax(masked_q).item()
            return best_idx

    def push_transition(self, state_flat, action_idx, reward, next_state_flat, done):
        self.replay_buffer.push(state_flat, action_idx, reward, next_state_flat, done)

    def train_step(self):
        if len(self.replay_buffer) < self.batch_size:
            return
        states, actions, rewards, next_states, dones = self.replay_buffer.sample(self.batch_size)

        states_t = torch.FloatTensor(states)       # shape (B,64)
        actions_t = torch.LongTensor(actions)      # shape (B,)
        rewards_t = torch.FloatTensor(rewards)     # shape (B,)
        next_states_t = torch.FloatTensor(next_states)
        dones_t = torch.BoolTensor(dones)          # shape (B,)

        # Q(s,a)
        q_values = self.policy_net(states_t)       # shape (B,65)
        gather_q = q_values.gather(1, actions_t.unsqueeze(1)).squeeze(1)  # shape (B,)

        with torch.no_grad():
            next_q = self.target_net(next_states_t)    # shape (B,65)
            max_next_q = torch.max(next_q, dim=1)[0]   # shape (B,)

        target = rewards_t + (1.0 - dones_t.float()) * self.gamma * max_next_q

        loss = F.mse_loss(gather_q, target)

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

        self.update_steps += 1
        if self.update_steps % self.update_target_every == 0:
            self.target_net.load_state_dict(self.policy_net.state_dict())



def main():
    if len(sys.argv) < 2:
        usage()
    color_str = sys.argv[1].upper()
    if color_str not in ["BLACK", "WHITE"]:
        usage()

    player_color = BLACK if color_str == "BLACK" else WHITE

    # Hyperparams
    epsilon = 0.2
    gamma = 0.99
    lr = 1e-3
    batch_size = 32

    agent = DQNAgent(color=player_color, epsilon=epsilon, lr=lr,
                     gamma=gamma, batch_size=batch_size)

    # ZMQ setup
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:5555")
    print(f"[DQN Client] Controlling {color_str}. Connected to server.")

    episode_count = 0
    step_count = 0

    try:
        while True:
            # 1) GET_BOARD
            socket.send_string("GET_BOARD")
            reply = socket.recv_string()
            data = json.loads(reply)
            board_2d = data["board"]
            current_player = data["current_player"]

            # Check if it's our turn
            if current_player != player_color:
                # not our turn => wait a bit, then re-check
                time.sleep(SLEEP_TIME)
                continue

            # 2) Epsilon-greedy DQN selection
            state_flat = flatten_board(board_2d)  # shape (64)
            action_idx = agent.select_action(board_2d, current_player)

            # Convert to row,col
            row, col = action_to_rc(action_idx)

            # 3) Send the move
            color_str2 = "BLACK" if player_color == BLACK else "WHITE"
            msg = f"{color_str2} MOVE {row} {col}"
            socket.send_string(msg)
            reply = socket.recv_string()

            if reply.startswith("OK:MOVE"):
                # For partial step => reward=0
                # Next GET_BOARD => next_state
                socket.send_string("GET_BOARD")
                next_reply = socket.recv_string()
                next_data = json.loads(next_reply)
                next_board_2d = next_data["board"]
                next_player = next_data["current_player"]

                next_state_flat = flatten_board(next_board_2d)

                agent.push_transition(state_flat, action_idx, 0.0, next_state_flat, False)
                agent.train_step()
                step_count += 1

            elif reply.startswith("ERR:ILLEGAL_MOVE"):
                # Possibly out of sync. We'll do a "GET_BOARD" next loop
                # No Q update for an illegal move
                time.sleep(SLEEP_TIME)

            elif reply.startswith("ERR:NOT_YOUR_TURN"):
                # The server says it's the other color
                time.sleep(SLEEP_TIME)

            elif reply.startswith("GAME_OVER"):
                parts = reply.split()
                bscore = int(parts[1])
                wscore = int(parts[2])

                # final reward
                if bscore > wscore:
                    final_reward = 1.0 if player_color == BLACK else -1.0
                elif wscore > bscore:
                    final_reward = 1.0 if player_color == WHITE else -1.0
                else:
                    final_reward = 0.0

                # push final transition
                dummy_next = [0]*64
                agent.push_transition(state_flat, action_idx, final_reward, dummy_next, True)
                agent.train_step()

                episode_count += 1
                print(f"[DQN Client] GAME_OVER => B:{bscore}, W:{wscore}, final_reward={final_reward}, episodes={episode_count}")

            elif reply.startswith("OK:QUIT"):
                print("[DQN Client] Server asked to quit. Exiting.")
                break
            else:
                print("[DQN Client] Unhandled reply:", reply)
                time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        print("[DQN Client] Interrupted by user.")
    finally:
        socket.close()
        context.term()
        # Optionally save the model
        torch.save(agent.policy_net.state_dict(), "dqn_reversi.pth")
        print("[DQN Client] Saved model and shutting down.")


if __name__ == "__main__":
    main()

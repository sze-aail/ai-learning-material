#!/usr/bin/env python3
import zmq
import json
import sys
import time
import random

# Constants
EMPTY = 0
BLACK = 1
WHITE = 2
BOARD_SIZE = 8

SLEEP_TIME = 1e-2

def usage():
    print(f"Usage: python {sys.argv[0]} BLACK|WHITE")
    sys.exit(1)

def pick_random_move(board_2d, my_color):
    """
    Example: pick any valid move at random.
    A real Q-learning approach would pick an action from Q-table (epsilon-greedy).
    """
    valid_moves = get_valid_actions(board_2d, my_color)
    if not valid_moves:
        return (-1, -1)  # pass
    return random.choice(valid_moves)

def get_valid_actions(board_2d, player):
    """
    Local function to identify valid moves by scanning the server's board data.
    If you'd prefer to let the server handle validity, you can just guess moves,
    but typically you'd want the set of valid moves for Q-learning's action space.
    """
    moves = []
    opp = WHITE if player == BLACK else BLACK
    directions = [(-1,0), (1,0), (0,-1), (0,1),
                  (-1,-1), (-1,1), (1,-1), (1,1)]
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board_2d[r][c] != EMPTY:
                continue
            valid = False
            for dr, dc in directions:
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

def main():
    if len(sys.argv) < 2:
        usage()

    color_str = sys.argv[1].upper()
    if color_str not in ["BLACK", "WHITE"]:
        usage()

    my_color = BLACK if color_str == "BLACK" else WHITE

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:5555")

    print(f"[Q-Learning Client] Controlling {color_str}.")
    print("Ensure your server supports GET_BOARD and can respond with 'GAME_OVER ...'.")

    episode_count = 0
    running = True

    try:
        while running:
            # 1) Ask the server for the current board + whose turn it is
            socket.send_string("GET_BOARD")
            board_reply = socket.recv_string()  # BLOCKING
            data = json.loads(board_reply)  # => {"board": [...], "current_player": int}

            board_2d = data["board"]
            current_player = data["current_player"]

            # 2) Check if it's our turn
            if current_player == my_color:
                # (A) Pick a move (random or from Q-learning policy)
                row, col = pick_random_move(board_2d, my_color)

                # (B) Send the MOVE command
                cmd = f"{color_str} MOVE {row} {col}"
                socket.send_string(cmd)
                reply = socket.recv_string()  # BLOCKING

                if reply.startswith("OK:MOVE"):
                    # Move accepted
                    # Insert your Q-learning "intermediate" update here if desired (reward=0)
                    pass

                elif reply.startswith("ERR:ILLEGAL_MOVE"):
                    # We tried an invalid move; server refused
                    print("[CLIENT] Illegal move. We'll try again next loop.")
                    # You might want to do a negative reward, or just ignore
                    time.sleep(SLEEP_TIME)

                elif reply.startswith("ERR:NOT_YOUR_TURN"):
                    # Possibly the other side has moves; try again soon
                    print("[CLIENT] Not our turn? Strange. We'll wait.")
                    time.sleep(SLEEP_TIME)

                elif reply.startswith("GAME_OVER"):
                    # Format: "GAME_OVER 35 29" (black_score, white_score)
                    parts = reply.split()
                    black_score = parts[1]
                    white_score = parts[2]
                    print(f"[CLIENT] Game Over => Black:{black_score}, White:{white_score}")
                    # Insert final Q-learning reward update if you want (+1 for win, etc.)
                    episode_count += 1
                    print(f"[CLIENT] Episode finished. Count={episode_count}.")
                    # The server resets the board automatically. We continue the loop for a new game.

                else:
                    print("[CLIENT] Unhandled reply:", reply)
                    time.sleep(1.0)

            else:
                # Not our turn => do nothing or wait briefly
                # The server might rotate turns, so we check again soon
                time.sleep(SLEEP_TIME)

    except KeyboardInterrupt:
        print("[CLIENT] Stopped by user.")
    finally:
        print("[CLIENT] Exiting. Episodes completed:", episode_count)
        socket.close()
        context.destroy()

if __name__ == "__main__":
    main()

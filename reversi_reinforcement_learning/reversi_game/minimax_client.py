#!/usr/bin/env python3
import zmq
import sys
import math
import json
import time

BOARD_SIZE = 8

EMPTY = 0
BLACK = 1
WHITE = 2

SLEEP_TIME = 1e-2

def usage():
    print(f"Usage: python {sys.argv[0]} BLACK|WHITE")
    sys.exit(1)

# ----------------------------------------
#       Local Reversi Representation
# ----------------------------------------
class ReversiBoard:
    def __init__(self):
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        self.current_player = BLACK  # default

    def load_from_json(self, board_2d, current_player):
        """Set local board from the server's JSON data."""
        self.board = board_2d
        self.current_player = current_player

    def copy(self):
        newb = ReversiBoard()
        newb.board = [row[:] for row in self.board]
        newb.current_player = self.current_player
        return newb

    def get_opponent(self, player):
        return WHITE if player == BLACK else BLACK

    def in_bounds(self, r, c):
        return (0 <= r < BOARD_SIZE) and (0 <= c < BOARD_SIZE)

    def valid_moves(self, player):
        moves = []
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if self.is_valid_move(r, c, player):
                    moves.append((r, c))
        return moves

    def is_valid_move(self, row, col, player):
        if self.board[row][col] != EMPTY:
            return False
        opp = self.get_opponent(player)
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        found_valid = False
        for dr, dc in directions:
            rr, cc = row+dr, col+dc
            found_opp = False
            while self.in_bounds(rr, cc) and self.board[rr][cc] == opp:
                found_opp = True
                rr += dr
                cc += dc
            if found_opp and self.in_bounds(rr, cc) and self.board[rr][cc] == player:
                found_valid = True
                break
        return found_valid

    def place_disc(self, row, col, player):
        if not self.is_valid_move(row, col, player):
            return False
        self.board[row][col] = player
        opp = self.get_opponent(player)
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        for dr, dc in directions:
            rr, cc = row+dr, col+dc
            flip_list = []
            while self.in_bounds(rr, cc) and self.board[rr][cc] == opp:
                flip_list.append((rr, cc))
                rr += dr
                cc += dc
            if self.in_bounds(rr, cc) and self.board[rr][cc] == player and flip_list:
                for (fr, fc) in flip_list:
                    self.board[fr][fc] = player
        return True

    def get_scores(self):
        black_count = sum(row.count(BLACK) for row in self.board)
        white_count = sum(row.count(WHITE) for row in self.board)
        return black_count, white_count

# ----------------------------------------
#   Minimax with Alpha-Beta
# ----------------------------------------
def evaluate_board(board: ReversiBoard):
    """Simple: #black - #white."""
    b, w = board.get_scores()
    return b - w

def alpha_beta(board: ReversiBoard, player, depth, alpha, beta, maximizing):
    # We might skip checking "game_over" here, because Othello can require skipping turns
    if depth == 0:
        return evaluate_board(board), None

    moves = board.valid_moves(player)
    if not moves:
        # No moves => "pass"
        return evaluate_board(board), None

    best_move = None

    if maximizing:
        value = -math.inf
        for (r, c) in moves:
            newb = board.copy()
            newb.place_disc(r, c, player)
            # Next turn is opponent
            score, _ = alpha_beta(newb, newb.get_opponent(player),
                                  depth - 1, alpha, beta, False)
            if score > value:
                value = score
                best_move = (r, c)
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value, best_move
    else:
        value = math.inf
        for (r, c) in moves:
            newb = board.copy()
            newb.place_disc(r, c, player)
            # Next turn
            score, _ = alpha_beta(newb, newb.get_opponent(player),
                                  depth - 1, alpha, beta, True)
            if score < value:
                value = score
                best_move = (r, c)
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

def choose_minimax_move(board: ReversiBoard, color, depth=3):
    """Return (row,col) that minimax suggests, or None if no moves."""
    maximizing = (color == BLACK)  # black tries to maximize board eval
    _, best_move = alpha_beta(board, color, depth, -math.inf, math.inf, maximizing)
    return best_move

# ----------------------------------------
#         Minimax Client Code
# ----------------------------------------
def main():
    if len(sys.argv) < 2:
        usage()

    color_str = sys.argv[1].upper()
    if color_str not in ["BLACK", "WHITE"]:
        usage()

    player_color = BLACK if color_str == "BLACK" else WHITE

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:5555")
    print(f"[CLIENT] Minimax controlling {color_str}. Connected to server.")

    local_board = ReversiBoard()

    # A helper to get board from server
    def get_board_from_server():
        socket.send_string("GET_BOARD")
        reply = socket.recv_string()
        data = json.loads(reply)  # data = {"board": [[...],[...]], "current_player": 1 or 2}
        local_board.load_from_json(data["board"], data["current_player"])
        print("[CLIENT] Synchronized board. Current player on server is:",
              "BLACK" if data["current_player"] == BLACK else "WHITE")

    # 1) On startup, always GET_BOARD so we know the initial state
    get_board_from_server()

    try:
        while True:
            # If it's not our turn, we simply wait a moment, then refresh board
            if local_board.current_player != player_color:
                # Just poll the server to see if anything changed
                time.sleep(SLEEP_TIME)
                get_board_from_server()
                continue

            # It's our turn => compute a minimax move
            move = choose_minimax_move(local_board, player_color, depth=3)
            if move is None:
                # No moves => pass
                row, col = -1, -1
            else:
                (row, col) = move

            # Send the move command
            msg = f"{color_str} MOVE {row} {col}"
            socket.send_string(msg)
            reply = socket.recv_string()

            if reply.startswith("OK:MOVE"):
                # We apply it locally
                local_board.place_disc(row, col, player_color)
                # But we don't know if the server changed current_player internally
                # => Re-get the board to sync
                get_board_from_server()

            elif reply.startswith("ERR:NOT_YOUR_TURN"):
                print("[CLIENT] Not our turn? We'll re-sync the board.")
                get_board_from_server()

            elif reply.startswith("ERR:ILLEGAL_MOVE"):
                print("[CLIENT] Move was illegal? Possibly out of sync. Re-sync.")
                get_board_from_server()

            elif reply.startswith("GAME_OVER"):
                # e.g. "GAME_OVER 32 30"
                parts = reply.split()
                bscore = parts[1]
                wscore = parts[2]
                print(f"[CLIENT] GAME_OVER from server. Final Score => B:{bscore}, W:{wscore}")
                print("[CLIENT] Starting a new game (server auto-reset).")
                # Re-get the board => it should now be in the initial state
                get_board_from_server()

            elif reply.startswith("OK:QUIT"):
                print("[CLIENT] Server requested quit. Exiting.")
                break

            else:
                print("[CLIENT] Unhandled reply:", reply)
                #time.sleep(1.0)
                # Attempt to re-sync
                get_board_from_server()

    except KeyboardInterrupt:
        print("[CLIENT] Interrupted by user.")
    finally:
        # Optionally tell server QUIT if you want to shut it down
        # socket.send_string("QUIT")
        # _ = socket.recv_string()
        socket.close()
        context.term()

if __name__ == "__main__":
    main()

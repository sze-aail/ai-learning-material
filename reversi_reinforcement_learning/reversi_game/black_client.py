import zmq
import random
import time

class BlackPlayerClient:
    def __init__(self, server_address="tcp://localhost:5555"):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(server_address)

    def get_valid_moves(self):
        """Retrieve the board state and find valid moves."""
        self.socket.send_json({"command": "get_ai_state"})
        board_state = self.socket.recv_json()["state"]

        valid_moves = []
        for row in range(len(board_state)):
            for col in range(len(board_state[row])):
                if board_state[row][col] == 0:  # Empty cell
                    valid_moves.append((row, col))
        return valid_moves

    def play_move(self):
        """Choose a random move and play it."""
        valid_moves = self.get_valid_moves()
        if not valid_moves:
            print("No valid moves left for Black.")
            return

        row, col = random.choice(valid_moves)
        self.socket.send_json({"command": "place", "row": row, "col": col})
        response = self.socket.recv_json()
        print(f"Black played at ({row}, {col}): {response['status']}")

if __name__ == "__main__":
    black_player = BlackPlayerClient()
    while True:
        black_player.play_move()
        time.sleep(2)  # Adjust timing as needed

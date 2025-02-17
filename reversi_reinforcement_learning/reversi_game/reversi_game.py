#!/usr/bin/env python3
import pygame
import sys
import zmq
import json
from pygame.locals import *

# ----------------------------------------
#             CONSTANTS
# ----------------------------------------
BOARD_SIZE = 8
TILE_SIZE = 60
WINDOW_SIZE = BOARD_SIZE * TILE_SIZE
FPS = 30

EMPTY = 0
BLACK = 1
WHITE = 2

GREEN = (34, 139, 34)
BLACK_COLOR = (0, 0, 0)
WHITE_COLOR = (255, 255, 255)

# ----------------------------------------
#        REVERSI GAME LOGIC
# ----------------------------------------
class ReversiGame:
    def __init__(self):
        self.reset()

    def reset(self):
        """Reset the board to the initial state."""
        self.board = [[EMPTY]*BOARD_SIZE for _ in range(BOARD_SIZE)]
        mid = BOARD_SIZE // 2
        self.board[mid-1][mid-1] = WHITE
        self.board[mid][mid]     = WHITE
        self.board[mid-1][mid]   = BLACK
        self.board[mid][mid-1]   = BLACK
        self.current_player = BLACK

    def in_bounds(self, r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def get_opponent(self, player):
        return BLACK if player == WHITE else WHITE

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
        for dr, dc in directions:
            rr, cc = row + dr, col + dc
            found_opp = False
            while self.in_bounds(rr, cc) and self.board[rr][cc] == opp:
                found_opp = True
                rr += dr
                cc += dc
            if found_opp and self.in_bounds(rr, cc) and self.board[rr][cc] == player:
                return True
        return False

    def place_disc(self, row, col, player):
        """Attempt to place a disc; flip discs if valid."""
        if not self.is_valid_move(row, col, player):
            return False

        self.board[row][col] = player
        opp = self.get_opponent(player)
        directions = [
            (-1, 0), (1, 0), (0, -1), (0, 1),
            (-1, -1), (-1, 1), (1, -1), (1, 1)
        ]
        for dr, dc in directions:
            rr, cc = row + dr, col + dc
            flip_list = []
            while self.in_bounds(rr, cc) and self.board[rr][cc] == opp:
                flip_list.append((rr, cc))
                rr += dr
                cc += dc
            if self.in_bounds(rr, cc) and self.board[rr][cc] == player and flip_list:
                for (fr, fc) in flip_list:
                    self.board[fr][fc] = player
        return True

    def next_player(self):
        self.current_player = self.get_opponent(self.current_player)

    def is_game_over(self):
        """Game over if neither current_player nor opponent has a valid move."""
        if self.valid_moves(self.current_player):
            return False
        if self.valid_moves(self.get_opponent(self.current_player)):
            return False
        return True

    def get_scores(self):
        black_score = sum(row.count(BLACK) for row in self.board)
        white_score = sum(row.count(WHITE) for row in self.board)
        return black_score, white_score

# ----------------------------------------
#        PYGAME DRAWING
# ----------------------------------------
def draw_board(screen, game):
    screen.fill(GREEN)
    for x in range(1, BOARD_SIZE):
        pygame.draw.line(screen, BLACK_COLOR, (x*TILE_SIZE, 0),
                         (x*TILE_SIZE, WINDOW_SIZE), 2)
        pygame.draw.line(screen, BLACK_COLOR, (0, x*TILE_SIZE),
                         (WINDOW_SIZE, x*TILE_SIZE), 2)
    # Discs
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            piece = game.board[r][c]
            if piece != EMPTY:
                center = (c*TILE_SIZE + TILE_SIZE//2, r*TILE_SIZE + TILE_SIZE//2)
                color = BLACK_COLOR if piece == BLACK else WHITE_COLOR
                pygame.draw.circle(screen, color, center, TILE_SIZE//2 - 2)

    # Title
    player_str = "Black" if game.current_player == BLACK else "White"
    pygame.display.set_caption(f"Reversi - Current: {player_str}")

# ----------------------------------------
#        SERVER (REQ/REP) LOOP
# ----------------------------------------
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    clock = pygame.time.Clock()

    context = zmq.Context()
    socket = context.socket(zmq.REP)
    socket.bind("tcp://*:5555")

    print("Server started on tcp://*:5555")

    game = ReversiGame()

    # Track if game is over; reset after next move request
    game_over_flag = False
    final_black = 0
    final_white = 0

    running = True
    while running:
        # 1) Handle window close
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

        # 2) If game isn't over yet, check if current player must auto-pass
        if not game_over_flag:
            # If current player has no valid moves, auto-pass
            if not game.valid_moves(game.current_player):
                game.next_player()
                # After passing, check if the new current player also has no moves => game over
                if game.is_game_over():
                    final_black, final_white = game.get_scores()
                    game_over_flag = True

        # 3) If the game just became over
        if not game_over_flag and game.is_game_over():
            final_black, final_white = game.get_scores()
            game_over_flag = True

        # 4) Non-blocking poll for incoming requests
        event_mask = socket.poll(timeout=0, flags=zmq.POLLIN)
        if event_mask & zmq.POLLIN:
            msg = socket.recv_string(zmq.NOBLOCK)
            parts = msg.strip().split()
            reply = "INVALID"

            if len(parts) >= 1:
                cmd = parts[0].upper()

                # 4a) GET_BOARD
                if cmd == "GET_BOARD":
                    data = {
                        "board": game.board,
                        "current_player": game.current_player
                    }
                    reply = json.dumps(data)
                    socket.send_string(reply)

                # 4b) QUIT
                elif cmd == "QUIT":
                    reply = "OK:QUIT"
                    socket.send_string(reply)
                    running = False

                # 4c) <COLOR> MOVE row col
                elif len(parts) == 4 and parts[1].upper() == "MOVE":
                    color_str = parts[0].upper()
                    row = int(parts[2])
                    col = int(parts[3])

                    # If game is over, respond once with GAME_OVER, then reset
                    if game_over_flag:
                        reply = f"GAME_OVER {final_black} {final_white}"
                        socket.send_string(reply)
                        game.reset()
                        game_over_flag = False
                        final_black = 0
                        final_white = 0
                        continue

                    # Otherwise, process move
                    player = BLACK if color_str == "BLACK" else WHITE
                    if player != game.current_player:
                        reply = "ERR:NOT_YOUR_TURN"
                    else:
                        if game.place_disc(row, col, player):
                            game.next_player()  # switch after successful move
                            reply = "OK:MOVE"
                        else:
                            reply = "ERR:ILLEGAL_MOVE"
                    socket.send_string(reply)

                else:
                    reply = "ERR:UNKNOWN_COMMAND"
                    socket.send_string(reply)

        # 5) Update the display
        draw_board(screen, game)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    context.destroy()
    sys.exit()

if __name__ == "__main__":
    main()

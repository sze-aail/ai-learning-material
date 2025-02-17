#!/usr/bin/env python3
import zmq
import time
import sys
import random

def main(player_color):
    """
    player_color should be 'BLACK' or 'WHITE'.
    The client randomly selects row,col moves from [0..7].
    """
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://127.0.0.1:5555")

    print(f"[RANDOM CLIENT] {player_color} started. Attempting random moves...")

    try:
        while True:
            # Generate random row, col in [0..7]
            row = random.randint(0, 7)
            col = random.randint(0, 7)

            msg = f"{player_color} MOVE {row} {col}"
            socket.send_string(msg)

            reply = socket.recv_string()

            if reply.startswith("OK:MOVE"):
                # Successfully made a move
                print(f"{player_color} move ({row},{col}) accepted. Waiting briefly...")
                # Wait a bit so that the other client can move
                time.sleep(1.0)

            elif reply.startswith("ERR:NOT_YOUR_TURN"):
                # It's not your turn; wait a bit, then try again
                print(f"{player_color} tried ({row},{col}), but it's NOT our turn. Retrying soon...")
                time.sleep(1.0)

            elif reply.startswith("ERR:ILLEGAL_MOVE"):
                # Move was illegal; just pick another random coordinate
                print(f"{player_color} move ({row},{col}) was illegal. Trying again...")

            elif reply.startswith("OK:QUIT"):
                # The server is shutting down or we were asked to quit
                print(f"{player_color} received OK:QUIT. Exiting.")
                break

            else:
                # Unknown or unhandled response
                print(f"{player_color} received unknown response: {reply}. Exiting.")
                break

    except KeyboardInterrupt:
        print("\nClient interrupted by user (Ctrl+C). Exiting.")
    finally:
        socket.close()
        context.term()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python random_client.py BLACK|WHITE")
        sys.exit(1)

    color_arg = sys.argv[1].upper()
    if color_arg not in ("BLACK", "WHITE"):
        print("Please specify BLACK or WHITE.")
        sys.exit(1)

    main(color_arg)
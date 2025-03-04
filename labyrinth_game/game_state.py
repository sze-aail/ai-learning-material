from enum import Enum

class GameState(Enum):
    PAUSED = 1
    SEARCHING = 2
    MOVING = 3
    QUIT = 4
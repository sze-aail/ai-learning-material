# controller.py
import pygame
from game_state import GameState
from model import PlayerModel
from state import DataState


class GameController:
    def __init__(self, state: DataState):

        self._state = GameState.PAUSED
        self.search_generator = None
        self._search_state = None
        self._algorithm = None
        self.player_model = None
        self._data_state = state


    def set_algorithm(self, algorithm):
        """
        External control may call this to load a search algorithm.
        Acts as an adapter.
        """
        self._algorithm = algorithm
        self.search_generator = self.algorithm.search(
            self._data_state.maze_model,
            self._data_state.maze_model.start,
            self._data_state.maze_model.goal
        )
        self._state = GameState.SEARCHING

    def reset(self, state: DataState):
        self._data_state = state
        self._data_state.maze_model.find_start_goal()
        self.search_generator = None
        self._search_state = None
        self._algorithm = None
        self._state = GameState.PAUSED

    def exit(self):
        self._state = GameState.QUIT

    def update(self, dt):
        # Update models.
        match self._state:
            case GameState.SEARCHING:
                if self.search_generator is not None:
                    try:
                        self._search_state = next(self.search_generator)
                    except StopIteration:
                        path = self.algorithm.reconstruct_path(
                            self.search_state["current"]
                        )
                        self._data_state.player.path = path
                        self._data_state.player.current_index = 0
                        self._state = GameState.MOVING
                        self.search_generator = None
            case GameState.MOVING:
                self._data_state.player.update(dt)

    @property
    def state(self):
        return self._state

    @property
    def search_state(self):
        return self._search_state

    @property
    def data_state(self) -> DataState:
        return self._data_state

    @property
    def algorithm(self):
        return self._algorithm

    def is_running(self):
        return self._state != GameState.QUIT

    def is_searching(self):
        return self._state == GameState.SEARCHING

    def is_moving(self):
        return self._state == GameState.MOVING

    def is_paused(self):
        return self._state == GameState.PAUSED

    def is_quit(self):
        return self._state == GameState.QUIT


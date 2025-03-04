from model import PlayerModel, MazeModel


class DataState(object):
    def __init__(self, maze_model, player_model):
        self._maze_model = maze_model
        self._player = player_model

    def __str__(self):
        return f"{self._player}\n{self._maze_model}"

    @property
    def player(self) -> PlayerModel:
        return self._player

    @property
    def maze_model(self) -> MazeModel:
        return self._maze_model
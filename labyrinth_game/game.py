from controller import GameController
from game_state import GameState
from maze.maze_cost import MazeCostGenerator
from search.astar_search import AStarSearch
from search.breadth_first_search import BreadthFirstSearch
from search.depth_first_search import DepthFirstSearch
from search.uniform_cost_search import UniformCostSearch
from state import DataState
from view import VisualVisitor, Button
import pygame
from maze.maze_generator import MazeGenerator
from model import MazeModel, PlayerModel
import sys

class Game(object):

    def __init__(self, width= 21, height= 15):
        pygame.init()
        # Generate maze algorithmically.
        maze_gen = MazeGenerator(width, height)
        grid = maze_gen.generate()
        self.cell_size = 32
        maze_model = MazeModel(grid, self.cell_size)
        self.screen_width = maze_model.cols * self.cell_size
        self.screen_height = maze_model.rows * self.cell_size
        self.screen = pygame.display.set_mode(
            (self.screen_width, self.screen_height)
        )
        pygame.display.set_caption("Maze Search Visualization")
        self.clock = pygame.time.Clock()

        self.visitor = VisualVisitor()
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 24)
        self.big_font = pygame.font.SysFont("Arial", 36)
        # Decomposed buttons.
        self.generate_maze_button = Button(
            (self.screen_width // 4 - 100, self.screen_height // 2 - 110, 200, 50),
            "Generate maze",
            self.font,
        )
        self.generate_cost_maze_button = Button(
            (3 * self.screen_width // 4 - 100, self.screen_height // 2 - 110, 200, 50),
            "Generate maze with cost",
            self.font,
        )

        self.bfs_button = Button(
            (self.screen_width // 4 - 100, self.screen_height // 2 - 50, 200, 50),
            "BFS",
            self.font,
        )
        self.dfs_button = Button(
            (3 * self.screen_width // 4 - 100, self.screen_height // 2 - 50, 200, 50),
            "DFS",
            self.font,
        )
        self.dijkstra_button = Button(
            (3 * self.screen_width // 4 - 100, self.screen_height // 2 +20, 200, 50),
            "Dijkstra",
            self.font,
        )
        self.astar_button = Button(
            (self.screen_width // 4 - 100, self.screen_height // 2 +20, 200, 50),
            "A*",
            self.font,
        )
        self.restart_button = Button(
            (self.screen_width // 2 - 100, self.screen_height - 80, 200, 50),
            "Restart",
            self.font,
            bg_color=(128, 0, 0),
        )

        player_model = PlayerModel(maze_model.start, self.cell_size)
        self._state = DataState(maze_model, player_model)
        # Controller init
        self._controller = GameController(self._state)

    def reset(self, _maze_model=None):
        if _maze_model:
            maze_model = _maze_model
        else:
            maze_gen = MazeGenerator(self._state.maze_model.cols, self._state.maze_model.rows)
            grid = maze_gen.generate()
            maze_model = MazeModel(grid, self.cell_size)
        player_model = PlayerModel(maze_model.start, self.cell_size)
        self._state = DataState(maze_model, player_model)
        self._controller.reset(self._state)

    def render(self):
        # Delegate all drawing to the view.
        self.screen.fill((0, 0, 0))
        self.visitor.visit_maze(self._state.maze_model, self.screen)
        if self._controller.algorithm is not None:
            self.visitor.visit_algorithm_label(self.screen, self.font, self._controller.algorithm)
        match self._controller.state:
            case GameState.PAUSED:
                self.visitor.visit_menu(
                    self.screen,
                    self.screen_width,
                    self.screen_height,
                    self.big_font,
                    [self.generate_maze_button, self.generate_cost_maze_button, self.bfs_button, self.dfs_button, self.astar_button, self.dijkstra_button],
                )
            case GameState.SEARCHING:
                if self._controller.search_state:
                    self.visitor.visit_search_tree(
                        self._controller.search_state["search_tree"],
                        self.screen,
                        self.cell_size,
                    )
            case GameState.MOVING:
                if self._controller.search_state:
                    self.visitor.visit_search_tree(
                        self._controller.search_state["search_tree"],
                        self.screen,
                        self.cell_size,
                    )
                if self._state.player.path:
                    self.visitor.visit_path(self._state.player, self.screen)
                self.visitor.visit_player(self._state.player, self.screen)
                if self._state.player.current_index >= len(self._state.player.path) - 1:
                    self.visitor.visit_restart_button(self.screen, self.restart_button)


    def run(self):
        while self._controller.is_running():
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self._controller.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    pos = pygame.mouse.get_pos()
                    match self._controller.state:
                        case GameState.PAUSED:
                            if self.bfs_button.is_clicked(pos):
                                self._controller.set_algorithm(BreadthFirstSearch())
                            elif self.dfs_button.is_clicked(pos):
                                self._controller.set_algorithm(DepthFirstSearch())
                            elif self.dijkstra_button.is_clicked(pos):
                                self._controller.set_algorithm(UniformCostSearch())
                            elif self.astar_button.is_clicked(pos):
                                self._controller.set_algorithm(AStarSearch())
                            elif self.generate_maze_button.is_clicked(pos):
                                cols, rows = self._state.maze_model.cols, self._state.maze_model.rows
                                maze_gen = MazeGenerator(cols, rows)
                                grid = maze_gen.generate()
                                maze_model = MazeModel(grid, self.cell_size)
                                self.reset(maze_model)
                            elif self.generate_cost_maze_button.is_clicked(pos):
                                cols, rows = self._state.maze_model.cols, self._state.maze_model.rows
                                maze_gen = MazeCostGenerator(cols, rows)
                                grid = maze_gen.generate()
                                maze_model = MazeModel(grid, self.cell_size)
                                self.reset(maze_model)
                        case GameState.MOVING:
                            if (
                                self._state.player.current_index
                                >= len(self._state.player.path) - 1
                                and self.restart_button.is_clicked(pos)
                            ):
                                self.reset()
            self.render()
            self._controller.update(dt)
            pygame.display.flip()
        pygame.quit()
        sys.exit()

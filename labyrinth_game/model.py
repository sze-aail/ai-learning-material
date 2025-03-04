# model.py
import math
from node import Node


class MazeModel:
    def __init__(self, grid, cell_size):
        """
        Initialize the maze model.
        Args:
            grid: List of strings representing the maze.
            cell_size: The pixel size of each cell.
        """
        self.grid = grid
        self.cell_size = cell_size
        self.rows = grid.rows
        self.cols = grid.cols
        self.start = None
        self.goal = None
        self.find_start_goal()

    def find_start_goal(self):
        """Find the start ('S') and goal ('G') cells and create Node objects."""
        for r, row in enumerate(self.grid.grid):
            for c, char in enumerate(row):
                if char == 'S':
                    self.start = Node(r, c)
                elif char == 'G':
                    self.goal = Node(r, c)

    def get_neighbors(self, node):
        """
        Return a list of neighboring Node objects for a given node.
        Only returns neighbors that are not walls.
        """
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbors = []
        for dr, dc in directions:
            nr, nc = node.row + dr, node.col + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if self.grid.grid[nr][nc] != '#':
                    neighbors.append(Node(nr, nc))
        return neighbors


class PlayerModel:
    def __init__(self, start, cell_size):
        """
        Initialize the player model.
        Args:
            start: A Node object representing the starting cell.
            cell_size: The pixel size of each cell.
        """
        self.cell_size = cell_size
        # Position as floating-point coordinates (center of cell).
        self.position = [start.col * cell_size + cell_size / 2,
                         start.row * cell_size + cell_size / 2]
        self.path = []  # List of Node objects (computed path).
        self.current_index = 0
        self.speed = 150  # Pixels per second.
        self.direction = 0  # Radians.

    def update(self, dt):
        """
        Update the player's position along the path.
        Args:
            dt: Time delta in seconds.
        """
        if self.current_index < len(self.path) - 1:
            next_node = self.path[self.current_index + 1]
            target = [next_node.col * self.cell_size + self.cell_size / 2,
                      next_node.row * self.cell_size + self.cell_size / 2]
            vx = target[0] - self.position[0]
            vy = target[1] - self.position[1]
            distance = math.hypot(vx, vy)
            if distance > 0:
                ux, uy = vx / distance, vy / distance
                move_dist = self.speed * dt
                if move_dist >= distance:
                    self.position = target
                    self.current_index += 1
                else:
                    self.position[0] += ux * move_dist
                    self.position[1] += uy * move_dist
                self.direction = math.atan2(uy, ux)

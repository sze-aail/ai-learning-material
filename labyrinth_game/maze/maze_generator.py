# maze_generator.py
from dataclasses import dataclass
import random
import typing
from collections import deque


@dataclass
class Maze:
    """
    A dataclass representing a maze.
    """
    grid: list[str]
    start: tuple[int, int]
    goal: tuple[int, int]
    costs: dict[tuple[int, int], int]

    def __str__(self):
        return "\n".join(self.grid)

    @property
    def rows(self):
        return len(self.grid)

    @property
    def cols(self):
        return len(self.grid[0])




class MazeGenerator:
    def __init__(self, width: int, height: int, branch_factor: float = 0.1, cost_range: typing.Tuple[int, int] = (1, 10)):
        """
        Create a maze generator.
        The width and height should be odd numbers; if even, they are increased by 1.

        Args:
            width (int): Maze width in cells.
            height (int): Maze height in cells.
            branch_factor (float): Probability to carve an extra passage at a wall.
            cost_range (tuple[int, int]): The (min, max) range for random cost assignment.
        """
        if width % 2 == 0:
            width += 1
        if height % 2 == 0:
            height += 1
        self.width = width
        self.height = height
        self.branch_factor = branch_factor
        self.cost_range = cost_range
        # Initialize grid with walls ('#')
        self.grid = [['#' for _ in range(width)] for _ in range(height)]

    def generate(self) -> Maze:
        """
        Generate a maze with extra branches and assign random costs to passage cells.
        The goal is chosen as the farthest cell from the start.

        Returns:
            Maze: A Maze dataclass instance with grid, start, goal, and costs.
        """
        start_x, start_y = 1, 1
        self.grid[start_y][start_x] = ' '  # Mark starting cell as passage.
        self._carve_passages_from(start_x, start_y)
        self._add_branches()
        # Find the farthest reachable cell from (1,1) for the goal.
        goal_x, goal_y = self._find_farthest_cell(start_x, start_y)
        # Mark start and goal in the grid.
        self.grid[start_y][start_x] = 'S'
        self.grid[goal_y][goal_x] = 'G'
        # Convert each row to a string.
        grid_str = ["".join(row) for row in self.grid]
        # Assign random costs for each passage cell.
        costs = {}
        for r in range(self.height):
            for c in range(self.width):
                if self.grid[r][c] != '#':
                    # This is a passage cell with a cost 1
                    costs[(r, c)] = 1
        return Maze(grid=grid_str, start=(start_y, start_x), goal=(goal_y, goal_x), costs=costs)

    def _carve_passages_from(self, cx: int, cy: int):
        """
        Recursively carve passages from the current cell (cx, cy) using backtracking.
        """
        directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
        random.shuffle(directions)
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 < nx < self.width and 0 < ny < self.height and self.grid[ny][nx] == '#':
                # Remove the wall between current cell and neighbor.
                self.grid[cy + dy // 2][cx + dx // 2] = ' '
                self.grid[ny][nx] = ' '
                self._carve_passages_from(nx, ny)

    def _add_branches(self):
        """
        Add extra passages based on branch_factor.
        For each wall cell adjacent to a passage, with probability branch_factor,
        convert the wall into a passage.
        """
        for r in range(1, self.height - 1):
            for c in range(1, self.width - 1):
                if self.grid[r][c] == '#':
                    # Check if at least one neighbor is a passage.
                    neighbors = [
                        self.grid[r - 1][c],
                        self.grid[r + 1][c],
                        self.grid[r][c - 1],
                        self.grid[r][c + 1]
                    ]
                    if ' ' in neighbors:
                        if random.random() < self.branch_factor:
                            self.grid[r][c] = ' '

    def _find_farthest_cell(self, start_x: int, start_y: int) -> typing.Tuple[int, int]:
        """
        Find the farthest reachable cell from (start_x, start_y) using BFS.

        Returns:
            Tuple[int, int]: Coordinates (x, y) of the farthest cell.
        """
        queue = deque()
        queue.append((start_x, start_y))
        visited = {(start_x, start_y)}
        distances = {(start_x, start_y): 0}
        farthest = (start_x, start_y)
        max_dist = 0

        while queue:
            cx, cy = queue.popleft()
            d = distances[(cx, cy)]
            if d > max_dist:
                max_dist = d
                farthest = (cx, cy)
            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = cx + dx, cy + dy
                if 0 <= nx < self.width and 0 <= ny < self.height and (nx, ny) not in visited:
                    if self.grid[ny][nx] != '#':  # Passage cell.
                        visited.add((nx, ny))
                        distances[(nx, ny)] = d + 1
                        queue.append((nx, ny))
        return farthest

# maze_cost_generator.py

import random

from maze.maze_generator import MazeGenerator, Maze


class MazeCostGenerator(MazeGenerator):
    def __init__(self, width, height, branch_factor=0.1, cost_range=(1, 10)):
        """
        Initialize a MazeCostGenerator.

        Args:
            width (int): Maze width in cells.
            height (int): Maze height in cells.
            branch_factor (float): The probability for extra passages to be carved.
            cost_range (tuple): A tuple (min_cost, max_cost) for passage cell costs.
        """
        super().__init__(width, height, branch_factor)
        self._cost_range = cost_range
        # Initialize a cost grid for each cell; walls will remain None.
        self._cost_grid = [[None for _ in range(self.width)] for _ in range(self.height)]

    def generate(self):
        """
        Generate the maze with extra branches and assign random costs to passage cells.
        Returns:
            A list of strings, each representing a row of the maze.
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
                    costs[(r, c)] = random.uniform(
                        self._cost_range[0], self._cost_range[1]
                    )
        return Maze(grid=grid_str, start=(start_y, start_x), goal=(goal_y, goal_x), costs=costs)

    def get_cost(self, row, col):
        """
        Get the cost assigned to the cell at the given row and column.

        Args:
            row (int): Row index.
            col (int): Column index.

        Returns:
            The cost value (float) if the cell is a passage; otherwise, None.
        """
        return self._cost_grid[row][col]
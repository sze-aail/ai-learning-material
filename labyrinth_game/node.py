# node.py
from collections import OrderedDict


class Node:
    def __init__(self, row, col, parent=None, cumulative_cost=float('inf'), step_cost=1):
        """
        Initialize a Node.

        Args:
            row (int): The row index of the node.
            col (int): The column index of the node.
            parent (Node, optional): The parent node. Defaults to None.
            cumulative_cost (float, optional): The total cost to reach this node from the start.
                                               Defaults to infinity.
            step_cost (int, optional): The cost to move from the parent to this node.
                                       Defaults to 1.
        """
        self.row = row
        self.col = col
        self.parent = parent
        self.id = (row << 16) | col  # Unique numeric identifier.
        self.children = OrderedDict()
        self._cumulative_cost = cumulative_cost
        self._step_cost = step_cost

    @property
    def cumulative_cost(self):
        """Get the cumulative cost (total cost from the start)."""
        return self._cumulative_cost

    @cumulative_cost.setter
    def cumulative_cost(self, value):
        self._cumulative_cost = value

    @property
    def step_cost(self):
        """Get the step cost (cost from the parent to this node)."""
        return self._step_cost

    @step_cost.setter
    def step_cost(self, value):
        self._step_cost = value

    def __eq__(self, other):
        if isinstance(other, Node):
            return self.id == other.id
        return False

    def __hash__(self):
        return self.id

    def __repr__(self):
        return (
            f"Node({self.row}, {self.col}, "
            f"cumulative_cost={self.cumulative_cost}, id={self.id})"
        )
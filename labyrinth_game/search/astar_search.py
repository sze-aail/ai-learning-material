import heapq
from itertools import count

from search.search_algorithms import FringeSearch


class AStarSearch(FringeSearch):
    def search(self, maze_model, start, goal):
        """
        Perform A* search on the maze_model from start to goal.
        Stores the goal for heuristic calculation.
        Yields a dictionary with:
            - "current": the node being processed.
            - "search_tree": the root node (start) of the search tree.
            - "visited": a list of visited nodes.
        """
        self._goal = goal
        # Initialize the starting node cumulative cost to 0.
        start.cumulative_cost = 0
        fringe = self.initialize_fringe(start)
        visited = {start.id: start}
        cost_so_far = {start.id: 0}

        while fringe:
            current = self.pop_fringe(fringe)
            yield {
                "current": current,
                "search_tree": start,
                "visited": list(visited.values())
            }
            if current == goal:
                break
            self.extend(maze_model, current, fringe, cost_so_far, visited)
        yield {
            "current": current,
            "search_tree": start,
            "visited": list(visited.values())
        }

    def cost_function(self, current, neighbor):
        """
        For A*, the edge cost is the neighbor's step cost.
        """
        return neighbor.step_cost

    def heuristic(self, node):
        """
        Compute the Manhattan distance from node to the goal.
        """
        return abs(node.row - self._goal.row) + abs(node.col - self._goal.col)

    def initialize_fringe(self, start):
        """
        Initialize the fringe as a heap (priority queue) with a tie-breaker counter.
        """
        self._counter = count()  # Tie-breaker counter.
        fringe = []
        heapq.heappush(fringe, (0, next(self._counter), start))
        return fringe

    def pop_fringe(self, fringe):
        """
        Pop and return the next node from the fringe.
        """
        return heapq.heappop(fringe)[2]

    def push_fringe(self, fringe, node, priority):
        """
        Push a node onto the fringe with priority = new_cost + heuristic.
        """
        heapq.heappush(fringe, (priority + self.heuristic(node), next(self._counter), node))
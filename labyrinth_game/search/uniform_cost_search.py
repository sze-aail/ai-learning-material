from search.search_algorithms import FringeSearch
from itertools import count
import heapq


class UniformCostSearch(FringeSearch):
    def initialize_fringe(self, start):
        self._counter = count()  # Tie-breaker counter.
        fringe = []
        heapq.heappush(fringe, (0, next(self._counter), start))
        return fringe

    def pop_fringe(self, fringe):
        # Return the node (third element in the tuple).
        return heapq.heappop(fringe)[2]

    def push_fringe(self, fringe, node, priority):
        heapq.heappush(fringe, (priority, next(self._counter), node))

    def cost_function(self, current, neighbor):
        # Use the neighbor's step_cost attribute.
        return neighbor.step_cost
from search.search_algorithms import FringeSearch


class DepthFirstSearch(FringeSearch):
    def cost_function(self, current, neighbor):
        # Each step costs 1.
        return 1

    def initialize_fringe(self, start):
        return [start]

    def pop_fringe(self, fringe):
        return fringe.pop()

    def push_fringe(self, fringe, node, priority):
        fringe.append(node)
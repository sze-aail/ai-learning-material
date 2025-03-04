# search_algorithms.py

from abc import ABC, abstractmethod



class SearchAlgorithm(ABC):
    def reconstruct_path(self, goal):
        """
        Reconstructs the path from the start to the goal using parent pointers.
        Returns a list of Node objects.
        """
        path = []
        current = goal
        while current is not None:
            path.append(current)
            current = current.parent
        path.reverse()
        return path

    @abstractmethod
    def search(self, maze_model, start, goal):
        """
        Perform the search.
        Yields a dictionary with:
            - "current": the node being processed.
            - "search_tree": the root node (start) of the search tree.
            - "visited": a list of visited nodes.
        """
        pass


class FringeSearch(SearchAlgorithm):
    @abstractmethod
    def initialize_fringe(self, start):
        """
        Initialize and return the fringe container.
        """
        pass

    @abstractmethod
    def pop_fringe(self, fringe):
        """
        Remove and return the next node from the fringe.
        """
        pass

    @abstractmethod
    def push_fringe(self, fringe, node, priority):
        """
        Add a node to the fringe with the given priority.
        """
        pass

    @abstractmethod
    def cost_function(self, current, neighbor):
        """
        Return the cost to move from current to neighbor.
        """
        pass

    def extend(self, maze_model, current, fringe, cost_so_far, visited):
        """
        Extend the search from the current node.
        For each neighbor, update its cumulative cost and parent pointer if a lower cost
        path is found. Then push the neighbor to the fringe with the new cost as priority.
        """
        for neighbor in maze_model.get_neighbors(current):
            new_cost = cost_so_far[current.id] + self.cost_function(current, neighbor)
            if neighbor.id not in cost_so_far or new_cost < cost_so_far[neighbor.id]:
                cost_so_far[neighbor.id] = new_cost
                neighbor.cumulative_cost = new_cost
                neighbor.parent = current
                current.children[neighbor.id] = neighbor
                visited[neighbor.id] = neighbor
                self.push_fringe(fringe, neighbor, new_cost)

    def search(self, maze_model, start, goal):
        """
        Perform the generic fringe-based search.
        Initializes the starting node's cumulative cost to 0, and maintains a visited
        dictionary and a cost_so_far map.
        """
        start.cumulative_cost = 0  # Set starting node cumulative cost to 0.
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









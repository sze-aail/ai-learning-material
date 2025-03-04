# view.py
import pygame
import math


class Button:
    def __init__(self, rect, text, font, bg_color=(0, 128, 0), text_color=(255, 255, 255)):
        """
        Initialize a button.
        Args:
            rect: Tuple (x, y, width, height) defining the button area.
            text: Button text.
            font: Pygame font object.
            bg_color: Background color.
            text_color: Text color.
        """
        self.rect = pygame.Rect(rect)
        self.text = text
        self.font = font
        self.bg_color = bg_color
        self.text_color = text_color

    def draw(self, surface):
        """Draw the button on the given surface."""
        pygame.draw.rect(surface, self.bg_color, self.rect)
        text_surf = self.font.render(self.text, True, self.text_color)
        surface.blit(
            text_surf,
            (
                self.rect.centerx - text_surf.get_width() // 2,
                self.rect.centery - text_surf.get_height() // 2,
            ),
        )

    def is_clicked(self, pos):
        """Return True if the button is clicked (pos is inside the rect)."""
        return self.rect.collidepoint(pos)


class VisualVisitor:
    def draw_rectangular_gradient(self, surface, rect, top_color, bottom_color):
        """
        Draw a vertical gradient within the given rect.
        """
        for y in range(rect.top, rect.bottom):
            factor = (y - rect.top) / rect.height
            color = [
                int(top_color[i] * (1 - factor) + bottom_color[i] * factor)
                for i in range(3)
            ]
            pygame.draw.line(surface, color, (rect.left, y), (rect.right, y))

    def visit_maze(self, maze_model, surface):
        """
        Draws the maze.
        Walls are drawn in a solid white-gray.
        Passages are drawn with a vertical gradient from a cost-dependent
        steel blue to white.
        """
        cell_size = maze_model.cell_size
        # Assume maze_model.cost_range is a tuple: (min_cost, max_cost)
        min_cost, max_cost = maze_model.cost_range if hasattr(maze_model, "cost_range") else (1, 10)

        for r in range(maze_model.rows):
            for c in range(maze_model.cols):
                rect = pygame.Rect(c * cell_size, r * cell_size, cell_size, cell_size)
                char = maze_model.grid.grid[r][c]
                if char == '#':
                    pygame.draw.rect(surface, (220, 220, 220), rect)
                else:
                    # Retrieve the cost for the cell at (r, c) from the Maze dataclass.
                    cost = maze_model.grid.costs[(r, c)]
                    # Normalize cost to a value between 0 and 1.
                    factor = (cost - min_cost) / (max_cost - min_cost) if max_cost > min_cost else 0
                    # Interpolate top color: low cost -> steel blue; high cost -> white.
                    top_color = (
                        int(70 * (1 - factor) + 255 * factor),
                        int(130 * (1 - factor) + 255 * factor),
                        int(180 * (1 - factor) + 255 * factor)
                    )
                    bottom_color = (255, 255, 255)
                    self.draw_rectangular_gradient(surface, rect, top_color, bottom_color)
                pygame.draw.rect(surface, (100, 100, 100), rect, 1)
                if char == 'S':
                    pygame.draw.rect(surface, (255, 0, 0), rect)
                elif char == 'G':
                    cx = c * cell_size + cell_size // 2
                    cy = r * cell_size + cell_size // 2
                    half = cell_size // 2 - 2
                    diamond = [
                        (cx, cy - half),
                        (cx + half, cy),
                        (cx, cy + half),
                        (cx - half, cy),
                    ]
                    pygame.draw.polygon(surface, (0, 255, 0), diamond)

    def visit_player(self, player_model, surface):
        """
        Draw the player as a triangle.
        The triangle is rotated so that a direction of 0 radians (movement to the right)
        makes the triangle point right.
        """
        pos = player_model.position
        adjusted_direction = player_model.direction + math.pi / 2
        r = player_model.cell_size / 2 - 2
        pts = [(0, -r), (-r / 2, r / 2), (r / 2, r / 2)]
        cos_a = math.cos(adjusted_direction)
        sin_a = math.sin(adjusted_direction)
        rotated = []
        for x, y in pts:
            rx = x * cos_a - y * sin_a
            ry = x * sin_a + y * cos_a
            rotated.append((pos[0] + rx, pos[1] + ry))
        pygame.draw.polygon(surface, (255, 255, 0), rotated)

    def visit_path(self, player_model, surface):
        """
        Draw the computed path as a magenta polyline connecting the centers of the cells.
        """
        if len(player_model.path) > 1:
            cell_size = player_model.cell_size
            points = []
            for node in player_model.path:
                center = (
                    node.col * cell_size + cell_size / 2,
                    node.row * cell_size + cell_size / 2,
                )
                points.append(center)
            pygame.draw.lines(surface, (255, 0, 255), False, points, 3)

    def visit_search_tree(self, search_tree, surface, cell_size):
        """Recursively draw the search tree."""
        self._draw_tree(search_tree, surface, cell_size)

    def _draw_tree(self, node, surface, cell_size):
        if node.parent is not None:
            parent_center = (
                node.parent.col * cell_size + cell_size // 2,
                node.parent.row * cell_size + cell_size // 2,
            )
            node_center = (
                node.col * cell_size + cell_size // 2,
                node.row * cell_size + cell_size // 2,
            )
            pygame.draw.line(surface, (255, 255, 255), parent_center, node_center, 2)
        node_center = (
            node.col * cell_size + cell_size // 2,
            node.row * cell_size + cell_size // 2,
        )
        pygame.draw.circle(surface, (200, 200, 200), node_center, 4)
        for child in node.children.values():
            self._draw_tree(child, surface, cell_size)

    def visit_algorithm_label(self, surface, font, algorithm):
        text = "Algorithm: " + type(algorithm).__name__
        alg_text = font.render(text, True, (255, 255, 255))
        surface.blit(alg_text, (10, 10))

    def visit_menu(self, surface, screen_width, screen_height, big_font, buttons):
        overlay = pygame.Surface((screen_width, screen_height))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))
        title_text = big_font.render("Select Search Algorithm", True, (255, 255, 255))
        surface.blit(title_text, (screen_width // 2 - title_text.get_width() // 2, 100))
        for btn in buttons:
            btn.draw(surface)

    def visit_restart_button(self, surface, restart_button):
        restart_button.draw(surface)



import pygame
import textwrap


class Interface:
    """Graphical interface for Maris Nostri Mercatores.

    This class is intentionally independent from the game logic.
    It only displays information provided by the game and returns
    commands typed by the player.
    """

    ####################################################################
    # Configuration
    ####################################################################

    WINDOW_WIDTH = 1500
    WINDOW_HEIGHT = 750

    SIDE_PANEL_WIDTH = 340
    MAP_WIDTH = 800
    MAP_HEIGHT = 650

    BG_COLOUR = (40, 40, 40)
    PANEL_COLOUR = (60, 60, 60)
    INPUT_COLOUR = (25, 25, 25)
    TEXT_COLOUR = (240, 240, 240)

    ####################################################################

    def __init__(
        self,
        logo_path="assets/logo.png",
        map_path="assets/map.png"
    ):

        pygame.init()

        pygame.display.set_caption("Maris Nostri Mercatores")

        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        )

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 18)
        self.big_font = pygame.font.SysFont(
            "consolas",
            24,
            bold=True
        )

        ################################################################
        # Logo
        ################################################################

        self.logo = pygame.image.load(
            logo_path
        ).convert_alpha()

        max_width = 200

        if self.logo.get_width() > max_width:

            ratio = max_width / self.logo.get_width()

            self.logo = pygame.transform.smoothscale(
                self.logo,
                (
                    int(self.logo.get_width() * ratio),
                    int(self.logo.get_height() * ratio)
                )
            )

        ################################################################
        # Map
        ################################################################

        self.map = pygame.image.load(
            map_path
        ).convert()

        self.map = pygame.transform.smoothscale(
            self.map,
            (self.MAP_WIDTH, self.MAP_HEIGHT)
        )

        ################################################################
        # Game information
        ################################################################

        self.command = ""

        self.command_history = []
        self.history_index = 0

        self.stats = ""
        self.stats_title = ""

        self.message = ""
        self.message_title = "Messages"

        self.running = True

    ####################################################################
    # Public methods
    ####################################################################

    def is_running(self):
        return self.running

    def set_stats(self, text, title=""):
        """Set the contents of the statistics panel."""

        self.stats = text
        self.stats_title = title

    def set_message(self, text, title="Messages"):
        """Set the contents of the message panel."""

        self.message = text
        self.message_title = title

    def set_map(self, map_path):
        """Load a new map image."""

        self.map = pygame.image.load(
            map_path
        ).convert()

        self.map = pygame.transform.smoothscale(
            self.map,
            (self.MAP_WIDTH, self.MAP_HEIGHT)
        )

    ####################################################################
    # Input
    ####################################################################

    def get_command(self):
        """Return a command if Enter was pressed."""

        for event in pygame.event.get():

            if event.type == pygame.QUIT:

                self.running = False
                return None

            if event.type == pygame.KEYDOWN:

                if event.key == pygame.K_RETURN:

                    command = self.command.strip()

                    self.command = ""

                    if command != "":

                        self.command_history.append(command)

                        self.history_index = len(
                            self.command_history
                        )

                        return command

                elif event.key == pygame.K_BACKSPACE:

                    self.command = self.command[:-1]

                elif event.key == pygame.K_UP:

                    if self.command_history:

                        self.history_index = max(
                            0,
                            self.history_index - 1
                        )

                        self.command = self.command_history[
                            self.history_index
                        ]

                elif event.key == pygame.K_DOWN:

                    if self.command_history:

                        self.history_index = min(
                            len(self.command_history),
                            self.history_index + 1
                        )

                        if (
                            self.history_index
                            == len(self.command_history)
                        ):
                            self.command = ""

                        else:
                            self.command = (
                                self.command_history[
                                    self.history_index
                                ]
                            )

                else:

                    self.command += event.unicode

        return None

    ####################################################################
    # Drawing
    ####################################################################

    def draw(self):

        self.screen.fill(self.BG_COLOUR)

        self._draw_stats()
        self._draw_map()
        self._draw_message()
        self._draw_command_box()

        pygame.display.flip()

        self.clock.tick(60)

    ####################################################################
    # Map
    ####################################################################

    def _draw_map(self):

        map_x = self.SIDE_PANEL_WIDTH + 10
        map_y = 20

        self.screen.blit(
            self.map,
            (map_x, map_y)
        )

        # Logo over the map
        self.screen.blit(
            self.logo,
            (
                map_x + 10,
                map_y + 10
            )
        )

    ####################################################################
    # Statistics panel
    ####################################################################

    def _draw_stats(self):

        panel = pygame.Rect(
            10,
            20,
            self.SIDE_PANEL_WIDTH - 20,
            self.MAP_HEIGHT
        )

        pygame.draw.rect(
            self.screen,
            self.PANEL_COLOUR,
            panel
        )

        # Title
        title = self.big_font.render(
            self.stats_title,
            True,
            self.TEXT_COLOUR
        )

        self.screen.blit(
            title,
            (
                panel.x + 15,
                panel.y + 15
            )
        )

        self._draw_wrapped_text(
            self.stats,
            panel.x + 15,
            panel.y + 55,
            panel.width - 30
        )

    ####################################################################
    # Message panel
    ####################################################################

    def _draw_message(self):

        panel_x = (
            self.SIDE_PANEL_WIDTH
            + self.MAP_WIDTH
            + 30
        )

        panel = pygame.Rect(
            panel_x,
            20,
            self.SIDE_PANEL_WIDTH - 20,
            self.MAP_HEIGHT
        )

        pygame.draw.rect(
            self.screen,
            self.PANEL_COLOUR,
            panel
        )

        # Title
        title = self.big_font.render(
            self.message_title,
            True,
            self.TEXT_COLOUR
        )

        self.screen.blit(
            title,
            (
                panel.x + 15,
                panel.y + 15
            )
        )

        self._draw_wrapped_text(
            self.message,
            panel.x + 15,
            panel.y + 55,
            panel.width - 30
        )

    ####################################################################
    # Text helper
    ####################################################################

    def _draw_wrapped_text(
        self,
        text,
        x,
        y,
        width
    ):

        # Roughly determine characters per line.
        char_width = self.font.size("M")[0]

        max_characters = max(
            1,
            width // char_width
        )

        for line in text.split("\n"):

            wrapped = textwrap.wrap(
                line,
                width=max_characters
            )

            if not wrapped:

                y += 25
                continue

            for subline in wrapped:

                txt = self.font.render(
                    subline,
                    True,
                    self.TEXT_COLOUR
                )

                self.screen.blit(
                    txt,
                    (x, y)
                )

                y += 25

    ####################################################################
    # Command box
    ####################################################################

    def _draw_command_box(self):

        rect = pygame.Rect(
            10,
            self.WINDOW_HEIGHT - 60,
            self.WINDOW_WIDTH - 20,
            40
        )

        pygame.draw.rect(
            self.screen,
            self.INPUT_COLOUR,
            rect
        )

        txt = self.font.render(
            "> " + self.command,
            True,
            self.TEXT_COLOUR
        )

        self.screen.blit(
            txt,
            (
                20,
                self.WINDOW_HEIGHT - 52
            )
        )

    ####################################################################

    def close(self):

        pygame.quit()
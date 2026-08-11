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

    WINDOW_WIDTH = 1400
    WINDOW_HEIGHT = 750

    LEFT_PANEL_WIDTH = 950

    BG_COLOUR = (40, 40, 40)
    PANEL_COLOUR = (60, 60, 60)
    INPUT_COLOUR = (25, 25, 25)
    TEXT_COLOUR = (240, 240, 240)

    ####################################################################

    def __init__(self,
                 logo_path="assets/logo.png",
                 map_path="assets/map.png"):

        pygame.init()

        pygame.display.set_caption("Maris Nostri Mercatores")

        self.screen = pygame.display.set_mode(
            (self.WINDOW_WIDTH, self.WINDOW_HEIGHT)
        )

        self.clock = pygame.time.Clock()

        self.font = pygame.font.SysFont("consolas", 20)
        self.big_font = pygame.font.SysFont("consolas", 28, bold=True)

        self.logo = pygame.image.load(logo_path).convert_alpha()
        
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

        self.map = pygame.image.load(map_path).convert()
        
        self.map = pygame.transform.smoothscale(
            self.map,
            (900, 600)
        )

        self.command = ""
        
        self.title = ""

        self.stats = ""
        
        self.command_history = []
        
        self.history_index = 0

        self.running = True

    ####################################################################
    # Public methods
    ####################################################################

    def is_running(self):
        return self.running

    def set_stats(self, text, title=""):
        """Replace the statistics panel."""

        self.stats = text
        self.title = self.big_font.render(title, True, self.TEXT_COLOUR)

    def set_map(self, map_path):
        """Load a new map image."""

        self.map = pygame.image.load(map_path).convert()
        
        self.map = pygame.transform.smoothscale(
            self.map,
            (900, 600)
        )

    def get_command(self):
        """Returns a command if Enter was pressed.
    
        Returns
        -------
        None
            No complete command yet.
    
        str
            Command entered by the player.
        """
    
        for event in pygame.event.get():
    
            if event.type == pygame.QUIT:
                self.running = False
                return "exit"
    
            if event.type == pygame.KEYDOWN:
    
                if event.key == pygame.K_RETURN:
    
                    command = self.command.strip()
    
                    self.command = ""
    
                    if command != "":
    
                        self.command_history.append(command)
                        self.history_index = len(self.command_history)
    
                        return command
    
                elif event.key == pygame.K_BACKSPACE:
    
                    self.command = self.command[:-1]
    
                elif event.key == pygame.K_UP:
    
                    if self.command_history:
    
                        self.history_index = max(
                            0,
                            self.history_index - 1
                        )
    
                        self.command = self.command_history[self.history_index]
    
                elif event.key == pygame.K_DOWN:
    
                    if self.command_history:
    
                        self.history_index = min(
                            len(self.command_history),
                            self.history_index + 1
                        )
    
                        if self.history_index == len(self.command_history):
                            self.command = ""
                        else:
                            self.command = self.command_history[self.history_index]
    
                else:
    
                    self.command += event.unicode
    
        return None

    ####################################################################
    # Drawing
    ####################################################################

    def draw(self):

        self.screen.fill(self.BG_COLOUR)


        self._draw_map()

        self._draw_stats()

        self._draw_command_box()

        pygame.display.flip()

        self.clock.tick(60)

    ####################################################################
    # Private drawing methods
    ####################################################################

    def _draw_map(self):

        MAP_X = 20
        MAP_Y = 20
    
        self.screen.blit(self.map, (MAP_X, MAP_Y))
    
        # Draw the logo over the map
        self.screen.blit(
            self.logo,
            (MAP_X + 10, MAP_Y + 10)
        )

    def _draw_stats(self):

        panel = pygame.Rect(
            self.LEFT_PANEL_WIDTH,
            20,
            self.WINDOW_WIDTH - self.LEFT_PANEL_WIDTH - 20,
            620
        )

        pygame.draw.rect(
            self.screen,
            self.PANEL_COLOUR,
            panel
        )

        self.screen.blit(
            self.title,
            (panel.x + 15, panel.y + 15)
        )

        y = panel.y + 60

        MAX_CHARACTERS = 34
        
        for line in self.stats.split("\n"):
        
            wrapped = textwrap.wrap(line, width=MAX_CHARACTERS)
        
            if not wrapped:
                y += 28
                continue
        
            for subline in wrapped:
        
                txt = self.font.render(
                    subline,
                    True,
                    self.TEXT_COLOUR
                )
        
                self.screen.blit(txt, (panel.x + 15, y))
        
                y += 28

    def _draw_command_box(self):

        rect = pygame.Rect(
            20,
            self.WINDOW_HEIGHT - 60,
            self.WINDOW_WIDTH - 40,
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

        self.screen.blit(txt, (30, self.WINDOW_HEIGHT - 52))

    ####################################################################

    def close(self):

        pygame.quit()
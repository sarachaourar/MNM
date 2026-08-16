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
    SCROLLBAR_TRACK_COLOUR = (100, 100, 100)
    SCROLLBAR_THUMB_COLOUR = (180, 180, 180)

    LINE_HEIGHT = 25
    SCROLLBAR_WIDTH = 5
    SCROLLBAR_MIN_THUMB_HEIGHT = 30

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
        self.message_scroll = 0

        # Scrollbar hit-testing (updated each draw, read each input poll)
        self.scrollbar_track_rect = None
        self.scrollbar_thumb_rect = None
        self.scrollbar_max_scroll = 0
        self.dragging_scrollbar = False
        self.drag_offset_y = 0

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
        """Set the contents of the message panel.

        Scroll position is only reset back to the top when the text
        actually changes, since callers may call this every frame
        with unchanged content (e.g. inside a game loop).
        """

        if text != self.message:
            self.message_scroll = 0

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

            if event.type == pygame.MOUSEWHEEL:

                self.message_scroll -= event.y * 30

                self.message_scroll = max(
                    0,
                    min(
                        self.message_scroll,
                        self.scrollbar_max_scroll
                    )
                )

            if event.type == pygame.MOUSEBUTTONDOWN:

                if event.button == 1:

                    mouse_pos = event.pos

                    if (
                        self.scrollbar_thumb_rect
                        and self.scrollbar_thumb_rect.collidepoint(
                            mouse_pos
                        )
                    ):
                        # Start dragging from wherever on the thumb
                        # the user clicked, so it doesn't jump.
                        self.dragging_scrollbar = True

                        self.drag_offset_y = (
                            mouse_pos[1]
                            - self.scrollbar_thumb_rect.y
                        )

                    elif (
                        self.scrollbar_track_rect
                        and self.scrollbar_track_rect.collidepoint(
                            mouse_pos
                        )
                    ):
                        # Clicked on the track: jump the thumb so its
                        # centre is under the click, then scroll.
                        self._scroll_thumb_to(
                            mouse_pos[1]
                            - self.scrollbar_thumb_rect.height / 2
                        )

            if event.type == pygame.MOUSEBUTTONUP:

                if event.button == 1:
                    self.dragging_scrollbar = False

            if event.type == pygame.MOUSEMOTION:

                if self.dragging_scrollbar:
                    self._scroll_thumb_to(
                        event.pos[1] - self.drag_offset_y
                    )

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
    # Scrollbar dragging helper
    ####################################################################

    def _scroll_thumb_to(self, desired_thumb_y):
        """Given a desired thumb y (pixels), set message_scroll to match."""

        if not self.scrollbar_track_rect or not self.scrollbar_thumb_rect:
            return

        track = self.scrollbar_track_rect
        thumb_height = self.scrollbar_thumb_rect.height

        min_y = track.y
        max_y = track.y + track.height - thumb_height

        thumb_y = max(min_y, min(desired_thumb_y, max_y))

        if max_y > min_y:
            ratio = (thumb_y - min_y) / (max_y - min_y)
        else:
            ratio = 0

        self.message_scroll = int(ratio * self.scrollbar_max_scroll)

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

        # Stats panel isn't scrollable, so we just discard the
        # returned height/scroll info here.
        self._draw_wrapped_text(
            self.stats,
            panel.x + 15,
            panel.y + 55,
            panel.width - 30,
            panel.height - 70,
            0
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

        # Message area (leave a few px on the right for the scrollbar)
        text_rect = pygame.Rect(
            panel.x + 15,
            panel.y + 55,
            panel.width - 30 - self.SCROLLBAR_WIDTH - 5,
            panel.height - 70
        )

        content_height, max_scroll, self.message_scroll = (
            self._draw_wrapped_text(
                self.message,
                text_rect.x,
                text_rect.y,
                text_rect.width,
                text_rect.height,
                self.message_scroll
            )
        )

        self._draw_scrollbar(
            text_rect,
            content_height,
            max_scroll
        )

    ####################################################################
    # Scrollbar
    ####################################################################

    def _draw_scrollbar(self, text_rect, content_height, max_scroll):
        """Draw a scrollbar track + thumb next to text_rect, if needed."""

        self.scrollbar_max_scroll = max_scroll

        if content_height <= text_rect.height:
            # Nothing to scroll: clear hit-test rects so clicks/drags
            # don't reference stale geometry from a longer message.
            self.scrollbar_track_rect = None
            self.scrollbar_thumb_rect = None
            return

        scrollbar_x = text_rect.right + 5

        # Track
        track = pygame.Rect(
            scrollbar_x,
            text_rect.y,
            self.SCROLLBAR_WIDTH,
            text_rect.height
        )

        pygame.draw.rect(
            self.screen,
            self.SCROLLBAR_TRACK_COLOUR,
            track
        )

        # Thumb
        thumb_height = max(
            self.SCROLLBAR_MIN_THUMB_HEIGHT,
            int(
                text_rect.height
                * text_rect.height
                / content_height
            )
        )

        if max_scroll > 0:
            scroll_ratio = self.message_scroll / max_scroll
        else:
            scroll_ratio = 0

        thumb_y = text_rect.y + int(
            scroll_ratio * (text_rect.height - thumb_height)
        )

        thumb = pygame.Rect(
            scrollbar_x,
            thumb_y,
            self.SCROLLBAR_WIDTH,
            thumb_height
        )

        pygame.draw.rect(
            self.screen,
            self.SCROLLBAR_THUMB_COLOUR,
            thumb
        )

        # Store geometry for hit-testing on the next input poll.
        self.scrollbar_track_rect = track
        self.scrollbar_thumb_rect = thumb

    ####################################################################
    # Text helper
    ####################################################################

    def _draw_wrapped_text(
        self,
        text,
        x,
        y,
        width,
        height,
        scroll=0
    ):
        """Draw word-wrapped, scroll-clipped text.

        `scroll` is passed in by the caller rather than read from
        instance state, since this method is shared by multiple
        panels (stats, message) that must not clobber each other's
        scroll position.

        Returns (content_height, max_scroll, clamped_scroll) so
        callers can reuse the wrap calculation (e.g. for a scrollbar)
        and store the clamped scroll value back if needed.
        """

        char_width = self.font.size("M")[0]

        max_characters = max(
            1,
            width // char_width
        )

        lines = []

        for line in text.split("\n"):

            wrapped = textwrap.wrap(
                line,
                width=max_characters
            )

            if not wrapped:
                lines.append("")
            else:
                lines.extend(wrapped)

        # Total height of all text
        content_height = len(lines) * self.LINE_HEIGHT

        # Maximum amount we can scroll
        max_scroll = max(
            0,
            content_height - height
        )

        scroll = max(0, min(scroll, max_scroll))

        # Draw text
        current_y = y - scroll

        # Clip text to the panel
        old_clip = self.screen.get_clip()

        self.screen.set_clip(
            pygame.Rect(x, y, width, height)
        )

        for line in lines:

            txt = self.font.render(
                line,
                True,
                self.TEXT_COLOUR
            )

            self.screen.blit(
                txt,
                (x, current_y)
            )

            current_y += self.LINE_HEIGHT

        self.screen.set_clip(old_clip)

        return content_height, max_scroll, scroll

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
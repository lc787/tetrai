LOGIC_OBJECTS = []
# Draw order is maintained by the draw_level property
CANVAS_OBJECTS = []

width = 800
height = 600
target_fps = 60
game_running = False

class ColorTheme:
    def __init__(self, name, colors: dict):
        self.name = name
        self.block_cyan = colors['block_cyan']
        self.block_blue = colors['block_blue']
        self.block_orange = colors['block_orange']
        self.block_yellow = colors['block_yellow']
        self.block_green = colors['block_green']
        self.block_purple = colors['block_purple']
        self.block_red = colors['block_red']
        self.block_grey = colors['block_grey']
        self.empty = colors['empty']
        self.background = colors['background']


color_theme = ColorTheme("default", {
    "block_cyan": (0, 255, 255),
    "block_blue": (0, 0, 255),
    "block_orange": (255, 165, 0),
    "block_yellow": (255, 255, 0),
    "block_green": (0, 255, 0),
    "block_purple": (128, 0, 128),
    "block_red": (255, 0, 0),
    "block_grey": (128, 128, 128),
    "empty": (255, 255, 255),
    "background": (120, 120, 120)
})

color_theme2 = ColorTheme("dark", {
    "block_cyan": (255, 165, 0),
    "block_blue": (0, 255, 0),
    "block_orange": (0, 255, 255),
    "block_yellow": (255, 255, 0),
    "block_green": (0, 0, 255),
    "block_purple": (255, 0, 0),
    "block_red": (128, 0, 128),
    "block_grey": (128, 128, 128),
    "empty": (255, 255, 255),
    "background": (0, 0, 0)
})
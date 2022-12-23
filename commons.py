import pygame as pg

from gameengine import Key

width = 800
height = 600
target_fps = 60
game_running = False


color_theme_default = {'name': "default", 'palette': {
    "block_cyan": (0, 255, 255),
    "block_blue": (0, 0, 255),
    "block_orange": (255, 165, 0),
    "block_yellow": (255, 255, 0),
    "block_green": (0, 255, 0),
    "block_purple": (128, 0, 128),
    "block_red": (255, 0, 0),
    "block_grey": (128, 128, 128),
    "empty": (255, 255, 255),
    "text": (0, 0, 0),
    "background": (120, 120, 120)
}}

key_binds = {
    'clockwise': Key(pg.K_e),
    'counter_clockwise': Key(pg.K_q),
    'switch': Key(pg.K_w),
    'hard_drop': Key(pg.K_SPACE),
    'soft_drop': Key(pg.K_DOWN),
    'left': Key(pg.K_LEFT),
    'right': Key(pg.K_RIGHT),
    '180': Key(pg.K_p),
    'pause': Key(pg.K_ESCAPE),
    'restart': Key(pg.K_r),
}

agent_key_binds = {
    'clockwise': Key(pg.K_e, input_mode="agent"),
    'counter_clockwise': Key(pg.K_q, input_mode="agent"),
    'switch': Key(pg.K_w, input_mode="agent"),
    'hard_drop': Key(pg.K_SPACE, input_mode="agent"),
    'soft_drop': Key(pg.K_DOWN, input_mode="agent"),
    'left': Key(pg.K_LEFT, input_mode="agent"),
    'right': Key(pg.K_RIGHT, input_mode="agent"),
    '180': Key(pg.K_p, input_mode="agent"),
    'pause': Key(pg.K_ESCAPE, input_mode="agent"),
    'restart': Key(pg.K_r, input_mode="agent"),
}
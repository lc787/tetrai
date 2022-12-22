import pygame as pg
import commons
import gameengine
import grid
from gamefield import GameField
from gameengine import CanvasObject, Key


def handle_input():
    gameengine.KEYS = pg.key.get_pressed()
    for event in pg.event.get():
        match event.type:
            case pg.QUIT:
                gameengine.game_running = False
            case pg.KEYDOWN:
                match event.key:
                    case pg.K_ESCAPE:
                        gameengine.game_running = False


def update(dt):
    for obj in gameengine.LOGIC_OBJECTS:
        obj.update(dt)


def draw(screen: pg.Surface):
    for obj in gameengine.CANVAS_OBJECTS[::-1]:
        obj.draw()
        screen.blit(obj.image, obj.rect)
    pg.display.flip()


def init_screen():
    pg.display.set_caption("TetrAI")
    screen = pg.display.set_mode((commons.width, commons.height))
    screen.fill((0, 0, 0))
    pg.display.flip()
    return screen


def init_objs():
    background = CanvasObject(0, 0, commons.width, commons.height)
    background.image.fill(commons.color_theme.background)
    background.draw_level = 0
    cell_size = 24
    cell_margin = 2
    game_grid = grid.PlayField(commons.width // 2, commons.height // 2, 24, 2, commons.color_theme_default,
                               play_field_offset=(-((cell_size + cell_margin) * 5 + cell_margin // 2),
                                                  -((cell_size + cell_margin) * 30 + cell_margin // 2)),
                               hold_field_offset=(-((cell_size + cell_margin) * 11 + cell_margin // 2),
                                                  -((cell_size + cell_margin) * 10 + cell_margin // 2)),
                               next_field_offset=(((cell_size + cell_margin) * 7 + cell_margin // 2),
                                                  -((cell_size + cell_margin) * 10 + cell_margin // 2)))


# Init app
pg.init()

# Init screen
screen = init_screen()

init_objs()

clock = pg.time.Clock()
delta_time = 0.0
commons.game_running = True

# Event loop
while commons.game_running:
    handle_input()
    update(delta_time)
    draw(screen)

    delta_time = 0.001 * clock.tick(commons.target_fps)
pg.quit()

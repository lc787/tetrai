import pygame as pg
import commons
from gamefield import GameField
from gameengine import CanvasObject


def handle_input():
    for event in pg.event.get():
        match event.type:
            case pg.QUIT:
                commons.game_running = False
            case pg.KEYDOWN:
                match event.key:
                    case pg.K_ESCAPE:
                        commons.game_running = False


def update(dt):
    for obj in commons.LOGIC_OBJECTS:
        obj.update(dt)


def draw(screen: pg.Surface):
    for obj in commons.CANVAS_OBJECTS:
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
    game_field = GameField(commons.width // 3, - 0.75*commons.height, 10, 40, 24, 2)
    game_field.draw_level = 1


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

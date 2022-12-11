from pygame import Surface, Rect, image
from commons import CANVAS_OBJECTS, LOGIC_OBJECTS


class CanvasObject:
    def __init__(self, x, y, width: int = None, height: int = None, image: image = None):
        self.__draw_level = 0
        if image is None:
            self.image = Surface((width, height))
        else:
            self.image = image
        self.rect: Rect = self.image.get_rect()
        self.rect.move_ip(x, y)
        super(CanvasObject, self).__init__()
        CANVAS_OBJECTS.append(self)

    @property
    def draw_level(self):
        return self.__draw_level

    # Draw order
    @draw_level.setter
    def draw_level(self, level: int):
        self.__draw_level = level
        super(CanvasObject, self).__init__()
        CANVAS_OBJECTS.sort(key=lambda x: x.draw_level)

    def draw(self):
        pass

    def kill(self):
        CANVAS_OBJECTS.remove(self)


class LogicObject:
    def __init__(self):
        LOGIC_OBJECTS.append(self)

    def update(self, dt: float):
        pass

    def kill(self):
        LOGIC_OBJECTS.remove(self)

from pygame import Surface, Rect, image

import commons

LOGIC_OBJECTS = []
# Draw order is maintained by the draw_level property
CANVAS_OBJECTS = []
KEYS = []
NOTIFIERS = {}
""" Contains notifiers by id """
# Example: {'1': {'1': [method1, method2]}
LISTENERS = {}


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
        CANVAS_OBJECTS.sort(key=lambda x: x.draw_level, reverse=True)

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


class Event:
    def __init__(self, message: str = None, **params):
        self.message = message
        self.params = params


class Notifier:
    def __init__(self):
        if len(NOTIFIERS.keys()) == 0:
            self.id = 0
        else:
            self.id = int(max(NOTIFIERS.keys())) + 1
        NOTIFIERS[self.id] = {}

    def notify(self, event: Event = Event()):
        """Notifies all subscribed listeners"""
        items = NOTIFIERS[self.id].items()
        for listener_id, methods in items:
            listener = LISTENERS[listener_id]
            if listener is not None:
                for method in methods:
                    method(listener)

    def connect(self, event: Event, listener, method):
        if listener.id not in NOTIFIERS[self.id].keys():
            NOTIFIERS[self.id][listener.id] = [method]
        else:
            NOTIFIERS[self.id][listener.id].append(method)

    def kill(self):
        NOTIFIERS[self.id] = {}


class Listener:
    def __init__(self):
        if len(LISTENERS.keys()) == 0:
            self.id = 0
        else:
            self.id = int(max(LISTENERS.keys())) + 1
        LISTENERS[self.id] = self

    def kill(self):
        for notifier_id in NOTIFIERS.keys():
            if self.id in NOTIFIERS[notifier_id]:
                NOTIFIERS[notifier_id].pop(self.id)
        LISTENERS.pop(self.id)


class Timer(Notifier, LogicObject):
    """Self ticking timer"""

    def __init__(self, delay, auto_start=True, auto_restart=False):

        self.delay = delay
        self.time = 0.0
        self.auto_restart = auto_restart
        self.can_tick = auto_start
        self.finished = False
        LogicObject.__init__(self)
        Notifier.__init__(self)

    def reset(self):
        self.can_tick = True
        self.finished = False
        self.time = 0.0

    def pause(self):
        self.can_tick = False

    def resume(self):
        self.can_tick = True

    def update(self, dt: float):
        if self.can_tick:
            self.time += dt
            if self.time > self.delay:
                if self.auto_restart:
                    self.can_tick = self.auto_restart
                    self.time = 0.0
                self.finished = True
                self.notify(Event("timeout"))


class Key(LogicObject):
    """Describes state of key"""

    def __init__(self, key_id: int):
        self.id = key_id
        self.pressed = False
        self.just_pressed = False
        LogicObject.__init__(self)

    def update(self, dt: float):
        if KEYS[self.id]:
            if not self.pressed:
                self.just_pressed = True
            else:
                self.just_pressed = False
            self.pressed = True
        else:
            self.pressed = False

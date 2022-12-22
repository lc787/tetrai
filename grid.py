import numpy as np
import pygame as pg

import commons
from gameengine import CanvasObject, Listener, Timer, LogicObject, Event


def piece_color(piece_type: int, theme):
    """Returns the color of a piece based on its type in ascii."""
    match piece_type:
        case 73:  # I
            return theme['palette']['block_cyan']
        case 74:  # J
            return theme['palette']['block_blue']
        case 76:  # L
            return theme['palette']['block_orange']
        case 79:  # O
            return theme['palette']['block_yellow']
        case 83:  # S
            return theme['palette']['block_green']
        case 84:  # T
            return theme['palette']['block_purple']
        case 90:  # Z
            return theme['palette']['block_red']
        case 88:  # X
            return theme['palette']['block_grey']
        case 0:  # Empty
            return theme['palette']['empty']
        case -1:  # Background
            return theme['palette']['background']


class Rotation:
    """ Rotation class for tetrominoes.
     Rotation is stored as an integer from 0 to 3, where 0 is the default rotation."""

    def __init__(self, value):
        self.__val = value

    def get(self):
        return self.__val

    def get_clockwise(self):
        return (self.__val + 1) % 4

    def get_counter_clockwise(self):
        return (self.__val - 1) % 4

    def set_clockwise(self):
        self.__val = (self.__val + 1) % 4

    def set_counter_clockwise(self):
        self.__val = (self.__val - 1) % 4


def piece_cfg(piece_type, rotation):
    """Returns the configuration of a piece based on its type and rotation.

    The configuration is a 4x4 matrix of 0s and 1s, where 1s represent the blocks of the piece.
    The matrix is rotated clockwise by the rotation parameter.
    For more info, see https://tetris.wiki/SRS"""
    # Used the configurations from https://codeincomplete.com/articles/javascript-tetris/
    cfg = 0x0000
    match piece_type:
        case 73:  # I
            match rotation.get():
                case 0:
                    cfg = 0x0F00
                case 1:
                    cfg = 0x2222
                case 2:
                    cfg = 0x00F0
                case 3:
                    cfg = 0x4444
        case 74:  # J
            match rotation.get():
                case 0:
                    cfg = 0x8E00
                case 1:
                    cfg = 0x6440
                case 2:
                    cfg = 0x0E20
                case 3:
                    cfg = 0x44C0
        case 76:  # L
            match rotation.get():
                case 0:
                    cfg = 0x2E00
                case 1:
                    cfg = 0x4460
                case 2:
                    cfg = 0x0E80
                case 3:
                    cfg = 0xC440
        case 79:  # O
            match rotation.get():
                case 0:
                    cfg = 0xCC00
                case 1:
                    cfg = 0xCC00
                case 2:
                    cfg = 0xCC00
                case 3:
                    cfg = 0xCC00
        case 83:  # S
            match rotation.get():
                case 0:
                    cfg = 0x6C00
                case 1:
                    cfg = 0x4620
                case 2:
                    cfg = 0x06C0
                case 3:
                    cfg = 0x8C40
        case 84:  # T
            match rotation.get():
                case 0:
                    cfg = 0x4E00
                case 1:
                    cfg = 0x4640
                case 2:
                    cfg = 0x0E40
                case 3:
                    cfg = 0x4C40
        case 90:  # Z
            match rotation.get():
                case 0:
                    cfg = 0xC600
                case 1:
                    cfg = 0x2640
                case 2:
                    cfg = 0x0C60
                case 3:
                    cfg = 0x4C80
    return cfg


class Grid:
    def __init__(self, cols, rows, dtype=np.int8):
        self.cols = cols
        self.rows = rows
        self.cells = np.zeros((rows, cols), dtype=dtype)

    def set(self, x, y, value):
        """Set value to specified cell. Unsafe, no bound-checking."""
        self.cells[self.rows - y - 1, x] = value

    def get(self, x, y):
        """Get value from specified cell. Unsafe, no bound-checking."""
        return self.cells[self.rows - y - 1, x]

    def get_safe(self, x, y):
        """Get value from specified cell. Returns -1 if out of bounds."""
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return -1
        return self.get(x, y)

    def reset(self):
        """Reset grid to all zeros."""
        self.cells = np.zeros((self.rows, self.cols), dtype=self.cells.dtype)


class DisplayGrid(Grid, CanvasObject):
    def __init__(self, x, y, cols, rows, cell_size, cell_margin, theme, transparent_mode=False, dtype=np.int8):
        Grid.__init__(self, cols, rows, dtype)
        # Drawings
        self.theme = theme
        self.cell_size = cell_size
        self.cell_margin = cell_margin
        self.transparent_mode = transparent_mode
        CanvasObject.__init__(self, x, y, width=cols * (cell_size + cell_margin) + cell_margin,
                              height=rows * (cell_size + cell_margin) + cell_margin)
        if transparent_mode:
            self.image.set_colorkey(theme['palette']['empty'])

    def set_theme(self, theme):
        self.theme = theme

    def show_piece(self, piece_type, rotation: Rotation, x, y):
        """Write a tetronimo to the grid. Unsafe, no bound-checking."""
        cfg = piece_cfg(piece_type, rotation)
        for i in range(16):
            if (cfg >> i) & 1:
                self.set(x + 3 - i % 4, y + i // 4, piece_type)

    def reset_and_show_piece(self, piece_type, rotation: Rotation, x, y):
        """Reset grid to all zeros and write a tetronimo to it. Unsafe, no bound-checking."""
        self.reset()
        self.show_piece(piece_type, rotation, x, y)

    def can_show_piece(self, piece_type, rotation: Rotation, x, y):
        """Check if a tetronimo can be written to the grid. Safe."""
        cfg = piece_cfg(piece_type, rotation)
        for i in range(16):
            if (cfg >> i) & 1:
                if self.get_safe(x + 3 - i % 4, y + i // 4) != 0:
                    return False

        return True

    def draw(self):
        for y in range(self.rows):
            for x in range(self.cols):
                piece_type = self.get(x, y)
                rect = pg.Rect(x * (self.cell_size + self.cell_margin) + self.cell_margin,
                               (self.rows - y - 1) * (self.cell_size + self.cell_margin) + self.cell_margin,
                               self.cell_size, self.cell_size)
                pg.draw.rect(self.image, piece_color(piece_type, self.theme), rect)


class PlayField(Listener, LogicObject):
    def __init__(self, x, y, block_size, block_margin, theme,
                 play_field_offset: tuple = (0, 0), hold_field_offset: tuple = (0, 0),
                 next_field_offset: tuple = (0, 0)):
        LogicObject.__init__(self)
        Listener.__init__(self)
        self.cols = 10
        self.rows = 40
        self.game_field = DisplayGrid(x + play_field_offset[0], y + play_field_offset[1], self.cols, self.rows,
                                      block_size, block_margin, theme)
        self.game_field.draw_level = 1
        self.ghost_field = \
            DisplayGrid(x + play_field_offset[0], y + play_field_offset[1], self.cols, self.rows, block_size,
                        block_margin, theme, transparent_mode=True)
        self.ghost_field.draw_level = 2
        self.hold_field = \
            DisplayGrid(x + hold_field_offset[0], y + hold_field_offset[1], 4, 4, block_size, 0, theme,
                        transparent_mode=True)
        self.hold_field.draw_level = 3

        self.bag = []
        self.max_next_pieces = 5
        next_fields_margin = 0
        self.next_fields = [DisplayGrid(x + next_field_offset[0],
                                        y + next_field_offset[1] + i * 4 * (
                                                    block_size + next_fields_margin) + 3 * next_fields_margin,
                                        4, 4, block_size, next_fields_margin, theme, transparent_mode=True)
                            for i in range(self.max_next_pieces)]
        for field in self.next_fields:
            field.draw_level = 4

        self.fall_timer = Timer(0.2)
        self.lock_timer = Timer(0.5, auto_start=False)
        self.rotation_timer = Timer(0.1)
        self.move_timer = Timer(0.1)
        self.fast_move_timer = Timer(0.01)

        # Used keys
        self.k_clockwise = commons.key_binds['clockwise']
        self.k_counter_clockwise = commons.key_binds['counter_clockwise']
        self.k_switch = commons.key_binds['switch']
        self.k_hard_drop = commons.key_binds['hard_drop']
        self.k_soft_drop = commons.key_binds['soft_drop']
        self.k_left = commons.key_binds['left']
        self.k_right = commons.key_binds['right']
        self.k_180 = commons.key_binds['180']

        # Game flags
        self.game_started = False
        self.game_over = False
        self.can_switch = True
        self.ghost_mode = True
        self.lock_requests = 0
        self.max_lock_requests = 15
        self.score = 0

        # Pieces
        self.current_piece_type = None
        self.current_piece_rotation = Rotation(0)
        self.current_piece_x = 0
        self.current_piece_y = 0
        self.hold_piece_type = None

        # Connect stuff after everything is initialised
        self.fall_timer.connect(Event("timeout"), self, self.on_natural_drop_piece)
        self.lock_timer.connect(Event("timeout"), self, self.on_lock_delay)
        # Start!
        self.start_game()

    # Field logic
    def clean_row(self, row):
        """Remove a row from the grid and move all rows above it down."""
        self.game_field.cells[row, :] = 0
        # Shift all rows above down
        self.game_field.cells[:row + 1, :] = np.roll(self.game_field.cells[:row + 1, :], 1, axis=0)

    def clean_rows(self):
        """Clean all full rows and return the number of rows cleaned."""
        cleaned_rows = 0
        for row in range(self.rows):
            # Are all pieces non-zero?
            if np.all(self.game_field.cells[row, :]):
                self.clean_row(row)
                cleaned_rows += 1
        return cleaned_rows

    # Piece bag
    def pop_bag(self):
        """Return the next pieces from the bag"""
        self.can_switch = True
        # If there are not enough pieces to show, extend the bag
        if len(self.bag) <= self.max_next_pieces + 1:
            batch = ["I", "I", "J", "J", "L", "L", "O", "O", "S", "S", "T", "T", "Z", "Z"]
            np.random.shuffle(batch)
            batch = [ord(c) for c in batch]
            self.bag.extend(batch)
        self.populate_next_field()
        return self.bag.pop(0)

    def populate_next_field(self):
        """Show the next pieces on the "next fields". Run after every piece grab"""
        # Peek the bag
        next_pieces = self.bag[1:self.max_next_pieces + 1]
        for i, field in enumerate(self.next_fields):
            field.reset_and_show_piece(next_pieces[i], Rotation(0), 0, 0)

    # Piece logic
    def lock_piece(self):
        cfg = piece_cfg(self.current_piece_type, self.current_piece_rotation)
        # Lock out flag. If it's above the vanish zone in its entirety (y = 20), it's game over
        lock_out = True
        for i in range(16):
            if (cfg >> i) & 1:
                x = self.current_piece_x + 3 - i % 4
                y = self.current_piece_y + i // 4
                if y < 20:
                    lock_out = False
                self.game_field.set(x, y, self.current_piece_type)
        if lock_out:
            self.game_over = True
            self.game_started = False
        else:
            rows = self.clean_rows()
            if rows:
                self.score += rows * 100

            self.spawn_piece(piece_type=self.pop_bag())

    def on_natural_drop_piece(self, event: Event):
        """Gets called when the piece is supposed to fall. If there is no space left to fall, lock!"""
        if self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                          self.current_piece_x, self.current_piece_y - 1):
            self.current_piece_y -= 1
            self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                  self.current_piece_x, self.current_piece_y)
            self.fall_timer.reset()
            self.request_lock()

    def spawn_piece(self, piece_type):
        """Spawn a piece at default spawn position"""
        self.current_piece_x = self.cols // 2 - 2
        self.current_piece_y = self.rows // 2
        self.current_piece_rotation = Rotation(0)
        self.current_piece_type = piece_type

        self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                              self.current_piece_x, self.current_piece_y)

    def start_game(self):
        self.spawn_piece(self.pop_bag())

    def on_lock_delay(self, event: Event = None):
        """Gets called when the lock delay is over. Lock the piece."""
        self.lock_piece()

    def request_lock(self):
        """Request a lock. If the max requests are reached, lock the piece. Otherwise, reset the natural fall timer"""
        self.lock_timer.reset()
        if not self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                              self.current_piece_x, self.current_piece_y - 1):
            self.lock_requests += 1
            if self.lock_requests >= self.max_lock_requests:
                self.lock_piece()
        else:
            self.lock_requests = 0
            self.lock_timer.reset()
            self.lock_timer.pause()

    def update(self, dt: float):
        desired_x = self.current_piece_x
        desired_y = self.current_piece_y
        desired_rotation = Rotation(self.current_piece_rotation.get())
        move_command = False
        rotate_command = False
        if self.k_soft_drop.pressed:
            desired_y -= 1
            move_command = True
        if self.k_left.pressed:
            desired_x -= 1
            move_command = True
        if self.k_right.pressed:
            desired_x += 1
            move_command = True
        if self.k_clockwise.just_pressed:
            desired_rotation.set_clockwise()
            rotate_command = True
        if self.k_counter_clockwise.just_pressed:
            desired_rotation.set_counter_clockwise()
            rotate_command = True
        if self.k_180.just_pressed:
            desired_rotation.set_clockwise()
            desired_rotation.set_clockwise()
            rotate_command = True
        if self.k_hard_drop.just_pressed:
            while self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                 self.current_piece_x, self.current_piece_y - 1):
                self.current_piece_y -= 1
            self.lock_piece()
        elif self.k_switch.just_pressed and self.can_switch:
            self.can_switch = False
            if self.hold_piece_type is None:
                self.hold_piece_type = self.current_piece_type
                self.current_piece_type = self.pop_bag()
                self.hold_field.reset_and_show_piece(self.hold_piece_type, Rotation(0), 0, 0)
                self.spawn_piece(self.current_piece_type)
            else:
                self.hold_piece_type, self.current_piece_type = self.current_piece_type, self.hold_piece_type
                self.hold_field.reset_and_show_piece(self.hold_piece_type, Rotation(0), 0, 0)
                self.spawn_piece(self.current_piece_type)

        if move_command:
            if self.move_timer.finished:
                if self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                  desired_x, desired_y):
                    self.current_piece_x = desired_x
                    self.current_piece_y = desired_y
                    self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                          self.current_piece_x, self.current_piece_y)
                    self.move_timer.reset()
                    # Lock requests reset on move
                    if not self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                          self.current_piece_x, self.current_piece_y - 1):

                        self.request_lock()
                    else:
                        self.lock_requests = 0
        if rotate_command:
            if self.rotation_timer.finished:
                request = False
                if self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                  self.current_piece_x, self.current_piece_y):
                    self.current_piece_rotation = Rotation(desired_rotation.get())
                    self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                          self.current_piece_x, self.current_piece_y)
                    self.rotation_timer.reset()
                    request = True
                # Try wall kick
                else:
                    if self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                      self.current_piece_x - 1, self.current_piece_y):
                        self.current_piece_x -= 1
                        self.current_piece_rotation = Rotation(desired_rotation.get())
                        self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                              self.current_piece_x, self.current_piece_y)
                        self.rotation_timer.reset()
                        request = True
                    elif self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                        self.current_piece_x + 1, self.current_piece_y):
                        self.current_piece_x += 1
                        self.current_piece_rotation = Rotation(desired_rotation.get())
                        self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                              self.current_piece_x, self.current_piece_y)
                        self.rotation_timer.reset()
                        request = True
                # Experimental floor kick
                    elif self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                        self.current_piece_x, self.current_piece_y + 1):
                        self.current_piece_y += 1
                        self.current_piece_rotation = Rotation(desired_rotation.get())
                        self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                              self.current_piece_x, self.current_piece_y)
                        self.rotation_timer.reset()
                        request = True
                if request:
                    if not self.ghost_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                           self.current_piece_x, self.current_piece_y - 1):
                        self.request_lock()
                    else:
                        self.lock_requests = 0

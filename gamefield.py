import numpy as np
import pygame as pg
from gameengine import LogicObject, CanvasObject
from commons import color_theme


# Get color based on piece type id
def get_color(i: int):
    match i:
        case 1:
            return color_theme.block_cyan
        case 2:
            return color_theme.block_blue
        case 3:
            return color_theme.block_orange
        case 4:
            return color_theme.block_yellow
        case 5:
            return color_theme.block_green
        case 6:
            return color_theme.block_purple
        case 7:
            return color_theme.block_red
        case 8:
            return color_theme.block_grey
        case 0:
            return color_theme.empty
        case _:
            raise ValueError("Invalid block type")


class Piece:
    def __init__(self, piece_type: str, rotation: int):
        self.piece_type = piece_type
        self.rotation = rotation


    @property
    def cfg(self):
        # Used the configurations from https://codeincomplete.com/articles/javascript-tetris/
        # https://static.wikia.nocookie.net/tetrisconcept/images/3/3d/SRS-pieces.png/revision/latest?cb=20060626173148
        cfg = 0x0000
        match self.piece_type:
            case "I":
                match self.rotation:
                    case 0:
                        cfg = 0x0F00
                    case 1:
                        cfg = 0x222
                    case 2:
                        cfg = 0x00F0
                    case 3:
                        cfg = 0x4444
            case "J":
                match self.rotation:
                    case 0:
                        cfg = 0x8E00
                    case 1:
                        cfg = 0x6440
                    case 2:
                        cfg = 0x0E20
                    case 3:
                        cfg = 0x44C0
            case "L":
                match self.rotation:
                    case 0:
                        cfg = 0x2E00
                    case 1:
                        cfg = 0x4460
                    case 2:
                        cfg = 0x0E80
                    case 3:
                        cfg = 0xC440
            case "O":
                match self.rotation:
                    case 0:
                        cfg = 0xCC00
                    case 1:
                        cfg = 0xCC00
                    case 2:
                        cfg = 0xCC00
                    case 3:
                        cfg = 0xCC00
            case "S":
                match self.rotation:
                    case 0:
                        cfg = 0x6C00
                    case 1:
                        cfg = 0x4620
                    case 2:
                        cfg = 0x06C0
                    case 3:
                        cfg = 0x8C40
            case "T":
                match self.rotation:
                    case 0:
                        cfg = 0x4E00
                    case 1:
                        cfg = 0x4640
                    case 2:
                        cfg = 0x0E40
                    case 3:
                        cfg = 0x4C40
            case "Z":
                match self.rotation:
                    case 0:
                        cfg = 0xC600
                    case 1:
                        cfg = 0x2640
                    case 2:
                        cfg = 0x0C60
                    case 3:
                        cfg = 0x4C80
        return cfg

    @property
    def type_id(self):
        match self.piece_type:
            case "I":
                return 1
            case "J":
                return 2
            case "L":
                return 3
            case "O":
                return 4
            case "S":
                return 5
            case "T":
                return 6
            case "Z":
                return 7

    def rotate_clockwise(self):
        self.rotation = (self.rotation + 1) % 4

    def rotate_counterclockwise(self):
        self.rotation = (self.rotation - 1) % 4


class GameField(CanvasObject, LogicObject):
    def __init__(self, x, y, cols, rows, block_size, block_margin):
        self.cols = cols
        self.rows = rows
        self.field = np.zeros((self.rows, self.cols), dtype=np.int8)
        # A collision-less field to draw the piece that is currently falling
        self.show_field = np.zeros((self.rows, self.cols), dtype=np.int8)

        self.next_pieces = []
        self.show_next = 6

        self.timer = 0.0
        self.delay = 1.0
        self.game_started = False
        self.game_over = False

        self.last_piece = None
        self.piece_x = 0
        self.piece_y = 0
        self.reserve_piece = None
        self.can_switch = True

        # Render parameters
        self.block_size = block_size
        self.block_margin = block_margin

        width = cols * (block_size + block_margin) + block_margin
        height = rows * (block_size + block_margin) + block_margin
        super(GameField, self).__init__(x, y, width, height)

    def set(self, x, y, value: int):
        self.field[self.rows - y - 1, x] = value

    def get(self, x, y):
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return -1
        return self.field[self.rows - y - 1, x]

    def set_show_field(self, x, y, value: int):
        self.show_field[self.rows - y - 1, x] = value

    def get_show_field(self, x, y):
        return self.show_field[self.rows - y - 1, x]

    def __clean_row(self, row):
        self.field[row, :] = 0
        self.field[0:row, :] = np.roll(self.field[0:row, :], 1, axis=0)

    # Called only when a piece is placed
    def __clean_rows(self):
        for row in range(self.rows):
            # Does 0 exist in the row?
            if np.all(self.field[row, :]):
                self.__clean_row(row)

    # Extend the next pieces list when needed
    def __extend_bag(self):
        # Standard ruleset
        piece_bag = ["I", "I", "J", "J", "L", "L", "O", "O", "S", "S", "T", "T", "Z", "Z"]
        np.random.shuffle(piece_bag)
        self.next_pieces.extend(piece_bag)

    # Replace current piece with the next one in the bag
    def __replace_from_bag(self):
        # If there are not enough pieces to show, extend the bag
        if len(self.next_pieces) <= self.show_next:
            self.__extend_bag()
        self.last_piece = Piece(self.next_pieces.pop(0), 0)

    # Get the next piece in the bag
    def get_next_pieces(self):
        return self.next_pieces[:self.show_next]

    # Spawns current piece. 'spawn' doesn't imply that the piece is placed on the field
    def spawn_piece(self):
        # at x 3
        self.piece_x = self.cols // 2 - 2
        # at y 20
        self.piece_y = self.cols // 2
        # Block out
        if not self.__can_place_piece(self.last_piece, self.piece_x, self.piece_y):
            self.game_over = True
            self.game_started = False
            print("Game over")
        self.can_switch = True

    def place_piece(self, piece: Piece, x, y):
        cfg = piece.cfg
        self.reset_show_field()
        for i in range(16):
            if (cfg >> i) & 1:
                self.set_show_field(x + 3 - i % 4, y + i // 4, piece.type_id)

    def lock_piece(self, piece: Piece, x, y):
        cfg = piece.cfg
        # Lock the piece. If it's above the vanish zone in its entirety (y = 20), it's game over
        lock_out = True
        for i in range(16):
            if (cfg >> i) & 1:
                if y + i // 4 < 20:
                    lock_out = False
                self.set(x + 3 - i % 4, y + i // 4, piece.type_id)
        if lock_out:
            self.game_over = True
            self.game_started = False
            print("Game over (lock out)")
        else:
            self.__clean_rows()

    # Used to de-spawn the active piece from the board (e.g. when switching)
    def hide_piece(self):
        if self.last_piece is not None:
            cfg = self.last_piece.cfg
            for i in range(16):
                if (cfg >> i) & 1:
                    self.set_show_field(self.piece_x + 3 - i % 4, self.piece_y + i // 4, 0)

    def reset_show_field(self):
        self.show_field = np.zeros((self.rows, self.cols), dtype=np.int8)

    # Switches, de-spawns, spawns and places piece
    def switch_piece(self):
        if self.reserve_piece is None:
            self.reserve_piece = self.last_piece
            self.__replace_from_bag()
        else:
            tmp_piece = self.last_piece
            self.last_piece = self.reserve_piece
            self.reserve_piece = tmp_piece
        self.reset_show_field()
        self.spawn_piece()
        self.place_piece(self.last_piece, self.piece_x, self.piece_y)

    def __can_place_piece(self, piece: Piece, x, y):
        cfg = piece.cfg
        for i in range(16):
            if (cfg >> i) & 1:
                if self.get(x + 3 - i % 4, y + i // 4) != 0:
                    return False
        return True

    def update(self, dt):
        self.timer += dt
        # If one delay has passed, move the piece down
        if not self.game_over and self.timer > self.delay:
            self.timer = 0.0
            # Game just started, spawn a piece
            if not self.game_started:
                print("Game started")
                self.__replace_from_bag()
                self.spawn_piece()
                self.place_piece(self.last_piece, self.piece_x, self.piece_y)
                self.game_started = True
            # Piece falls
            elif self.__can_place_piece(self.last_piece, self.piece_x, self.piece_y - 1):
                self.reset_show_field()
                self.piece_y -= 1
                self.place_piece(self.last_piece, self.piece_x, self.piece_y)
            # If the piece can't fall, place it and spawn a new one
            else:
                self.reset_show_field()
                self.lock_piece(self.last_piece, self.piece_x, self.piece_y)
                self.__replace_from_bag()
                self.spawn_piece()
                self.place_piece(self.last_piece, self.piece_x, self.piece_y)

        # User input
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            self.rect.x -= 10 * dt
            if self.__can_place_piece(self.last_piece, self.piece_x - 1, self.piece_y):
                self.reset_show_field()
                self.piece_x -= 1
                self.place_piece(self.last_piece, self.piece_x, self.piece_y)
        if keys[pg.K_RIGHT]:
            if self.__can_place_piece(self.last_piece, self.piece_x + 1, self.piece_y):
                self.reset_show_field()
                self.piece_x += 1
                self.place_piece(self.last_piece, self.piece_x, self.piece_y)
        if keys[pg.K_DOWN]:
            if self.__can_place_piece(self.last_piece, self.piece_x, self.piece_y - 1):
                self.reset_show_field()
                self.piece_y -= 1
                self.place_piece(self.last_piece, self.piece_x, self.piece_y)
        if keys[pg.K_q]:
            self.last_piece.rotate_counterclockwise()
            if not self.__can_place_piece(self.last_piece, self.piece_x, self.piece_y):
                self.last_piece.rotate_clockwise()
        if keys[pg.K_e]:
            self.last_piece.rotate_clockwise()
            if not self.__can_place_piece(self.last_piece, self.piece_x, self.piece_y):
                self.last_piece.rotate_counterclockwise()
        if keys[pg.K_SPACE]:
            if self.can_switch:
                self.can_switch = False
                self.switch_piece()

    def draw(self):
        self.image.fill(color_theme.block_red)
        for y in range(self.rows):
            for x in range(self.cols):
                color = get_color(self.get(x, y))
                pg.draw.rect(self.image, color,
                             [(self.block_margin + self.block_size) * x + self.block_margin,
                              ((self.block_margin + self.block_size) * (self.rows-y+1) + self.block_margin),
                              self.block_size, self.block_size])
                show_field_color_index = self.get_show_field(x, y)
                # TODO: fix color of falling piece
                if show_field_color_index != 0:
                    pg.draw.rect(self.image, color,
                                 [(self.block_margin + self.block_size) * x + self.block_margin,
                                  ((self.block_margin + self.block_size) * (self.rows - y+1) + self.block_margin),
                                  self.block_size, self.block_size])

import numpy as np
import pygame as pg
from gameengine import LogicObject, CanvasObject
from commons import color_theme, color_theme2

color_themes = [color_theme, color_theme2]


# Get color based on piece type id
def get_color(i: int, color_theme):
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
                        cfg = 0x2222
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
        self.ghost_field = np.zeros((self.rows, self.cols), dtype=np.int8)

        self.bag = []
        self.show_next = 6

        self.fall_delay = 1.0
        self.fall_timer = 0.0
        self.rotation_delay = 0.1
        self.rotation_timer = 0.0
        self.move_delay = 0.1
        self.move_timer = 0.0
        self.hard_drop_delay = 0.6
        self.hard_drop_timer = 0.0

        self.left_pressed = False
        self.left_just_pressed = False
        self.right_pressed = False
        self.right_just_pressed = False
        self.down_pressed = False
        self.down_just_pressed = False
        self.up_pressed = False
        self.up_just_pressed = False
        self.space_pressed = False
        self.space_just_pressed = False
        self.q_pressed = False
        self.q_just_pressed = False
        self.e_pressed = False
        self.e_just_pressed = False
        self.color_theme = 1

        self.game_started = False
        self.game_over = False

        # Actions refer to successful user inputs
        self.registered_actions_queue = [{"type": "game", "game": "start"}]
        self.max_registered_actions_queue = 10
        self.current_piece = None
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

    """Action queue"""

    def register_action(self, action):
        if len(self.registered_actions_queue) == self.max_registered_actions_queue:
            self.registered_actions_queue.pop(0)
        self.registered_actions_queue.append(action)
        print(f"Registered action: {action}")

    def get_last_action(self):
        return self.registered_actions_queue[-1]

    """Game field"""

    def set_field(self, x, y, value: int):
        self.field[self.rows - y - 1, x] = value

    def get_field(self, x, y):
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return -1
        return self.field[self.rows - y - 1, x]

    def reset_field(self):
        self.field = np.zeros((self.rows, self.cols), dtype=np.int8)

    def clean_row(self, row):
        self.field[row, :] = 0
        # Shift all rows above down
        self.field[:row + 1, :] = np.roll(self.field[:row + 1, :], 1, axis=0)

    # Should be called only when a piece is locked
    def clean_rows(self):
        cleaned_rows = 0
        for row in range(self.rows):
            # Are all pieces non-zero?
            if np.all(self.field[row, :]):
                self.clean_row(row)
                cleaned_rows += 1
        return cleaned_rows

    """Ghost field"""

    def set_ghost_field(self, x, y, value: int):
        self.ghost_field[self.rows - y - 1, x] = value

    def get_ghost_field(self, x, y):
        if x < 0 or x >= self.cols or y < 0 or y >= self.rows:
            return -1
        return self.ghost_field[self.rows - y - 1, x]

    def reset_ghost_field(self):
        self.ghost_field = np.zeros((self.rows, self.cols), dtype=np.int8)

    """Piece Bag"""

    # Replace current piece with the next one in the bag
    def pop_bag(self):
        # If there are not enough pieces to show, extend the bag
        if len(self.bag) <= self.show_next:
            batch = ["I", "I", "J", "J", "L", "L", "O", "O", "S", "S", "T", "T", "Z", "Z"]
            np.random.shuffle(batch)
            self.bag.extend(batch)
        self.current_piece = Piece(self.bag.pop(0), 0)

    # Get the next pieces in the bag
    def peek_bag(self):
        return self.bag[:self.show_next]

    """Pieces"""

    # Spawns current piece. 'spawn' doesn't imply that the piece is placed on the field
    def reset_piece(self):
        # at x 3
        self.piece_x = self.cols // 2 - 2
        print(self.piece_x)
        # at y 20
        self.piece_y = self.rows // 2
        print(self.piece_y)
        # Block out
        if not self.__can_place_piece(self.current_piece, self.piece_x, self.piece_y):
            self.game_over = True
            self.game_started = False
            self.can_switch = False
            print("Game over")

    def place_piece(self, piece: Piece, x, y):
        cfg = piece.cfg
        self.reset_ghost_field()
        for i in range(16):
            if (cfg >> i) & 1:
                self.set_ghost_field(x + 3 - i % 4, y + i // 4, piece.type_id)

    def show_ghost(self):
        ghost_y = self.piece_y
        while self.__can_place_piece(self.current_piece, self.piece_x, ghost_y - 1):
            ghost_y -= 1
        self.place_piece(self.current_piece, self.piece_x, ghost_y)

    def lock_piece(self, piece: Piece, x, y):
        cfg = piece.cfg
        # Lock the piece. If it's above the vanish zone in its entirety (y = 20), it's game over
        lock_out = True
        for i in range(16):
            if (cfg >> i) & 1:
                if y + i // 4 < 20:
                    lock_out = False
                self.set_field(x + 3 - i % 4, y + i // 4, piece.type_id)
        if lock_out:
            self.game_over = True
            self.game_started = False
            print("Game over (lock out)")
        else:
            self.register_action({"type": "piece", "piece": "lock", "piece_type": piece.piece_type})
            cleaned = self.clean_rows()
            if cleaned > 0:
                action = {"type": "line_clear", "line_clear": "cleaned", "cleaned": cleaned, "special": False}
                if cleaned >= 2 and piece.piece_type == 'T':
                    last_action = self.get_last_action()
                    # TODO: what if queue is filled with something else by the time we get here?
                    if last_action['type'] == 'piece' and last_action['piece'] == 'rotate':
                        # TODO: check for 3 corners out of 4 to be occupied for 3-corner T-slot
                        action['special'] = True
                        action.update({"special_type": "immobile T-spin"})
                self.register_action(action)
            self.can_switch = True

    # Used to de-spawn the active piece from the board (e.g. when switching)
    def hide_piece(self):
        if self.current_piece is not None:
            cfg = self.current_piece.cfg
            for i in range(16):
                if (cfg >> i) & 1:
                    self.set_ghost_field(self.piece_x + 3 - i % 4, self.piece_y + i // 4, 0)

    # Switches, de-spawns, spawns and places piece
    def switch_piece(self):
        if self.reserve_piece is None:
            self.reserve_piece = self.current_piece
            self.pop_bag()
        else:
            tmp_piece = self.current_piece
            self.current_piece = self.reserve_piece
            self.reserve_piece = tmp_piece
        self.register_action({"type": "piece", "piece": "switch"})
        self.reset_ghost_field()
        self.reset_piece()
        self.place_piece(self.current_piece, self.piece_x, self.piece_y)

    def __can_place_piece(self, piece: Piece, x, y):
        cfg = piece.cfg
        for i in range(16):
            if (cfg >> i) & 1:
                if self.get_field(x + 3 - i % 4, y + i // 4) != 0:
                    return False
        return True

    # If it can place the piece, place it and return True. False otherwise
    def try_place_piece(self, piece: Piece, x, y):
        if not self.__can_place_piece(piece, x, y):
            return False
        self.place_piece(piece, x, y)
        return True

    def update(self, dt):
        self.fall_timer += dt
        self.rotation_timer += dt
        self.move_timer += dt
        # If one delay has passed, move the piece down
        if not self.game_over and self.fall_timer > self.fall_delay:
            self.fall_timer = 0.0
            # Game just started, spawn a piece
            if not self.game_started:
                print("Game started")
                self.pop_bag()
                self.reset_piece()
                self.place_piece(self.current_piece, self.piece_x, self.piece_y)
                self.game_started = True
            # Piece falls
            elif self.__can_place_piece(self.current_piece, self.piece_x, self.piece_y - 1):
                self.reset_ghost_field()
                self.piece_y -= 1
                self.place_piece(self.current_piece, self.piece_x, self.piece_y)
            # If the piece can't fall, place it and spawn a new one
            else:
                self.reset_ghost_field()
                self.lock_piece(self.current_piece, self.piece_x, self.piece_y)
                self.pop_bag()
                self.reset_piece()
                self.place_piece(self.current_piece, self.piece_x, self.piece_y)

        # User input
        # todo: move to commons
        keys = pg.key.get_pressed()
        if keys[pg.K_LEFT]:
            if not self.left_pressed:
                self.left_just_pressed = True
            else:
                self.left_just_pressed = False
            self.left_pressed = True
        else:
            self.left_pressed = False

        if keys[pg.K_RIGHT]:
            if not self.right_pressed:
                self.right_just_pressed = True
            else:
                self.right_just_pressed = False
            self.right_pressed = True
        else:
            self.right_pressed = False

        if keys[pg.K_DOWN]:
            if not self.down_pressed:
                self.down_just_pressed = True
            else:
                self.down_just_pressed = False
            self.down_pressed = True
        else:
            self.down_pressed = False

        if keys[pg.K_UP]:
            if not self.up_pressed:
                self.up_just_pressed = True
            else:
                self.up_just_pressed = False
            self.up_pressed = True
        else:
            self.up_pressed = False

        if keys[pg.K_SPACE]:
            if not self.space_pressed:
                self.space_just_pressed = True
            else:
                self.space_just_pressed = False
            self.space_pressed = True
        else:
            self.space_pressed = False
        if keys[pg.K_q]:
            if not self.q_pressed:
                self.q_just_pressed = True
            else:
                self.q_just_pressed = False
            self.q_pressed = True
        else:
            self.q_pressed = False

        if keys[pg.K_e]:
            if not self.e_pressed:
                self.e_just_pressed = True
            else:
                self.e_just_pressed = False
            self.e_pressed = True
        else:
            self.e_pressed = False

        if self.move_timer > self.move_delay:
            if self.left_pressed:
                if self.__can_place_piece(self.current_piece, self.piece_x - 1, self.piece_y):
                    self.move_timer = 0.0
                    self.reset_ghost_field()
                    self.piece_x -= 1
                    self.place_piece(self.current_piece, self.piece_x, self.piece_y)
                    self.register_action({"type": "piece", "piece": "move", "move": "left"})

            if self.right_pressed:
                if self.__can_place_piece(self.current_piece, self.piece_x + 1, self.piece_y):
                    self.move_timer = 0.0
                    self.reset_ghost_field()
                    self.piece_x += 1
                    self.place_piece(self.current_piece, self.piece_x, self.piece_y)
                    self.register_action({"type": "piece", "piece": "move", "move": "right"})

            if self.down_pressed:
                if self.__can_place_piece(self.current_piece, self.piece_x, self.piece_y - 1):
                    self.move_timer = 0.0
                    self.reset_ghost_field()
                    self.piece_y -= 1
                    self.place_piece(self.current_piece, self.piece_x, self.piece_y)
                    self.register_action({"type": "piece", "piece": "move", "move": "down"})

        if self.q_just_pressed:
            self.current_piece.rotate_counterclockwise()
            placed = True
            # Simple wall kick algorithm
            if not self.__can_place_piece(self.current_piece, self.piece_x, self.piece_y):
                if self.__can_place_piece(self.current_piece, self.piece_x + 1, self.piece_y):
                    self.place_piece(self.current_piece, self.piece_x + 1, self.piece_y)
                elif self.__can_place_piece(self.current_piece, self.piece_x - 1, self.piece_y):
                    self.place_piece(self.current_piece, self.piece_x - 1, self.piece_y)
                else:
                    self.current_piece.rotate_clockwise()
                    placed = False
            if placed:
                print("HI")
                self.register_action({"type": "piece", "piece": "rotate", "direction": "counterclockwise"})
                self.rotation_timer = 0.0
        if self.e_just_pressed:
            self.current_piece.rotate_clockwise()
            placed = True
            # Simple wall kick algorithm
            if not self.__can_place_piece(self.current_piece, self.piece_x, self.piece_y):
                if self.__can_place_piece(self.current_piece, self.piece_x + 1, self.piece_y):
                    self.place_piece(self.current_piece, self.piece_x + 1, self.piece_y)
                elif self.__can_place_piece(self.current_piece, self.piece_x - 1, self.piece_y):
                    self.place_piece(self.current_piece, self.piece_x - 1, self.piece_y)
                else:
                    self.current_piece.rotate_counterclockwise()
                    placed = False
            if placed:
                self.register_action({"type": "piece", "piece": "rotate", "direction": "clockwise"})
                self.rotation_timer = 0.0
        if self.space_just_pressed:
            if self.can_switch:
                self.can_switch = False
                self.switch_piece()

    def draw(self):
        self.image.fill(color_theme.background)
        for y in range(self.rows):
            for x in range(self.cols):
                color = get_color(self.get_field(x, y), color_themes[self.color_theme])
                pg.draw.rect(self.image, color,
                             [(self.block_margin + self.block_size) * x + self.block_margin,
                              ((self.block_margin + self.block_size) * (self.rows - y - 1) + self.block_margin),
                              self.block_size, self.block_size])
                ghost_field_color_index = self.get_ghost_field(x, y)
                color = get_color(ghost_field_color_index, color_themes[self.color_theme])
                # TODO: fix color of falling piece
                if ghost_field_color_index != 0:
                    pg.draw.rect(self.image, color,
                                 [(self.block_margin + self.block_size) * x + self.block_margin,
                                  ((self.block_margin + self.block_size) * (self.rows - y - 1) + self.block_margin),
                                  self.block_size, self.block_size])

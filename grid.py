import numpy as np
import pygame as pg

import commons
import gameengine
from gameengine import CanvasObject, Listener, Timer, LogicObject, Event, Notifier


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

    def show_piece(self, piece_type, rotation: Rotation, x, y, color_override=None):
        """Write a tetronimo to the grid. Unsafe, no bound-checking."""
        cfg = piece_cfg(piece_type, rotation)
        for i in range(16):
            if (cfg >> i) & 1:
                piece_type = color_override if color_override is not None else piece_type
                self.set(x + 3 - i % 4, y + i // 4, piece_type)

    def reset_and_show_piece(self, piece_type, rotation: Rotation, x, y, color_override=None):
        """Reset grid to all zeros and write a tetronimo to it. Unsafe, no bound-checking."""
        self.reset()
        self.show_piece(piece_type, rotation, x, y, color_override=color_override)

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

    def get_column_height(self, i):
        """Get the height of the specified column. Safe"""
        for y in range(self.rows - 1, 0, -1):
            if self.get_safe(i, y) != 0:
                return y
        return 0

    def get_column_holes(self, i, col_height=None):
        """Get the number of holes of the specified column. Safe"""
        holes = 0
        height = col_height if col_height is not None else self.get_column_height(i)
        for y in range(self.rows):
            if self.get_safe(i, y) == 0:
                if height > y:
                    holes += 1
        return holes


class PlayField(Notifier, Listener, LogicObject):
    def __init__(self, x, y, block_size, block_margin, theme, key_map=commons.key_binds,
                 play_field_offset: tuple = (0, 0), hold_field_offset: tuple = (0, 0),
                 next_field_offset: tuple = (0, 0),
                 environment: Listener = None,
                 # Score schemes. When designing, these should scale with the official tetris score guideline.
                 # See https://tetris.wiki/Scoring. (also see set_score())
                 # Positive values encourage the model to explore the action space.
                 agent_score_scheme: dir = {'move_delta_score': 1, 'game_over_delta_score': -1000,
                                            'non_line_clear_delta_score': 8},
                 agent_mode=False):
        LogicObject.__init__(self)
        Listener.__init__(self)
        Notifier.__init__(self)
        self.cols = 10
        self.rows = 40
        self.theme = theme

        # Init fields
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

        # Init game timers
        self.fall_timer = Timer(0.2)
        self.lock_timer = Timer(0.5, auto_start=False)
        self.rotation_timer = Timer(0.1)
        self.move_timer = Timer(0.1)
        self.fast_move_timer = Timer(0.01)
        self.delta_points_render_timer = Timer(2, auto_start=False)

        # Used keys
        self.k_clockwise = key_map['clockwise']
        self.k_counter_clockwise = key_map['counter_clockwise']
        self.k_switch = key_map['switch']
        self.k_hard_drop = key_map['hard_drop']
        self.k_soft_drop = key_map['soft_drop']
        self.k_left = key_map['left']
        self.k_right = key_map['right']
        self.k_180 = key_map['180']
        self.k_restart = key_map['restart']
        self.k_pause = key_map['pause']

        # Game flags
        self.game_started = False
        self.game_over = False
        self.game_paused = False
        self.can_switch = True
        self.ghost_mode = True
        self.lock_requests = 0
        self.max_lock_requests = 15

        # Game state
        font = pg.font.SysFont('Arial', 20)
        score_render = font.render('Score: 0', True, theme['palette']['text'])
        delta_score_render = font.render('+0', True, theme['palette']['text'])
        self.score_panel = CanvasObject(x - 300, y, image=score_render)
        self.score_panel.draw_level = 5
        self.delta_score_panel = CanvasObject(x - 300, y + 20, image=delta_score_render)
        self.delta_score_panel.draw_level = 5
        self.delta_score_panel.invisible = True
        self.score = 0
        # Last score change, used by Reinforcement Learning agents
        self.last_delta_score = 0
        # Score gained for any move
        self.move_delta_score = agent_score_scheme['move_delta_score']
        # Game lost score
        self.game_over_delta_score = agent_score_scheme['game_over_delta_score']
        self.non_line_clear_delta_score = agent_score_scheme['non_line_clear_delta_score']
        self.level = 1
        self.last_move_name = None
        self.last_clear_name = None
        self.last_action = None
        self.agent_mode = agent_mode

        # Pieces
        self.current_piece_type = None
        self.current_piece_rotation = Rotation(0)
        self.current_piece_x = 0
        self.current_piece_y = 0
        self.hold_piece_type = None

        # Connect stuff after everything is initialised
        self.fall_timer.connect(Event("timeout"), self, self.on_natural_drop_piece)
        self.lock_timer.connect(Event("timeout"), self, self.on_lock_delay)
        self.delta_points_render_timer.connect(Event("timeout"), self, self.on_delta_score_render_timeout)
        if environment is not None:
            if hasattr(environment, 'step'):
                self.connect(Event("feature_batch"),
                             environment, environment.step)

        # Connect clear lines event
        # self.connect(Event())

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
    def pop_bag(self, enable_switch=True):
        """Return the next pieces from the bag"""
        if enable_switch:
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

    # Piece and score logic
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
            self.last_delta_score += self.game_over_delta_score
            self.game_over = True
            self.notify(Event("game_over", features=self.fetch_features(0)))
            self.pause()
        else:
            rows = self.clean_rows()

            if rows != 0:
                self.last_delta_score += self.set_score(rows, self.current_piece_type)
            else:
                self.last_delta_score += self.non_line_clear_delta_score
            self.notify(Event("feature_batch", features=self.fetch_features(rows)))
            self.spawn_piece(piece_type=self.pop_bag())

    def on_delta_score_render_timeout(self, event: Event = None):
        self.delta_points_render_timer.pause()
        self.delta_score_panel.invisible = True

    def set_score(self, rows, last_piece_type):
        drop_multiplier = 1
        if self.last_move_name == "hard_drop":
            drop_multiplier = 2
        if self.last_move_name == "rotate" and last_piece_type == ord('T'):
            # TODO: Implement T-spin detection
            pass
        delta_points = 0
        match rows:
            case 1:
                delta_points = 100 * self.level
                self.last_clear_name = "Single"
            case 2:
                delta_points = 300 * self.level
                self.last_clear_name = "Double"
            case 3:
                delta_points = 500 * self.level
                self.last_clear_name = "Triple"
            case 4:
                if self.last_clear_name == "Tetris" or self.last_clear_name == "B2B Tetris":
                    delta_points = 1200 * self.level
                    self.last_clear_name = "B2B Tetris"
                else:
                    delta_points = 800 * self.level
                    self.last_clear_name = "Tetris"
        self.score += delta_points
        self.score_panel.image = pg.font.SysFont('Arial', 20) \
            .render(f'Score: {self.score}', True, self.theme['palette']['text'])
        self.delta_score_panel.image = pg.font.SysFont('Arial', 20) \
            .render(f'+{delta_points}', True, self.theme['palette']['text'])
        self.delta_score_panel.invisible = False
        self.delta_points_render_timer.reset()
        return delta_points

    def move_piece(self):
        """Wrapper for normal & ghost piece placement"""
        # Ghost
        lowest_y = self.current_piece_y
        # Add up and reset when locking
        self.last_delta_score += self.move_delta_score
        while self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                             self.current_piece_x, lowest_y - 1):
            lowest_y -= 1
        self.ghost_field.reset_and_show_piece(self.current_piece_type, self.current_piece_rotation,
                                              self.current_piece_x, lowest_y, color_override=ord('X'))
        # Normal
        self.ghost_field.show_piece(self.current_piece_type, self.current_piece_rotation,
                                    self.current_piece_x, self.current_piece_y)

    def on_natural_drop_piece(self, event: Event = None):
        """Gets called when the piece is supposed to fall. If there is no space left to fall, lock!"""
        if self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                          self.current_piece_x, self.current_piece_y - 1):
            self.current_piece_y -= 1
            self.move_piece()
            self.fall_timer.reset()
            self.request_lock()

    def spawn_piece(self, piece_type):
        """Spawn a piece at default spawn position"""
        self.current_piece_x = self.cols // 2 - 2
        self.current_piece_y = self.rows // 2
        self.current_piece_rotation = Rotation(0)
        self.current_piece_type = piece_type
        self.last_delta_score = 0
        self.move_piece()

    def start_game(self):
        # Init game
        self.score = 0
        self.last_delta_score = 0
        self.game_started = True
        self.game_over = False
        self.level = 1

        # Reset timers
        self.fall_timer.reset()
        self.lock_timer.reset()
        self.rotation_timer.reset()
        self.move_timer.reset()
        self.fast_move_timer.reset()

        # Reset fields
        self.game_field.reset()
        self.ghost_field.reset()
        self.hold_field.reset()
        for field in self.next_fields:
            field.reset()

        # Reset bag
        self.bag = []
        self.pop_bag()

        self.game_paused = False
        self.hold_piece_type = None
        self.last_move_name = None
        self.last_clear_name = None
        self.last_action = None
        # Spawn piece
        self.spawn_piece(self.pop_bag())
        self.notify(Event("feature_batch", features=self.fetch_features(0)))

    def pause(self):
        self.fall_timer.pause()
        self.lock_timer.pause()
        self.rotation_timer.pause()
        self.move_timer.pause()
        self.fast_move_timer.pause()
        self.game_paused = True

    def resume(self):
        self.fall_timer.resume()
        self.lock_timer.resume()
        self.rotation_timer.resume()
        self.move_timer.resume()
        self.fast_move_timer.resume()
        self.game_paused = False

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

    def fetch_features(self, rows_cleared):
        """Features of environment for RL use. Call after every lock"""
        features = {}
        features['current_piece_type'] = self.current_piece_type
        features['current_piece_rotation'] = self.current_piece_rotation
        features['current_piece_x'] = self.current_piece_x
        features['current_piece_y'] = self.current_piece_y
        features['game_field'] = self.game_field
        features['score'] = self.score
        # From game grid, fetch height of each column
        features['column_heights'] = [self.game_field.get_column_height(i) for i in range(self.cols)]
        features['column_holes'] = [self.game_field.get_column_holes(i, features['column_heights'][i])
                                    for i in range(self.cols)]
        features['total_holes'] = sum(features['column_holes'])
        # A measure of bumpiness (the sum of the absolute differences between adjacent columns)
        features['total_bumpiness'] = sum([abs(features['column_heights'][i] - features['column_heights'][i + 1])
                                           for i in range(self.cols - 1)])
        features['max_height'] = max(features['column_heights'])
        features['min_height'] = min(features['column_heights'])
        features['next_piece_type'] = self.bag[0]
        features['hold_piece_type'] = self.hold_piece_type
        features['reward'] = self.last_delta_score
        features['lines_cleared'] = rows_cleared
        return features

    def update(self, dt: float):
        desired_x = self.current_piece_x
        desired_y = self.current_piece_y
        desired_rotation = Rotation(self.current_piece_rotation.get())
        move_command = False
        rotate_command = False
        switch_command = False
        agent_key = None
        if self.agent_mode:
            # Get action from agent queue
            agent_key = gameengine.AGENT_KEY_QUEUE.get_key()
        if self.agent_mode and agent_key == "soft_drop" or self.k_soft_drop.pressed:
            desired_y -= 1
            move_command = True
        if self.agent_mode and agent_key == "left" or self.k_left.pressed:
            desired_x -= 1
            move_command = True
        if self.agent_mode and agent_key == "right" or self.k_right.pressed:
            desired_x += 1
            move_command = True
        if self.agent_mode and agent_key == "clockwise" or self.k_clockwise.just_pressed:
            desired_rotation.set_clockwise()
            rotate_command = True
        if self.agent_mode and agent_key == "counter_clockwise" or self.k_counter_clockwise.just_pressed:
            desired_rotation.set_counter_clockwise()
            rotate_command = True
        if self.agent_mode and agent_key == "180" or self.k_180.just_pressed:
            desired_rotation.set_clockwise()
            desired_rotation.set_clockwise()
            rotate_command = True
        if not self.game_paused and (self.agent_mode and agent_key == "hard_drop" or self.k_hard_drop.just_pressed):
            while self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                 self.current_piece_x, self.current_piece_y - 1):
                self.current_piece_y -= 1
            self.last_move_name = "hard_drop"
            self.lock_piece()

        elif not self.game_paused and (self.agent_mode and agent_key == "switch" or self.k_switch.just_pressed) and self.can_switch:
            self.can_switch = False
            if self.hold_piece_type is None:
                self.hold_piece_type = self.current_piece_type
                self.current_piece_type = self.pop_bag(enable_switch=False)
                self.hold_field.reset_and_show_piece(self.hold_piece_type, Rotation(0), 0, 0)
                self.spawn_piece(self.current_piece_type)
            else:
                self.hold_piece_type, self.current_piece_type = self.current_piece_type, self.hold_piece_type
                self.hold_field.reset_and_show_piece(self.hold_piece_type, Rotation(0), 0, 0)
                self.spawn_piece(self.current_piece_type)
            switch_command = True
        if self.agent_mode and agent_key == "pause" or self.k_pause.just_pressed:
            if self.game_paused:
                self.resume()
            else:
                self.pause()
        if self.agent_mode and agent_key == "restart" or self.k_restart.just_pressed:
            self.start_game()
        if not self.game_paused and move_command and not switch_command:
            if self.move_timer.finished:
                if self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                  desired_x, desired_y):
                    self.current_piece_x = desired_x
                    self.current_piece_y = desired_y
                    self.move_piece()
                    self.move_timer.reset()
                    # Lock requests reset on move
                    if not self.game_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                          self.current_piece_x, self.current_piece_y - 1):
                        self.last_move_name = "move"
                        self.request_lock()
                    else:
                        self.lock_requests = 0
        if not self.game_paused and rotate_command and not switch_command:
            if self.rotation_timer.finished:
                request = False
                if self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                  self.current_piece_x, self.current_piece_y):
                    self.current_piece_rotation = Rotation(desired_rotation.get())
                    self.move_piece()
                    self.rotation_timer.reset()
                    request = True
                # Try wall kick
                else:
                    if self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                      self.current_piece_x - 1, self.current_piece_y):
                        self.current_piece_x -= 1
                        self.current_piece_rotation = Rotation(desired_rotation.get())
                        self.move_piece()
                        self.rotation_timer.reset()
                        request = True
                    elif self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                        self.current_piece_x + 1, self.current_piece_y):
                        self.current_piece_x += 1
                        self.current_piece_rotation = Rotation(desired_rotation.get())
                        self.move_piece()
                        self.rotation_timer.reset()
                        request = True
                    # Experimental floor kick
                    elif self.game_field.can_show_piece(self.current_piece_type, desired_rotation,
                                                        self.current_piece_x, self.current_piece_y + 1):
                        self.current_piece_y += 1
                        self.current_piece_rotation = Rotation(desired_rotation.get())
                        self.move_piece()
                        self.rotation_timer.reset()
                        request = True
                if request:
                    if not self.ghost_field.can_show_piece(self.current_piece_type, self.current_piece_rotation,
                                                           self.current_piece_x, self.current_piece_y - 1):
                        self.last_move_name = "rotate"
                        self.request_lock()
                    else:
                        self.lock_requests = 0

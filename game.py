import os

import pygame as pg
from matplotlib import pyplot as plt

import commons
import gameengine
import grid
from gameengine import CanvasObject

from keras import backend as K
from keras.layers import Dense, Input
from keras.models import Model
from keras.optimizers import Adam
import numpy as np


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
        if obj.invisible:
            continue
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
    gameengine.AGENT_KEY_QUEUE = KeyQueue()
    background = CanvasObject(0, 0, commons.width, commons.height)
    background.image.fill(commons.color_theme_default['palette']['background'])
    background.draw_level = 0
    cell_size = 24
    cell_margin = 1
    env_manager = EnvironmentManager()
    game_grid = grid.PlayField(commons.width // 2, commons.height // 2, cell_size, cell_margin,
                               commons.color_theme_default, commons.key_binds,
                               play_field_offset=(-((cell_size + cell_margin) * 5 + cell_margin // 2),
                                                  -((cell_size + cell_margin) * 30 + cell_margin // 2)),
                               hold_field_offset=(-((cell_size + cell_margin) * 11 + cell_margin // 2),
                                                  -((cell_size + cell_margin) * 10 + cell_margin // 2)),
                               next_field_offset=(((cell_size + cell_margin) * 7 + cell_margin // 2),
                                                  -((cell_size + cell_margin) * 10 + cell_margin // 2)),
                               environment=env_manager, agent_mode=True)
    gameengine.FIELD = game_grid


class KeyQueue(gameengine.LogicObject):
    def __init__(self):
        super().__init__()
        self.queue = []
        self.max_size = 100
        self.current_key = None

    def update(self, dt):
        if len(self.queue) > 0:
            self.current_key = self.queue.pop(0)
        else:
            self.current_key = None

    def add_key(self, key):
        if len(self.queue) < self.max_size:
            self.queue.append(key)

    def get_key(self):
        return self.current_key


class EnvironmentManager(gameengine.Listener):
    def __init__(self):
        gameengine.Listener.__init__(self)
        self.score = 0
        self.num_episodes = 1000
        self.max_actions = 1000
        self.score_history = []
        self.agent = Agent(alpha=0.00001, beta=0.00005)
        self.observation = self.get_default_observation()

    def get_default_observation(self):
        return np.array([0, 0, 0, 0, 0, 0, 0])

    def step(self, event: gameengine.Event):
        print(event.message)
        """Step function. Control flow is managed by the game engine."""
        if event.message == 'game_over':
            done = True
        else:
            done = False
        new_observation, reward = [event.params['features']['lines_cleared'], event.params['features']['total_holes'],
                                   event.params['features']['total_bumpiness'], event.params['features']['max_height'],
                                   event.params['features']['min_height'],
                                   event.params['features']['current_piece_type'],
                                   event.params['features']['next_piece_type']], event.params['features']['reward'],
        # Normalize observation
        new_observation = np.array(new_observation) / 100
        action = self.agent.choose_action(self.observation)
        rotation, x = action % 4, action // 4 - 5
        print(f'Chosen rotation: {rotation}, x: {x}')
        # TODO: Prevent excessive centering

        # Queue action
        for _ in range(rotation):
            gameengine.AGENT_KEY_QUEUE.add_key("clockwise")
        if x >= 0:
            for _ in range(x+1):
                gameengine.AGENT_KEY_QUEUE.add_key("right")
        elif x < 0:
            for _ in range(abs(x)):
                gameengine.AGENT_KEY_QUEUE.add_key("left")
        gameengine.AGENT_KEY_QUEUE.add_key("hard_drop")
        self.observation = new_observation
        self.score += reward
        self.agent.learn(self.observation, action, reward, new_observation, done)
        if done:
            self.score_history.append(self.score)
            self.score = 0
            print(f'Episode {len(self.score_history)} finished with score {self.score_history[-1]}')
            if len(self.score_history) % 100 == 0:
                plt.plot(self.score_history)
                plt.show()
                self.agent.save_models()
            if len(self.score_history) == self.num_episodes:
                print('Finished training')
                self.agent.save_models()
            gameengine.AGENT_KEY_QUEUE.add_key("restart")


class Agent:
    def __init__(self,
                 alpha, beta, gamma=0.99, epsilon=0.1, epsilon_decay=0.99975, epsilon_min=0.01,
                 n_actions=40,
                 layer1_size=16, layer2_size=16,
                 # lines_cleared, holes, bumpiness,
                 # max_height, min_height, current_piece_type, next_piece_type
                 input_dims=7,
                 checkpoint_dir=f'C:{os.sep}Users{os.sep}master{os.sep}PycharmProjects{os.sep}tetrai',
                 env=None):
        gameengine.Listener.__init__(self)
        self.checkpoint_dir = checkpoint_dir
        self.env = env
        self.gamma = gamma
        self.alpha = alpha
        self.beta = beta
        self.epsilon = epsilon
        self.epsilon_decay = epsilon_decay
        self.epsilon_min = epsilon_min
        self.n_actions = n_actions
        self.input_dims = input_dims
        self.fc1_dims = layer1_size
        self.fc2_dims = layer2_size

        self.actor, self.critic, self.policy = self.build_actor_critic_network()
        self.action_space = [i for i in range(self.n_actions)]

    def build_actor_critic_network(self):
        input = Input(shape=(self.input_dims,))
        # Actor specific
        delta = Input(shape=[1])
        dense1 = Dense(self.fc1_dims, activation='relu')(input)
        dense2 = Dense(self.fc2_dims, activation='relu')(dense1)
        # Actor & policy specific
        probs = Dense(self.n_actions, activation='softmax')(dense2)
        # Critic specific
        values = Dense(1, activation='linear')(dense2)

        actor = Model(inputs=[input, delta], outputs=[probs])
        actor.compile(optimizer=Adam(learning_rate=self.alpha), loss='mean_squared_error')
        critic = Model(inputs=[input], outputs=[values])
        critic.compile(optimizer=Adam(learning_rate=self.beta), loss='mean_squared_error')
        policy = Model(inputs=[input], outputs=[probs])

        return actor, critic, policy

    def choose_action(self, observation):
        state = observation[np.newaxis, :]
        probabilities = self.policy.predict(state)[0]
        # TODO: remove epsilon-greedy and use temperature
        if np.random.random() < self.epsilon:
            action = np.random.choice(self.action_space)
        else:
            action = np.random.choice(self.action_space, p=probabilities)
        self.epsilon = max(self.epsilon * self.epsilon_decay, self.epsilon_min)
        return action

    def learn(self, state, action, reward, new_state, done):
        state = state[None, :]
        new_state = new_state[None, :]

        new_critic_value = self.critic.predict(new_state)
        critic_value = self.critic.predict(state)

        # Calculate advantage
        target = reward + self.gamma * new_critic_value * (1 - int(done))
        delta = target - critic_value

        actions = np.zeros([1, self.n_actions])
        actions[np.arange(1), action] = 1.0

        # Train actor
        self.actor.fit([state, delta], actions, verbose=0)
        # Train critic
        self.critic.fit(state, target, verbose=0)

    def save_models(self):
        print('... saving models ...')
        if not os.path.exists(self.checkpoint_dir):
            os.makedirs(self.checkpoint_dir)

        self.actor.save_weights(os.path.join(self.checkpoint_dir, 'actor.h5'))
        self.critic.save_weights(os.path.join(self.checkpoint_dir, 'critic.h5'))

    def load_models(self):
        print('... loading models ...')
        self.actor.load_weights(self.actor.checkpoint_file)
        self.critic.load_weights(self.critic.checkpoint_file)


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

import argparse
import random
import pyglet
import sys
import ctypes
import os

from pyglet import clock
from pyglet.window import key as keycodes
from pyglet.gl import *

import retro

# TODO:
# indicate to user when episode is over (hard to do without save/restore lua state)
# record bk2 directly
# resume from bk2

SAVE_PERIOD = 60  # frames


class buttoncodes:
    A = 15
    B = 16
    X = 17
    Y = 18
    START = 8
    SELECT = 9
    XBOX = 14
    LEFT_BUMPER = 12
    RIGHT_BUMPER = 13
    RIGHT_STICK = 11
    LEFT_STICK = 10
    D_LEFT = 6
    D_RIGHT = 7
    D_UP = 4
    D_DOWN = 5


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--game', help='retro game to use')
    parser.add_argument('--state', help='retro state to start from')
    parser.add_argument('--scenario', help='scenario to use', default='scenario')
    args = parser.parse_args()

    if args.game is None:
        print('Please specify a game with --game <game>')
        print('Available games:')
        for game in sorted(retro.list_games()):
            print(game)
        sys.exit(1)

    if args.state is None:
        print('Please specify a state with --state <state>')
        print('Available states:')
        for state in sorted(retro.list_states(args.game)):
            print(state)
        sys.exit(1)

    env = retro.make(game=args.game, state=args.state, use_restricted_actions=retro.ACTIONS_ALL, scenario=args.scenario)
    obs = env.reset()
    screen_height, screen_width = obs.shape[:2]

    random.seed(0)

    key_handler = pyglet.window.key.KeyStateHandler()
    win_width = 2000
    win_height = win_width * screen_height // screen_width
    win = pyglet.window.Window(width=win_width, height=win_height, vsync=False)

    if hasattr(win.context, '_nscontext'):
        pixel_scale = win.context._nscontext.view().backingScaleFactor()

    win.width = win.width // pixel_scale
    win.height = win.height // pixel_scale

    joysticks = pyglet.input.get_joysticks()
    if len(joysticks) > 0:
        joystick = joysticks[0]
        joystick.open()
    else:
        joystick = None

    win.push_handlers(key_handler)

    key_previous_states = {}
    button_previous_states = {}

    steps = 0
    recorded_actions = []
    recorded_states = []

    pyglet.app.platform_event_loop.start()

    fps_display = pyglet.clock.ClockDisplay()
    clock.set_fps_limit(60)

    glEnable(GL_TEXTURE_2D)
    texture_id = GLuint(0)
    glGenTextures(1, ctypes.byref(texture_id))
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA8, screen_width, screen_height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

    while not win.has_exit:
        win.dispatch_events()

        win.clear()

        keys_clicked = set()
        keys_pressed = set()
        for key_code, pressed in key_handler.items():
            if pressed:
                keys_pressed.add(key_code)

            if not key_previous_states.get(key_code, False) and pressed:
                keys_clicked.add(key_code)
            key_previous_states[key_code] = pressed

        buttons_clicked = set()
        buttons_pressed = set()
        if joystick is not None:
            for button_code, pressed in enumerate(joystick.buttons):
                if pressed:
                    buttons_pressed.add(button_code)

                if not button_previous_states.get(button_code, False) and pressed:
                    buttons_clicked.add(button_code)
                button_previous_states[button_code] = pressed

        if keycodes.R in keys_clicked or buttoncodes.LEFT_BUMPER in buttons_clicked:
            if len(recorded_states) > 1:
                recorded_states.pop()
                steps, save_state = recorded_states.pop()
                recorded_states = recorded_states[:steps]
                recorded_actions = recorded_actions[:steps]
                env.em.set_state(save_state)

        if keycodes.ESCAPE in keys_pressed or buttoncodes.XBOX in buttons_clicked:
            # record all the actions so far to a bk2 and exit
            i = 0
            while True:
                movie_filename = 'human/%s/%s/%s-%s-%04d.bk2' % (args.game, args.scenario, args.game, args.state, i)
                if not os.path.exists(movie_filename):
                    break
                i += 1
            os.makedirs(os.path.dirname(movie_filename), exist_ok=True)
            env.record_movie(movie_filename)
            env.reset()
            for step, act in enumerate(recorded_actions):
                if step % 1000 == 0:
                    print('saving %d/%d' % (step, len(recorded_actions)))
                env.step(act)
            env.stop_record()
            print('complete')
            sys.exit(1)

        inputs = {
            'A': keycodes.Z in keys_pressed or buttoncodes.A in buttons_pressed,
            'B': keycodes.X in keys_pressed or buttoncodes.B in buttons_pressed,
            'C': keycodes.C in keys_pressed,
            'X': keycodes.A in keys_pressed or buttoncodes.X in buttons_pressed,
            'Y': keycodes.S in keys_pressed or buttoncodes.Y in buttons_pressed,
            'Z': keycodes.D in keys_pressed,

            'UP': keycodes.UP in keys_pressed or buttoncodes.D_UP in buttons_pressed,
            'DOWN': keycodes.DOWN in keys_pressed or buttoncodes.D_DOWN in buttons_pressed,
            'LEFT': keycodes.LEFT in keys_pressed or buttoncodes.D_LEFT in buttons_pressed,
            'RIGHT': keycodes.RIGHT in keys_pressed or buttoncodes.D_RIGHT in buttons_pressed,

            'MODE': keycodes.TAB in keys_pressed or buttoncodes.SELECT in buttons_pressed,
            'START': keycodes.ENTER in keys_pressed or buttoncodes.START in buttons_pressed,
        }
        action = [inputs[b] for b in env.BUTTONS]

        if steps % SAVE_PERIOD == 0:
            recorded_states.append((steps, env.em.get_state()))
        obs, rew, done, info = env.step(action)
        recorded_actions.append(action)
        steps += 1

        glBindTexture(GL_TEXTURE_2D, texture_id)
        video_buffer = ctypes.cast(obs.tobytes(), ctypes.POINTER(ctypes.c_short))
        glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, obs.shape[1], obs.shape[0], GL_RGB, GL_UNSIGNED_BYTE, video_buffer)

        x = 0
        y = 0
        h = win.height
        w = win.width

        pyglet.graphics.draw(
            4,
            pyglet.gl.GL_QUADS,
            ('v2f', [x, y, x + w, y, x + w, y + h, x, y + h]),
            ('t2f', [0, 1, 1, 1, 1, 0, 0, 0]),
        )

        fps_display.draw()

        win.flip()

        # process joystick events
        timeout = clock.get_sleep_time(False)
        pyglet.app.platform_event_loop.step(timeout)

        clock.tick()

    pyglet.app.platform_event_loop.stop()


main()

# retro-movies

This is a collection of human demonstrations of [gym-retro](https://github.com/openai/retro) games in BK2 format.  Right now it consists only of a single demonstration for each level of the [Sonic Benchmark](https://arxiv.org/abs/1804.03720) used by the [Retro Contest](https://contest.openai.com/). These recordings can be used to have the agent start playing from random points sampled from the course of each level, exposing the agent to a lot of areas it may not have seen if it only started from the beginning of the level.

To convert a movie to a video:
```sh
python -m retro.scripts.playback_movie human/SonicAndKnuckles3-Genesis/contest/SonicAndKnuckles3-Genesis-AngelIslandZone.Act1-0000.bk2
open human/SonicAndKnuckles3-Genesis/contest/SonicAndKnuckles3-Genesis-AngelIslandZone.Act1-0000.mp4
```

To get states from a movie:
```python
import retro

movie_path = 'human/SonicAndKnuckles3-Genesis/contest/SonicAndKnuckles3-Genesis-AngelIslandZone.Act1-0000.bk2'
movie = retro.Movie(movie_path)
movie.step()

env = retro.make(game=movie.get_game(), state=retro.STATE_NONE, use_restricted_actions=retro.ACTIONS_ALL)
env.initial_state = movie.get_state()
env.reset()

print('stepping movie')
while movie.step():
    keys = []
    for i in range(env.NUM_BUTTONS):
        keys.append(movie.get_key(i))
    _obs, _rew, _done, _info = env.step(keys)
    saved_state = env.em.get_state()

print('stepping environment started at final state of movie')
env.initial_state = saved_state
env.reset()
while True:
    env.render()
    env.step(env.action_space.sample())
```

To record your own movie (assuming you have gym-retro installed):
```sh
pip install pyglet
python human-recorder.py --game SonicAndKnuckles3CustomKevin-Genesis --scenario contest --state MushroomHillZone.Custom
```

Hit R or Left Bumper if you're using an Xbox controller to rewind time by a short amount.

When you hit ESC or the center Xbox button on the controller, the episode will be recorded to a file (it is not recorded until this point).

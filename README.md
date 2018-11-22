**Status:** Archive (code is provided as-is, no updates expected)

# retro-movies

This is a collection of human demonstrations of [gym-retro](https://github.com/openai/retro) games in BK2 format.  Right now it consists only of a single demonstration for each level of the [Sonic Benchmark](https://arxiv.org/abs/1804.03720) used by the [Retro Contest](https://contest.openai.com/). These recordings can be used to have the agent start playing from random points sampled from the course of each level, exposing the agent to a lot of areas it may not have seen if it only started from the beginning of the level.

To convert a movie to a video:
```sh
python -m retro.scripts.playback_movie human/SonicAndKnuckles3-Genesis/contest/SonicAndKnuckles3-Genesis-AngelIslandZone.Act1-0000.bk2
open human/SonicAndKnuckles3-Genesis/contest/SonicAndKnuckles3-Genesis-AngelIslandZone.Act1-0000.mp4
```

To get states from a movie, run [get_states.py](get_states.py)
```sh
python -m get_states.py
```

For convenience, we have [included statistics on the movies](get_states.results) already included in this repo.

To record your own movie (assuming you have gym-retro installed):
```sh
pip install pyglet
python human-recorder.py --game SonicAndKnuckles3CustomKevin-Genesis --scenario contest --state MushroomHillZone.Custom
```

Hit R or Left Bumper if you're using an Xbox controller to rewind time by a short amount.

When you hit ESC or the center Xbox button on the controller, the episode will be recorded to a file (it is not recorded until this point).

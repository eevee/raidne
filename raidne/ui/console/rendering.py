# encoding: utf8
"""Console rendering for every Thing in the game.

Contains a single function, `rendering_for`, which takes a single Thing
argument.
"""
from multimethod import strict_multimethod

from raidne.game import things

@strict_multimethod(things.Thing)
def rendering_for(obj):
    return u'‽'


### Architecture

@strict_multimethod(things.Floor)
def rendering_for(obj):
    return u'·'

@strict_multimethod(things.Wall)
def rendering_for(obj):
    return u'▓'


### Creatures

@strict_multimethod(things.Player)
def rendering_for(obj):
    return u'☻'

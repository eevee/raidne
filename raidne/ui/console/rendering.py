# encoding: utf8
"""Console rendering for every Thing in the game.

Contains a single function, `rendering_for`, which accepts a Thing argument and
returns (character, palette_entry).

Also contains a list `PALETTE_ENTRIES`, containing the palette used by
everything in the game.
"""
from multimethod import strict_multimethod

from raidne.game import things

PALETTE_ENTRIES = [
    # (name, other)
    # (name, fg, bg, mono, fg_high, bg_high)
    ('floor', 'black', 'default', None, '#666', 'default'),
]


### Fallback

@strict_multimethod(things.Thing)
def rendering_for(obj):
    return u'‽', 'default'


### Architecture

@strict_multimethod(things.Floor)
def rendering_for(obj):
    return u'·', 'floor'

@strict_multimethod(things.Wall)
def rendering_for(obj):
    return u'▒', 'default'


### Creatures

@strict_multimethod(things.Player)
def rendering_for(obj):
    return u'☻', 'default'

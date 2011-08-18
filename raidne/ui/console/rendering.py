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

    # UI
    ('message-old', 'dark gray', 'default', None, '#666', 'default'),
    ('message-fresh', 'white', 'default', None, '#fff', 'default'),
    ('inventory-default', 'default', 'default', None, 'default', 'default'),
    ('inventory-selected', 'default', 'dark blue', None, 'default', '#068'),

    # Architecture
    ('floor', 'black', 'default', None, '#666', 'default'),

    # Creatures
    ('player', 'yellow', 'default', None, '#ff6', 'default'),
    ('newt', 'yellow', 'default', None, '#ff6', 'default'),

    # Items
    ('potion', 'light magenta', 'default', None, '#f6f', 'default'),
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

@strict_multimethod(things.StaircaseDown)
def rendering_for(obj):
    return u'▙', 'default'


### Creatures

@strict_multimethod(things.Player)
def rendering_for(obj):
    return u'☻', 'player'

@strict_multimethod(things.Newt)
def rendering_for(obj):
    return u':', 'newt'


### Items

@strict_multimethod(things.Potion)
def rendering_for(obj):
    return u'ᵭ', 'potion'

# encoding: utf8
"""Console rendering for every Thing in the game.

Contains a single function, `rendering_for`, which accepts a Thing argument and
returns (character, palette_entry).

Also contains a list `PALETTE_ENTRIES`, containing the palette used by
everything in the game.
"""
from functools import partial

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


# TODO most likely things should express what they look "like" and then this
# should key off of that
def rendering_for(thing):
    if thing.isa(things.Architecture):
        if thing.isa(things.floor):
            return u'·', 'floor'
        if thing.isa(things.wall):
            return u'▒', 'default'
        if thing.isa(things.staircase_down):
            return u'▙', 'default'
        if thing.isa(things.trap):
            return u'X', 'default'

    elif thing.isa(things.Creature):
        if thing.isa(things.player):
            return u'☻', 'player'
        if thing.isa(things.newt):
            return u':', 'newt'

    elif thing.isa(things.Item):
        if thing.isa(things.potion):
            return u'ᵭ', 'potion'

    return u'‽', 'default'

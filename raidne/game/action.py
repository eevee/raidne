# XXX write docstring.  these should all be SIMPLE; actual logic and whatever
# should be in effects

from raidne import exceptions
from raidne.game import effect
from raidne.util import Position

class Action(object):
    pass

class MeleeAttack(Action):
    cost = 24  # TODO

    def __init__(self, actor, target):
        self.actor = actor
        self.target = target
        # XXX this should probably take a direction/aim/range/whatever, not a particular thing

    def __call__(self, ui_proxy, dungeon):
        # XXX assert they are both on the floor and within melee distance of each other

        # Calculate attacker's damage
        # XXX this isn't a calculation  :)
        damage = effect.MeleeDamage(self.actor.attack_power)
        yield damage, self.target


class Walk(object):
    cost = 24  # TODO

    def __init__(self, actor, direction):
        self.actor = actor
        self.direction = direction

    # XXX: is passing the entire toplevel interface down here such a good idea?
    def __call__(self, ui_proxy, dungeon):
        # Check that the target tile accepts our movement
        # TODO this needs to go somewhere else, eventually, to check teleports etc
        old_position = dungeon.current_floor.find(self.actor).position
        new_position = self.direction.relative_to(old_position)
        for thing in dungeon.current_floor.tile(new_position):
            if thing.solid:
                # XXX "cancel" the action, or just return?
                # XXX need to do something to avoid the action cost at least
                return
                raise exceptions.CollisionError


        dungeon.current_floor.move(self.actor, self.direction)
        new_time = dungeon.current_floor.tile(new_position)

        # this message needs to fire when the player moves at *all*; how to do
        # this.  hook methods?
        if self.actor.is_player:
            items = new_tile.items
            if items:
                ui_proxy.message(u"You see here: {0}.".format(
                    u','.join(item.name for item in items)))


class Descend(object):
    # target is a staircase.
    # TODO do more standardized initialization and specifying of targets;
    # eventually these should all inherit from some Event base class
    cost = None  # TODO

    def __init__(self, actor, target):
        # XXX should there even be a target, or should this just use the
        # actor's current position
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        map = dungeon.current_floor
        # XXX this is just all kinds of wrong.
        if self.actor == dungeon.player and not map.find(self.actor).architecture.__class__.__name__ == 'StaircaseDown':
            ui_proxy.message("You can't go down here.")
            return

        map.remove(self.actor)

        # XXX THIS IS DEFINITELY ALL KINDS OF WRONG.  WHERE SHOULD THIS LOGIC GO OMG
        assert self.actor == dungeon.player
        map = dungeon.current_floor = dungeon.floors[1]  # XXX uhhhhhh.
        # XXX need to put the player on the corresponding up staircase, or
        # somewhere else if it's blocked or doesn't exist...
        map.put(self.actor, Position(1, 1))


class PickUp(object):
    """Actor is picking up an item."""

    def __init__(self, actor, target):
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        actor_tile = dungeon.current_floor.find(self.actor)
        target_tile = dungeon.current_floor.find(self.target)

        assert actor_tile == target_tile
        # XXX assert is item, or actually check that the thing responds to being taken
        # XXX assert actor has an inventory

        self.actor.inventory.append(self.target)
        dungeon.current_floor.remove(self.target)
        ui_proxy.message("{0} picked up {1}".format(self.actor.name, self.target.name))

        #items = tile.items
        #self.player.inventory.extend(items)
        #for item in items:
        #    self.current_floor.remove(item)
        #    ui.message("Got {0}.".format(item.name))


class UseItem(Action):
    def __init__(self, actor, target):
        self.actor = actor
        self.target = target

    def __call__(self, ui_proxy, dungeon):
        yield self.target._type.action_effects[UseItem], self.actor

class Throw(Action):
    def __init__(self, actor, obj, target):
        # TODO
        pass

    def __call__(self, proxy):
        try:
            # XXX i guess this bit should actually be in the caller
            target.handle_action(self)

            throw_effect = obj.throw_effect()
            # this runs all the effect hooks that apply to the throw_effect
            target.handle_effect(throw_effect)
            # this actually invokes throw_effect
            throw_effect(target)

        except CancelEvent:
            pass



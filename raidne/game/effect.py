class Effect(object):
    """Some kind of effect that happens to an object.  Usually the end result
    of an `Action`.
    """

    def __init__(self):
        pass


class MeleeDamage(Effect):

    def __init__(self, damage):
        self.damage = damage
        #super(MeleeDamage, self).__init__(*args, **kwargs)

    def __call__(self, ui_proxy, dungeon, actor, agent, target):
        # TODO does this need actor?  source?  is agent even important, if the
        # dungeon handles hooks?
        # TODO should this all just be 'event' stuff at this point sigh

        # Inform the player that this happened
        # TODO CONTD ok i guess this is a good reason but that's lame
        ui_proxy.message("{0} attacks {1}!!".format(actor.name, target.name))

        # And inflict!
        target.health.modify(- self.damage)

        # Handle death.
        # XXX this should probably go in the creature's damage handler.
        # XXX we need a real event queue to put this on
        # XXX looks like thing types can't use the python class system.  type needs to be an attr
        if target.health.current == 0:
            # XXX meters should probably support bool or something
            ui_proxy.message("{0} dies".format(target.name))
            dungeon.current_floor.remove(target)


class Heal(Effect):
    amount = 10

    def __call__(self, ui_proxy, dungeon, actor, agent, target):
        target.health.modify(self.amount)
        ui_proxy.message("{0} feels better".format(actor.name))

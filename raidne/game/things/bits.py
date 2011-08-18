"""Not actually things in here -- just little classes that help represent bits
of things."""

class Meter(object):
    """HP or magic; some integral thing that has a maximum and can be lowered
    and filled.
    """
    __slots__ = ('current', 'maximum')

    def __init__(self, maximum):
        if maximum < 1:
            raise ValueError("Maximum must be positive")

        self.maximum = maximum
        self.current = maximum

    def modify(self, delta):
        """Modify the current value, capping between the maximum and zero."""
        self.current += delta
        if self.current < 0:
            self.current = 0
        elif self.current > self.maximum:
            self.current = self.maximum

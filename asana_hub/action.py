"""
Defines an Action.
"""

def get_subclasses(c):
    """Gets the subclasses of a class."""
    subclasses = c.__subclasses__()
    for d in list(subclasses):
        subclasses.extend(get_subclasses(d))
    return subclasses

class Action(object):
    """A ToolApp Action."""

    # name of action
    name = "unnamed"

    def __init__(self, args, app):
        self.args = args
        self.app = app

    def run(self):
        raise NotImplementedError(
            "run() is not implemented in %s" % self.__class__.__name__)

    @classmethod
    def iter_actions(cls):
        """Iterates over new instances of Actions."""

        for sub_class in get_subclasses(cls):
            yield sub_class

# Import all actions!
from .actions import *

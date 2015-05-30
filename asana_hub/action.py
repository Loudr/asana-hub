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
    def add_arguments(cls, parser):
        """Add arguments to the parser for collection in app.args.

        Args:
            parser:
                `argparse.ArgumentParser`. Parser.
                Arguments added here are server on
                self.args.
        """
        pass

    def get_repo_and_project(self):
        """Returns repository and project."""
        app = self.app

        # Get repo
        repo = app.data.apply('github-repo', app.args.github_repo,
            app.prompt_repo,
            on_load=app.github.get_repo,
            on_save=lambda r: r.id
            )

        assert repo, "repository not found."

        # Get project
        project = app.data.apply('asana-project', app.args.asana_project,
            app.prompt_project,
            on_load=app.asana.projects.find_by_id,
            on_save=lambda p: p['id']
            )

        assert project, "project not found."

        return repo, project

    @classmethod
    def iter_actions(cls):
        """Iterates over new instances of Actions."""

        for sub_class in get_subclasses(cls):
            yield sub_class

# Import all actions!
from .actions import *

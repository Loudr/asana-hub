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

        parser.add_argument(
            '-as-api', '--asana-api',
            action='store',
            nargs='?',
            const='',
            dest='asana_api',
            help="[setting] asana api key.",
            )

        parser.add_argument(
            '-gh-api', '--github-api',
            action='store',
            nargs='?',
            const='',
            dest='github_api',
            help="[setting] github api token.",
            )

        parser.add_argument(
            '--first-issue',
            type=int,
            action='store',
            nargs='?',
            const='',
            help="[setting] only sync issues [FIRST_ISSUE] and above"
            )

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

        # Set first issue
        first_issue = app.data.apply('first-issue', app.args.first_issue,
            "set the first issue to sync with [1 for new repos]",
            on_save=int)

        assert first_issue
        assert first_issue >= 0, "issue must be positive"

        return repo, project

    @classmethod
    def iter_actions(cls):
        """Iterates over new instances of Actions."""

        for sub_class in get_subclasses(cls):
            yield sub_class

# Import all actions!
from .actions import *

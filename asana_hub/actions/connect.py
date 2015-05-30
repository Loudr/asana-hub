"""
connect action

Connects and authenticates OAuth2.

"""

import logging

from ..action import Action

class Connect(Action):
    """Connects and authenticates OAuth accounts."""

    # name of action
    name = "connect"

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
            '--project',
            action='store',
            nargs='?',
            const='',
            dest='asana_project',
            help="asana project id.",
            )

        parser.add_argument(
            '--repo',
            action='store',
            nargs='?',
            const='',
            dest='github_repo',
            help="github repository id.",
            )
        pass

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        logging.info("connected ok.")
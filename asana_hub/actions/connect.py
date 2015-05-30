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

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        logging.info("connected ok.")
"""
issue action

Creates a new github issue and asana task.

"""

import logging

from ..action import Action

class Issue(Action):
    """Creates a new github issue and asana task."""

    # name of action
    name = "issue"

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
            '-t', '--title',
            action='store',
            nargs='?',
            const='',
            dest='title',
            help="[issue] task/issue title.",
            )

        parser.add_argument(
            '-b', '--body',
            action='store',
            nargs='?',
            const='',
            dest='body',
            help="[issue] task/issue body.",
            )

        pass

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        repo, project = self.get_repo_and_project()

        # Collect title and body
        title = app.settings.apply(None, app.args.title,
            "task/issue title",
            )

        assert title, "title required"

        body = app.settings.apply(None, app.args.body,
            "body/message",
            ) or ''

        # Post asana task.
        asana_workspace_id = project['workspace']['id']
        task = app.asana.tasks.create_in_workspace(
            asana_workspace_id,
            {
            'name': title,
            'notes': body,
            # TODO: Correct assignee.
            'assignee': 'me',
            'projects': [project['id']]
            })

        asana_task_id = task['id']
        asana_task_url = app.make_asana_url(project['id'], asana_task_id)

        body = body + ("\n\n"
            "**Asana: #%d**\n"
            "%s" % (
                asana_task_id,
                asana_task_url,
            ))

        # Create github issue
        issue = repo.create_issue(
            title=title,
            body=body.strip(),
            )

        # Create asana comment (story)
        app.announce_issue_to_task(asana_task_id, issue)

        logging.info("github issue #%d created:\n%s\n",
            issue.number, issue.html_url)

        logging.info("asana task #%d created:\n%s\n",
            asana_task_id, asana_task_url)

        # Save issue and task to db.
        app.save_issue_data_task(issue.number, asana_task_id)

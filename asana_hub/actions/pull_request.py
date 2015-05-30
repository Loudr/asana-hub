"""
issue action

Creates a new github issue and asana task.

"""

import logging

from ..action import Action

class PullRequest(Action):
    """Creates a new github pull-request for an exist issue and a branch."""

    # name of action
    name = "pr"

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
            '-i', '--issue',
            action='store',
            nargs='?',
            const='',
            dest='issue',
            help="[pr] issue #",
            )

        parser.add_argument(
            '-br', '--branch',
            action='store',
            nargs='?',
            const='',
            dest='branch',
            help="[pr] branch",
            )

        parser.add_argument(
            '-tbr', '--target-branch',
            action='store',
            nargs='?',
            const='',
            default='master',
            dest='target_branch',
            help="[pr] name of branch to pull changes into\n(defaults to: master)",
            )

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        repo, project = self.get_repo_and_project()
        project_id = project['id']

        # Collect title and body
        issue = app.settings.apply(None, app.args.issue,
            "issue # to create PR for",
            )

        assert issue, "issue required"
        issue = repo.get_issue(int(issue))
        assert issue, "issue could not be found"

        branch = app.settings.apply(None, app.args.branch,
            "branch to create pull-request from [via api]",
            ) or ''

        # Get issue data to create pull request tasks list.
        issue_data = app.get_saved_issue_data(issue)

        issue_tasks = issue_data.get('tasks', [])
        issue_data['tasks'] = issue_tasks

        # pull_requests is a list of pull request numbers
        issue_prs = issue_data.get('pull_requests', [])
        issue_data['pull_requests'] = issue_prs

        asana_msgs = ''
        for task in issue_tasks:
            asana_msgs += '\n * [#%d](%s)' % (
                task,
                app.make_asana_url(project_id, task)
                )

        if asana_msgs:
            asana_msgs = '## Asana Tasks\n' + asana_msgs

        # Create pull request.
        pull_request = repo.create_pull(
            title=issue.title,
            head=branch,
            base="master",
            body="Fixes #%d - %s\n"
                "\n## Testing:\n\n"
                "%s"
                "" % (
                    issue.number,
                    issue.title,
                    asana_msgs,
                    )
            )

        # Post asana task.
        title = "PR #%d" % pull_request.number
        body = "%s" % (
            pull_request.html_url
            )

        task_ids = []
        for task_id in issue_tasks:
            task = app.asana.tasks.add_subtask(
                task_id,
                {
                'name': title,
                'notes': body,
                # TODO: Correct assignee.
                'assignee': 'me',
                })
            task_ids.append(task['id'])

            app.save_issue_data_task(issue.number, task['id'])

        # Add pull request to local data
        if pull_request.number not in issue_prs:
            issue_prs.append(pull_request.number)

        logging.info("github pull_request #%d created:\n%s\n",
            pull_request.number, pull_request.html_url)


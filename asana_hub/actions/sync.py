"""
sync action

Syncs completion status of issues and their matched tasks.

"""

import logging
import re

from ..action import Action

ASANA_ID_RE = re.compile(r'#(\d{12,16})', re.M)
"""Regular expression for capturing asana IDs."""

ASANA_MULTI_RE = re.compile(r'## Asana Tasks:\n(#(\d{12,})\s*)+', re.M)
"""Regular exprsssion to catch malformed data due to too many tasks."""

class Sync(Action):
    """Syncs completion status of issues and their matched tasks."""

    # name of action
    name = "sync"

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
            '--create-missing-tasks',
            action='store_true',
            dest='create_missing_tasks',
            help="[sync] create asana tasks for issues without tasks"
            )

    def apply_tasks_to_issue(self, issue, tasks):
        """Applies task numbers to an issue."""
        task_numbers = "\n".join('#'+str(tid) for tid in tasks)
        if task_numbers:
            new_body = ASANA_MULTI_RE.sub('', issue.body)
            new_body = new_body + "\n## Asana Tasks:\n\n%s" % task_numbers
            issue.edit(body=new_body)

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        repo, project = self.get_repo_and_project()
        asana_workspace_id = project['workspace']['id']
        project_id = project['id']

        # Iterate over the issues in the opposite state as the namespace
        # we are in. We simply want to toggle these guys.
        logging.info("collecting github.com issues")
        issues_map = {}
        for issue in repo.get_issues(state="all"):
            issue_number = str(issue.number)
            issue_body = issue.body
            asana_match = ASANA_ID_RE.search(issue_body)
            multi_match = ASANA_MULTI_RE.search(issue_body)

            if multi_match:
                issue_body = ASANA_MULTI_RE.sub('', issue_body)
                asana_match = None

            if (app.has_saved_issue_data(issue_number, "closed") or
                app.has_saved_issue_data(issue_number, "open")):
                issues_map[issue_number] = issue
                status = "cached"

                if not asana_match:
                    # Update body with asana task #
                    closed_tasks = \
                        app.get_saved_issue_data(issue, 'closed').get('tasks', [])
                    open_tasks = \
                        app.get_saved_issue_data(issue, 'open').get('tasks', [])

                    # Add tasks if we have any.
                    if open_tasks or closed_tasks:
                        self.apply_tasks_to_issue(issue,
                            open_tasks + closed_tasks)
                        status = "updated with asana #s"

            # else, missing tasks
            elif asana_match:
                print issue_body
                assert False, "OK"

            elif self.args.create_missing_tasks and not issue.pull_request:
                # missing task
                # Create tasks for non-prs
                task = app.asana.tasks.create_in_workspace(
                    asana_workspace_id,
                    {
                        'name': issue.title,
                        'notes': issue_body,
                        # TODO: Correct assignee.
                        'assignee': 'me',
                        'projects': [project_id],
                        'completed': bool(issue.closed_at)
                    })

                # Announce task git issue
                task_id = task['id']
                app.announce_issue_to_task(task_id, issue)

                # Save task to drive
                app.save_issue_data_task(issue_number, task_id,
                    issue.state)
                status = "new task #%d" % task_id

            else:
                status = "no task"

            logging.info("\t%d) %s - %s",
                issue.number, issue.title, status)

        # Refresh status of issue/tasks
        for issue_number, issue in issues_map.iteritems():

            state = issue.state
            other_state = 'open' if state == 'closed' else 'closed'

            # Get tasks in the issue that are outdated.
            issue_data = app.get_saved_issue_data(issue_number, other_state)
            issue_tasks = issue_data.get('tasks', [])

            for task_id in issue_tasks:
                logging.info("\tupdating #%d (%s->%s) - %d",
                    issue.number,
                    other_state, state,
                    task_id)
                task = app.get_asana_task(task_id)
                if not task:
                    issue_tasks.remove(task_id)
                    logging.debug("task #%d was deleted.", task_id)
                    continue

                if issue.closed_at:
                    # close task
                    app.asana.tasks.update(
                        task['id'],
                        {
                        'completed': True
                        })
                else:
                    # open task
                    app.asana.tasks.update(
                        task['id'],
                        {
                        'completed': False
                        })

                app.move_saved_issue_data(issue_number, other_state, state)





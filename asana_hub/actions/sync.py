# -*- coding: utf-8 -*-
"""
sync action

Syncs completion status of issues and their matched tasks.

"""

import logging
import re

from ..action import Action

ASANA_ID_RE = re.compile(r'#(\d{12,16})', re.M)
"""Regular expression for capturing asana IDs."""

ASANA_SECTION_RE = re.compile(r'## Asana Tasks:\s+(#(\d{12,})\s*)+', re.M)
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

    def apply_tasks_to_issue(self, issue, tasks, issue_body=None):
        """Applies task numbers to an issue."""
        issue_body = issue_body or issue.body
        task_numbers = "\n".join('#'+str(tid) for tid in tasks)
        if task_numbers:
            new_body = ASANA_SECTION_RE.sub('', issue_body)
            new_body = new_body + "\n## Asana Tasks:\n\n%s" % task_numbers
            issue.edit(body=new_body)
            return new_body

        return issue_body

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
            multi_match_sections = len(ASANA_SECTION_RE.findall(issue_body)) > 1

            state = issue.state
            other_state = 'open' if state == 'closed' else 'closed'
            status = "cached"

            # Collect closed and opened tasks known for this issue.
            closed_tasks = \
                app.get_saved_issue_data(issue, 'closed').get('tasks', [])
            open_tasks = \
                app.get_saved_issue_data(issue, 'open').get('tasks', [])
            recorded_tasks = set(open_tasks + closed_tasks)

            # Collect tasks named on github issue
            issue_named_tasks = set()
            for m_grp in ASANA_ID_RE.finditer(issue_body):
                issue_named_tasks.add(int(m_grp.group(1)))

            # Get tasks that are named but missing from cache.
            tasks_to_save_to_this_issue = issue_named_tasks - recorded_tasks
            for task_id in tasks_to_save_to_this_issue:
                status = "collected tasks"
                app.save_issue_data_task(issue_number, task_id, issue.state)

            my_tasks = recorded_tasks.union(tasks_to_save_to_this_issue)

            # Determine if there are multiple groups of ASANA TASKS
            # named.
            if multi_match_sections:
                issue_body = ASANA_SECTION_RE.sub('', issue_body)
                asana_match = None

                issue_body = self.apply_tasks_to_issue(issue, my_tasks,
                    issue_body=issue_body)
                status = "minified issue body"

            # If we have tasks already, this issue is cached.
            if recorded_tasks:
                issue_data = app.get_saved_issue_data(issue_number, other_state)
                issue_cached_tasks = issue_data.get('tasks', [])

                issues_map[issue_number] = (issue, issue_cached_tasks)

                # If the body is missing asana tasks, add all those we know
                # about.
                if not asana_match:
                    # Add tasks if we have any.
                    if recorded_tasks:
                        issue_body = self.apply_tasks_to_issue(issue, my_tasks,
                            issue_body=issue_body)
                        status = "updated with asana #s"

                # If the section isn't formatted... let's reformat it.
                elif not ASANA_SECTION_RE.search(issue_body):
                    issue_body = self.apply_tasks_to_issue(issue, my_tasks,
                        issue_body=issue_body)
                    status = "reformatted asana tasks"

            # tasks named on issue need to be synced
            elif asana_match and issue_named_tasks:
                status = "connecting tasks"
                self.apply_tasks_to_issue(issue, my_tasks,
                    issue_body=issue_body)

                issues_map[issue_number] = (issue, my_tasks)

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

            if status != "cached":
                logging.info("\t%d) %s - %s",
                    issue.number, issue.title, status)

        # Refresh status of issue/tasks
        logging.info("refreshing task statuses...")
        for issue_number, (issue, issue_tasks) in issues_map.iteritems():

            state = issue.state
            other_state = 'open' if state == 'closed' else 'closed'

            # Get tasks in the issue that are outdated.
            for task_id in issue_tasks:
                logging.info("\t#%d - updating (%s->%s) - %d",
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





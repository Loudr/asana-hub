# -*- coding: utf-8 -*-
"""
sync action

Syncs completion status of issues and their matched tasks.

"""

import logging
import re
import collections

from ..action import Action

ASANA_ID_RE = re.compile(r'#(\d{12,16})', re.M)
"""Regular expression for capturing asana IDs."""

ASANA_SECTION_RE = re.compile(r'## Asana Tasks:\s+(#(\d{12,})\s*)+', re.M)
"""Regular exprsssion to catch malformed data due to too many tasks."""

_ms_label = lambda x: "_ms:%d"%x
"""Converts a milestone id into an _ms prefixed string"""

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
            '-c', '--create-missing-tasks',
            action='store_true',
            dest='create_missing_tasks',
            help="[sync] create asana tasks for issues without tasks"
            )

        parser.add_argument(
            '-l', '--sync-labels',
            action='store_true',
            dest='sync_labels',
            help="[sync] sync labels and milestones for each issue"
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

    def sync_labels(self, repo):
        """Creates a local map of github labels/milestones to asana tags."""

        logging.info("syncing new github.com labels to tags")

        # create label tag map
        ltm = self.app.data.get("label-tag-map", {})

        # loop over labels, if they don't have tags, make them
        for label in repo.get_labels():
            tag_id = ltm.get(label.name, None)
            if tag_id is None:

                tag = self.app.asana.tags.create(name=label.name,
                                      workspace=self.asana_ws_id,
                                      notes="gh: %s" % label.url
                                      )

                logging.info("\t%s => tag %d", label.name, tag['id'])
                ltm[label.name] = tag['id']

        # loop over milestones, if they don't have tags, make them
        for ms in repo.get_milestones(state="all"):
            tag_id = ltm.get(_ms_label(ms.id), None)
            if tag_id is None:

                tag = self.app.asana.tags.create(name=ms.title,
                                      workspace=self.asana_ws_id,
                                      notes="gh: %s" % ms.url
                                      )

                logging.info("\t%s => tag %d", ms.title, tag['id'])
                ltm[_ms_label(ms.id)] = tag['id']

        self.app.data['label-tag-map'] = ltm
        return ltm

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        repo, project = self.get_repo_and_project()
        self.asana_ws_id = asana_workspace_id = project['workspace']['id']
        project_id = project['id']

        # Sync project labels <-> asana tags
        if app.args.sync_labels:
            label_tag_map = self.sync_labels(repo)
        else:
            label_tag_map = {}

        # Iterate over the issues in the opposite state as the namespace
        # we are in. We simply want to toggle these guys.
        logging.info("collecting github.com issues")
        issues_map = {}

        # Get the first issue, to limit syncing.
        first_issue = app.data.get('first-issue')

        for issue in repo.get_issues(state="all"):

            # bypass issues < `first-issue` setting.
            if (first_issue is not None and
                issue.number < first_issue):
                logging.debug("stopping at first-issue: %d", first_issue)
                break

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

            # Sync tags and labels
            labels = set()
            if app.args.sync_labels:
                for label in issue.get_labels():
                    labels.add(label.name)
                if issue.milestone:
                    labels.add(_ms_label(issue.milestone.id))

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

                my_tasks.add(task_id)

            else:
                status = "no task"

            logging.info("\t%d) %s - %s",
                issue.number, issue.title, status)

            # Sync tags/labels
            for task in my_tasks:
                task_data = app.get_saved_task_data(task)
                tag_ids = task_data.get('tags') or []
                try:
                    added_tags = 0
                    for label in labels:
                        tag_id = label_tag_map.get(label)
                        if not tag_id:
                            continue
                        if tag_id in tag_ids:
                            continue
                        tag_ids.append(tag_id)
                        app.asana.tasks.add_tag(task, tag=tag_id)
                        added_tags += 1

                    if added_tags:
                        logging.info("\t\t - added %d tags to %s",
                                     added_tags, task)
                        task_data['tags'] = tag_ids

                except app.asana_errors.InvalidRequestError:
                    logging.warn("warning: bad task %d", task)

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





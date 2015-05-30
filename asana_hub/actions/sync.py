"""
sync action

Syncs completion status of issues and their matched tasks.

"""

import logging

from ..action import Action

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
            '-full', '--sync-full',
            action='store_true',
            dest='sync_full',
            help="[sync] should sync full?",
            )

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        repo, project = self.get_repo_and_project()
        project_id = project['id']

        namespaces = ['open']
        if self.args.sync_full:
            namespaces.append('closed')

        # Load issues that we are tracking.
        for ns in namespaces:
            # Iterate over the issues in the opposite state as the namespace
            # we are in. We simply want to toggle these guys.
            other_ns = "open" if ns == "closed" else "closed"
            logging.info("collecting %s issues", other_ns)
            issues_map ={}
            for issue in repo.get_issues(state=other_ns):
                issue_number = str(issue.number)
                if app.has_saved_issue_data(issue_number, ns):
                    logging.info("\t%d) %s", issue.number, issue.title)
                    issues_map[issue_number] = issue
                    break

            for issue_number, issue in issues_map.iteritems():

                if ((ns == 'open' and not issue.closed_at) or
                    (ns == 'closed' and issue.closed_at)):
                    continue

                issue_data = app.get_saved_issue_data(issue_number, ns)
                for task_id in issue_data.get('tasks', []):
                    logging.info("Toggling #%d - %d", issue.number, task_id)
                    task = app.asana.tasks.find_by_id(task_id)
                    if not task: continue

                    if issue.closed_at:
                        # close task
                        app.asana.tasks.update(
                            task['id'],
                            {
                            'completed': True
                            })
                    else:
                        app.asana.tasks.update(
                            task['id'],
                            {
                            'completed': False
                            })

                app.move_saved_issue_data(issue_number, ns, other_ns)





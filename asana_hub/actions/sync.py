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
        issues = {}

        logging.info("tracking these issues:")

        for issue in repo.get_issues():
            issue_number = str(issue.number)
            for ns in namespaces:
                issues_map = issues[ns] = {}
                if app.has_saved_issue_data(issue_number, ns):
                    logging.info("\t%d) %s", issue.number, issue.title)
                    issues_map[issue_number] = issue
                    break

        for ns, issue_map in issues.iteritems():
            other_ns = "open" if ns == "closed" else "closed"
            for issue_number, issue in issue_map.iteritems():

                print issue.number, "number"
                print issue.title, "title"
                print issue.closed_at, "closed_at"
                print issue.closed_by, "closed_by"
                if ((ns == 'open' and not issue.closed_at) or
                    (ns == 'closed' and issue.closed_at)):
                    continue

                issue_data = app.get_saved_issue_data(issue_number, ns)
                for task_id in issue_data.get('tasks', []):
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

                self.move_saved_issue_data(issue_number, ns, other_ns)





"""
Command-line interface for asana-hub.
"""

import argparse
import logging
import sys
import os
import traceback

try:
    from asana import Client
    from asana import error as asana_errors
    from github import Github

    import urllib3
    import certifi

    # Setup pool manager and SSL verification.
    http = urllib3.PoolManager(
        cert_reqs='CERT_REQUIRED', # Force certificate check.
        ca_certs=certifi.where(),  # Path to the Certifi bundle.
    )

    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except:
        logging.debug("pyopenssl not detected.\n"
            "to install pyopenssl: "
            "pip install pyopenssl ndg-httpsclient pyasn1")

except ImportError:
    raise Exception("Could not import required packages.\n"
        "Did you pip install -r requirements.txt ?")

from .json_data import JSONData
from .action import Action

class ToolApp(object):

    def authenticate(self):
        """Connects to Github and Asana and authenticates via OAuth."""
        if self.oauth:
            return False

        # Save asana.
        self.settings.apply('api-asana', self.args.asana_api,
            "enter asana api key")

        # Save github.com
        self.settings.apply('api-github', self.args.github_api,
            "enter github.com token")

        logging.debug("authenticating asana api.")
        self.asana = Client.basic_auth(self.settings['api-asana'])
        self.asana_errors = asana_errors
        self.asana_me = self.asana.users.me()
        logging.debug("authenticating github api")
        self.github = Github(self.settings['api-github'])
        self.github_user = self.github.get_user()

        self.oauth = True

    @classmethod
    def _list_select(cls, lst, prompt, offset=0):
        """Given a list of values and names, accepts the index value or name."""

        inp = raw_input("select %s: " % prompt)
        assert inp, "value required."

        try:
            return lst[int(inp)+offset]
        except ValueError:
            return inp
        except IndexError:
            assert False, "bad value."

    def prompt_repo(self):

        # Select org
        orgs = [None]
        print "0) %s [you]" % self.github_user.name
        for idx, org in enumerate(self.github_user.get_orgs()):
            orgs.append(org)
            print "%d) %s" % (idx+1, org.name)

        org = self._list_select(orgs, "org")
        ctx = org or self.github_user

        repos = []
        for idx, repo in enumerate(ctx.get_repos()):
            repos.append(repo)
            print "%d) %s" % (idx, repo.name)

        repo = self._list_select(repos, "repo")
        logging.debug("repo id: %d", repo.id)

        return repo

    def prompt_project(self):

        # Select workspace
        workspaces = []
        for idx, workspace in enumerate(self.asana_me['workspaces']):
            workspaces.append(workspace)
            print "%d) %s" % (idx, workspace['name'])

        workspace = self._list_select(workspaces, "workspace")

        # Select workspace
        as_projects = self.asana.projects.find_by_workspace(workspace['id'],
            iterator_type=None)

        projects = []

        for idx, project in enumerate(as_projects):
            projects.append(project)
            print "%d) %s" % (idx, project['name'])

        project = self._list_select(projects, "project")

        return project

    @classmethod
    def make_asana_url(cls, project_id, task_id):
        """Returns a URL to an asana task."""
        return "https://app.asana.com/0/%d/%d" % (project_id, task_id)

    ##################
    ### Issue Data ###
    ##################

    @classmethod
    def _issue_data_key(cls, namespace):
        """Returns key for issue_data in data."""
        return 'issue_data_%s' % namespace

    def save_issue_data_task(self, issue, task, namespace='open'):
        """Saves a issue data (tasks, etc.) to local data.

        Args:
            issue:
                `int`. Github issue number.
            task:
                `int`. Asana task ID.
            namespace:
                `str`. Namespace for storing this issue.
        """

        issue_data = self.get_saved_issue_data(issue, namespace)

        if not issue_data.has_key('tasks'):
            issue_data['tasks'] = [task]
        elif task not in issue_data['tasks']:
            issue_data['tasks'].append(task)

    def has_saved_issue_data(self, issue, namespace='open'):
        issue_data_key = self._issue_data_key(namespace)
        issue_data = self.data.get(issue_data_key,
            {})

        if isinstance(issue, int):
            issue_number = str(issue)
        elif isinstance(issue, basestring):
            issue_number = issue
        else:
            issue_number = issue.number

        return issue_data.has_key(str(issue_number))

    def get_saved_issue_data(self, issue, namespace='open'):
        """Returns issue data from local data.

        Args:
            issue:
                `int`. Github issue number.
            namespace:
                `str`. Namespace for storing this issue.
        """

        if isinstance(issue, int):
            issue_number = str(issue)
        elif isinstance(issue, basestring):
            issue_number = issue
        else:
            issue_number = issue.number

        issue_data_key = self._issue_data_key(namespace)
        issue_data = self.data.get(issue_data_key,
            {})

        _data = issue_data.get(str(issue_number), {})
        issue_data[str(issue_number)] = _data
        return _data

    def move_saved_issue_data(self, issue, ns, other_ns):
        """Moves an issue_data from one namespace to another."""

        if isinstance(issue, int):
            issue_number = str(issue)
        elif isinstance(issue, basestring):
            issue_number = issue
        else:
            issue_number = issue.number

        issue_data_key = self._issue_data_key(ns)
        other_issue_data_key = self._issue_data_key(other_ns)
        issue_data = self.data.get(issue_data_key,
            {})
        other_issue_data = self.data.get(other_issue_data_key,
            {})

        _id = issue_data.pop(issue_number, None)
        if _id:
            other_issue_data[issue_number] = _id

        self.data[other_issue_data_key] = other_issue_data
        self.data[issue_data_key] = issue_data

    #################
    ### Task Data ###
    #################

    @classmethod
    def _task_data_key(cls):
        """Returns key for task_data in data."""
        return 'task-data'

    def has_saved_task_data(self, task):
        task_data_key = self._task_data_key()
        task_data = self.data.get(task_data_key,
            {})

        if isinstance(task, int):
            task_number = str(task)
        elif isinstance(task, basestring):
            task_number = task
        else:
            task_number = task['id']

        return task_data.has_key(str(task_number))

    def get_saved_task_data(self, task):
        """Returns task data from local data.

        Args:
            task:
                `int`. Asana task number.
        """

        if isinstance(task, int):
            task_number = str(task)
        elif isinstance(task, basestring):
            task_number = task
        else:
            task_number = task['id']

        task_data_key = self._task_data_key()
        task_data = self.data.get(task_data_key, {})

        _data = task_data.get(str(task_number), {})
        task_data[str(task_number)] = _data
        return _data

    #############
    ### Misc. ###
    #############

    def announce_issue_to_task(self, asana_task_id, issue):
        """Creates a story on a task announcing the issue."""
        return self.asana.stories.create_on_task(asana_task_id,
            {
            'text':
                "Git Issue #%d: \n"
                "%s" % (
                    issue.number,
                    issue.html_url,
                    )
            })

    def get_asana_task(self, asana_task_id):
        """Retrieves a task from asana."""

        try:
            return self.asana.tasks.find_by_id(asana_task_id)
        except asana_errors.NotFoundError:
            return None
        except asana_errors.ForbiddenError:
            return None

    def __init__(self, version):
        """Accepts version of the app."""

        # Setup settings
        self.version = version
        self.exit_code = 999
        self.oauth = False

        # Setup logging
        self.logger = logging.getLogger()
        formatter = logging.Formatter("%(message)s")
        self.logger.setLevel(logging.DEBUG)
        self.logger.propagate = False
        self.logger.handlers = []
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        parser = argparse.ArgumentParser(description='Loudr Utility Tool')

        # Default paths for settings and data
        def_settings_file = os.path.join(
            os.path.expanduser("~"),
            '.asana-hub',
            )

        def_data_file = os.path.expanduser("./.asana-hub.proj")

        # Load actions
        actions = {}
        choices = []
        help_msgs = ''

        for action in Action.iter_actions():
            actions[action.name] = action
            choices.append(action.name)
            help_msgs += '\n-  %s: %s' % (action.name, action.__doc__)

        help_msgs += '\n'

        parser.add_argument(
            'action',
            action='store',
            nargs=1,
            help=help_msgs,
            choices=choices,
            )

        parser.add_argument(
            '-vv', '--verbose',
            action='store_true',
            dest='verbose',
            help="use debugging verbosity.",
            )

        parser.add_argument(
            '-s', '--settings-file',
            action='store',
            nargs='?',
            dest='settings_file',
            default=def_settings_file,
            help="path to save oauth api keys.",
            )

        parser.add_argument(
            '-d', '--data-file',
            action='store',
            nargs='?',
            dest='data_file',
            default=def_data_file,
            help="path to save repository and project based data.",
            )

        # Add action arguments.
        for action in actions.values():
            action.add_arguments(parser)

        # Add actions from the parent class. (The settings)
        Action.add_arguments(parser)

        parser.add_argument('-v', '--version', action='version',
            version='%(prog)s ' + '%s' % version)

        self.args = parser.parse_args()

        if len(sys.argv) < 2:
            parser.print_help()
            self.exit_code = 1
            return

        if self.args.verbose:
            ch.setLevel(logging.DEBUG)

        # Load settings
        self.settings = JSONData(filename=self.args.settings_file,
            args=self.args, version=version)

        self.data = JSONData(filename=self.args.data_file,
            args=self.args, version=version)

        # Load action method and call.
        try:
            action_name = self.args.action[0]
            action_class = actions.get(action_name)
            if not action_class:
                raise NotImplementedError(
                    "%s is not implemented." % action_name)

            # Instantiate and run
            action = action_class(app=self, args=self.args)
            action.run()
        except AssertionError as exc:
            logging.error("Error: %s", unicode(exc))
            logging.debug("%s", traceback.format_exc())
            self.exit_code = 1
            return
        except Exception as exc:
            logging.exception("Exception: %r", exc)
            self.exit_code = 129
            return
        finally:

            # Save settings
            self.settings.save()
            # Save data
            self.data.save()

        self.exit_code = 0


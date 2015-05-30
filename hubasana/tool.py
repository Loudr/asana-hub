"""
Command-line interface for hubasana.
"""

import argparse
import logging
import sys

try:
    from asana import Client
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

from .settings import Settings

class ToolApp(object):

    def oauth_start(self):
        if self.oauth:
            return False

        self.settings.assert_key('api-asana')
        self.settings.assert_key('api-github')

        logging.debug("authenticating asana api.")
        self.asana = Client.basic_auth(self.settings['api-asana'])
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

    def connect(self):
        """Connects OAuth libraries."""

        # Save asana.
        self.settings.apply('api-asana', self.args.asana_api,
            "enter asana api key")

        # Save github.com
        self.settings.apply('api-github', self.args.github_api,
            "enter github.com token")

        self.oauth_start()

        logging.info("connected ok.")

    @classmethod
    def make_asana_url(cls, project_id, task_id):
        """Returns a URL to an asana task."""
        return "https://app.asana.com/0/%d/%d" % (project_id, task_id)

    def create(self):

        self.oauth_start()

        # Get repo
        repo = self.settings.apply('github-repo', self.args.github_repo,
            self.prompt_repo,
            on_load=self.github.get_repo,
            on_save=lambda r: r.id
            )

        assert repo, "repository not found."

        # Get project
        project = self.settings.apply('asana-project', self.args.asana_project,
            self.prompt_project,
            on_load=self.asana.projects.find_by_id,
            on_save=lambda p: p['id']
            )

        assert project, "project not found."

        # Collect title and body
        title = self.settings.apply(None, self.args.title,
            "task/issue title",
            )

        assert title, "title required"

        body = self.settings.apply(None, self.args.body,
            "body/message",
            ) or ''

        # Post asana task.
        asana_workspace_id = project['workspace']['id']
        task = self.asana.tasks.create_in_workspace(
            asana_workspace_id,
            {
            'name': title,
            'notes': body,
            'assignee': 'me',
            'projects': [project['id']]
            })

        asana_task_id = task['id']
        asana_task_url = self.make_asana_url(project['id'], asana_task_id)

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
        self.asana.stories.create_on_task(asana_task_id,
            {
            'text':
                "Git Issue #%d: \n"
                "%s" % (
                    issue.number,
                    issue.html_url,
                    )
            })

        logging.info("github issue #%d created:\n%s\n",
            issue.number, issue.html_url)

        logging.info("asana task #%d created:\n%s\n",
            asana_task_id, asana_task_url)

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

        parser.add_argument(
            'action',
            action='store',
            nargs=1,
            help='action to take',
            choices=[
                'connect',
                'create',
            ]
            )

        parser.add_argument(
            '-d', '--verbose',
            action='store_true',
            dest='verbose',
            help="use debugging verbosity.",
            )

        parser.add_argument(
            '-s', '--settings-file',
            action='store',
            nargs='?',
            dest='settings_file',
            default='.hubasana',
            help="file to use instead of .hubasana to store oauth & settings.",
            )

        parser.add_argument(
            '--asana-api',
            action='store',
            nargs='?',
            const='',
            dest='asana_api',
            help="asana api key.",
            )

        parser.add_argument(
            '--github-token',
            action='store',
            nargs='?',
            const='',
            dest='github_api',
            help="github api token.",
            )

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

        parser.add_argument(
            '--title',
            action='store',
            nargs='?',
            const='',
            dest='title',
            help="task/issue title.",
            )

        parser.add_argument(
            '--body',
            action='store',
            nargs='?',
            const='',
            dest='body',
            help="task/issue body.",
            )

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
        self.settings = Settings(args=self.args, version=version)

        # Load action method and call.
        try:
            action = self.args.action[0]
            method = getattr(self, action, None)
            if method is None:
                raise NotImplementedError("%s is not implemented." % action)

            method()

            # Save settings
            self.settings.save()
        except AssertionError as exc:
            logging.error(unicode(exc))
            self.exit_code = 1
            return
        except Exception as exc:
            logging.exception("Exception: %r", exc)
            self.exit_code = 129
            return

        self.exit_code = 0


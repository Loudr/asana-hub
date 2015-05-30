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

    def run(self):
        app = self.app

        # OAuth 2 exchange.
        app.authenticate()

        # Get repo
        repo = app.settings.apply('github-repo', app.args.github_repo,
            app.prompt_repo,
            on_load=app.github.get_repo,
            on_save=lambda r: r.id
            )

        assert repo, "repository not found."

        # Get project
        project = app.settings.apply('asana-project', app.args.asana_project,
            app.prompt_project,
            on_load=app.asana.projects.find_by_id,
            on_save=lambda p: p['id']
            )

        assert project, "project not found."

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
        app.asana.stories.create_on_task(asana_task_id,
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

        # Save issue and task to db.
        app.save_issue_task(issue.number, asana_task_id)

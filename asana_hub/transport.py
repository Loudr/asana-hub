# -*- coding: utf-8 -*-
"""
transport queue handlers

Provides an interface for multiprocessing transport queues.

"""

import logging
import re
import multiprocessing
import Queue
import urllib3
import certifi

from asana import Client
from asana import error as asana_errors
from github import Github

import tool

mem = multiprocessing.Manager()

data = mem.dict()
"""Transient data about github and asana repo."""

shutdown_event = mem.Event()
"""Shutdown event"""

queue = mem.Queue()
"""Multiprocessing transport queue."""

settings_queue = mem.Queue()
"""Multprocessing queue for updating settings."""

processes = []
"""Contains running workers."""

ASANA_SECTION_RE = re.compile(r'## Asana Tasks:\s+(.*#(\d{12,}))+', re.M)
"""Regular exprsssion to catch malformed data due to too many tasks."""

class TransportWorker(object):

    """Represents a single thread worker that responds to a queue of tasks.
    """

    def __init__(self, settings):
        self.settings = settings
        self.asana = Client.basic_auth(self.settings['api-asana'])
        self.asana_me = self.asana.users.me()
        self.github = Github(self.settings['api-github'])
        self.github_user = self.github.get_user()

    def get_repo(self):
        return self.github.get_repo(data['github-repo'])

    def run(self):

        while True:

            if shutdown_event.is_set():
                logging.debug("got shutdown signal")
                break

            try:
                packet = queue.get(timeout=5)
            except Queue.Empty:
                continue

            # Handle packet
            packet_task = packet.pop('task')
            method = getattr(self, packet_task, None)
            if not method:
                raise Exception("Packet method '%s' is not supported." %
                                packet_task)

            logging.debug("running packet: %s", packet_task)
            method(**packet)

    def create_missing_task(self,
                            asana_workspace_id,
                            name,
                            assignee,
                            projects,
                            completed,
                            issue_number,
                            issue_html_url,
                            issue_state,
                            issue_body,
                            tasks,
                            labels,
                            label_tag_map):

        """Creates a missing task."""

        task = self.asana.tasks.create_in_workspace(
            asana_workspace_id,
            {
                'name': name,
                'notes': issue_body,
                'assignee': assignee,
                'projects': projects,
                'completed': completed,
            })

        # Announce task git issue
        task_id = task['id']

        put("create_story",
            task_id=task_id,
            text="Git Issue #%d: \n"
                  "%s" % (
                    issue_number,
                    issue_html_url,
                    )
            )

        put("apply_tasks_to_issue",
            tasks=[task_id],
            issue_number=issue_number,
            issue_body=issue_body,
            )

        # Save task to drive
        put_setting("save_issue_data_task",
                    issue=issue_number,
                    task_id=task_id,
                    namespace=issue_state)

        tasks.append(task_id)

        # Sync tags/labels
        put("sync_tags",
            tasks=tasks,
            labels=labels,
            label_tag_map=label_tag_map)

    def add_tag(self, task_id, tag_id):

        try:
            self.asana.tasks.add_tag(task_id=task_id, tag=tag_id)
        except asana_errors.InvalidRequestError:
            logging.warn("warning: bad task %d", task_id)

    def sync_tags(self, tasks, labels, label_tag_map):

        for task_id in tasks:
            tag_ids = []
            try:
                added_tags = 0
                for label in labels:
                    tag_id = label_tag_map.get(label)
                    if not tag_id:
                        continue
                    # if tag_id in tag_ids:
                    #     continue
                    tag_ids.append(tag_id)
                    put("add_tag",
                        task_id=task_id,
                        tag_id=tag_id)
                    added_tags += 1

                if added_tags:
                    put_setting("add_tags_to_task",
                                task_id=task_id,
                                tag_ids=tag_ids)

            except asana_errors.InvalidRequestError:
                logging.warn("warning: bad task %d", task_id)

    def create_story(self, task_id, text):

        self.asana.stories.create_on_task(task_id,
                                          { 'text': text })

    def issue_edit(self, issue_number, body):

        repo = self.get_repo()
        issue = repo.get_issue(issue_number)
        issue.edit(body=body)


    def apply_tasks_to_issue(self, tasks, issue_number, issue_body):
        """Applies task numbers to an issue."""
        issue_body = issue_body
        task_numbers = format_task_numbers_with_links(tasks)
        if task_numbers:
            new_body = ASANA_SECTION_RE.sub('', issue_body)
            new_body = new_body + "\n## Asana Tasks:\n\n%s" % task_numbers
            put("issue_edit",
                issue_number=issue_number,
                body=new_body)
            return new_body

        return issue_body

    def update_task(self, task_id, params):
        self.asana.tasks.update(task_id, params)


def run_worker(settings):
    try:
        worker = TransportWorker(settings)
        worker.run()
    except:
        shutdown_event.set()
        raise

def put(task, **kwargs):
    kwargs['task'] = task
    queue.put(kwargs)

def put_setting(task, **kwargs):
    """Pushes a setting to the queue."""
    kwargs['task'] = task
    settings_queue.put(kwargs)

def flush(callback=None):
    """Waits until queue is empty."""

    while True:
        if shutdown_event.is_set():
            return

        if callable(callback):
            callback()

        try:
            item = queue.get(timeout=1)
            queue.put(item)  # put it back, we're just peeking.
        except Queue.Empty:
            return

def issue_edit(issue, **kwargs):
    """Saves an issue"""
    put("issue_edit",
        issue_number=issue.number,
        **kwargs)

def task_create(asana_workspace_id, name, notes, assignee, projects,
                completed, **kwargs):
    """Creates a task"""
    put("task_create",
        asana_workspace_id=asana_workspace_id,
        name=name,
        notes=notes,
        assignee=assignee,
        projects=projects,
        completed=completed,
        **kwargs)

def start(app):

    logging.debug("Starting multiprocess workers")
    for _ in range(multiprocessing.cpu_count()):
        process = multiprocessing.Process(target=run_worker,
                                          kwargs={
                                            'settings': app.settings.data,
                                          })
        process.start()
        processes.append(process)

def shutdown():
    logging.debug("Shutting down transporter")

    shutdown_event.set()
    for p in processes:
        p.join()

def is_shutdown():
    """Returns True if the app is requesting a global shutdown."""
    return shutdown_event.is_set()

def iter_settings():
    """Yields items from the settings queue."""

    while True:
        try:
            item = settings_queue.get(timeout=1)
            yield item
        except Queue.Empty:
            return

def format_task_numbers_with_links(tasks):
    """Returns formatting for the tasks section of asana."""

    project_id = data.get('asana-project', None)

    def _task_format(task_id):
        if project_id:
            asana_url = tool.ToolApp.make_asana_url(project_id, task_id)
            return "[#%d](%s)" % (task_id, asana_url)
        else:
            return "#%d" % task_id

    return "\n".join([_task_format(tid) for tid in tasks])

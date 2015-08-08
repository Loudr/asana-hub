# -*- coding: utf-8 -*-
"""
transport queue handlers

Provides an interface for multiprocessing transport queues.

"""

import logging
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
                            notes,
                            assignee,
                            projects,
                            completed,
                            issue_number,
                            issue_html_url,
                            issue_state,
                            tasks):

        """Creates a missing task."""

        task = self.asana.tasks.create_in_workspace(
            asana_workspace_id,
            {
                'name': name,
                'notes': notes,
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

        # Save task to drive
        put_setting("save_issue_data_task",
                    issue=issue_number,
                    task_id=task_id,
                    namespace=issue_state)

        tasks.append(task_id)

    def create_story(self, task_id, text):

        self.asana.stories.create_on_task(task_id,
                                          { 'text': text })

    def issue_edit(self, issue_number, body):

        repo = self.get_repo()
        issue = repo.get_issue(issue_number)
        issue.edit(body=body)

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

def flush():
    """Waits until queue is empty."""

    while True:
        if shutdown_event.is_set():
            return

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

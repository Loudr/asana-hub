asana-hub v0.2.0
================

.. image:: https://img.shields.io/pypi/v/asana-hub.svg    :target:
.. image:: https://img.shields.io/pypi/dm/asana-hub.svg   :target:

A python tool for creating issues and tasks simultaneously on github and
asana, and keeping them in sync.

One-two-three Create an Asana *task* and matching Github *issue* in a
repository, and *eventually* keep them in sync.

Setup
-----

Either with ``sudo`` or in a ``virtualenv``:

.. code:: bash

    $ pip install asana-hub
    $ asana-hub connect

Usage
-----

.. code:: bash

    # Connect Asana & Github Accounts
    $ asana-hub connect
    asana linked.
    github.com account linked.

    $ asana-hub create
    Select github.com repository, by name or number.
    1) my-repo

    > my-repo

    Select project to create task in.
    1) Project 1 (alias)
    2) Project 2
    3) Other Project
    or alias.

    > 2

    Task/Issue Name:
    > This is my first bug.

    Description:
    > This is a nasty bug.

    github issue #5 created:
    https://github.com/my-repo/issues/5

    asana task #654321 created:
    https://app.asana.com/0/123456/654321

When issue+task pairs are created via `asana-hub`, they may be kept in sync via

.. code:: bash

    $ asana-hub sync

This will iterate over all issues that have closed since the last update, and
complete any corresponding asana tasks.

.asana-hub and .asana-hub.proj
------------------------------

asana-hub creates a settings file in your home folder called
``.asana-hub`` to store your asana & github api tokens.

a ``.asana-hub.proj`` exists to maintain sync data in your repository,
including: \* selected github repository id \* selected asana project id
\* created issues and tasks (for sync)

.. |PyPi version| image:: https://img.shields.io/pypi/v/asana-hub.svg
   :target: https://pypi.python.org/pypi/asana-hub
.. |PyPi downloads| image:: https://img.shields.io/pypi/dm/asana-hub.svg
   :target: https://pypi.python.org/pypi/asana-hub

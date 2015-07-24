# asana-hub

[ ![PyPi version](https://img.shields.io/pypi/v/asana-hub.svg) ](https://pypi.python.org/pypi/asana-hub)
[ ![PyPi downloads](https://img.shields.io/pypi/dm/asana-hub.svg) ](https://pypi.python.org/pypi/asana-hub)

asana-hub is a python tool for creating issues and tasks simultaneously on github and asana,
and keeping them in sync.

One-two-three Create an Asana *task* and matching Github *issue* in a repository,
and _eventually_ keep them in sync.

## Setup

Either with `sudo` or in a `virtualenv`:

```bash
$ pip install asana-hub
$ asana-hub connect
```

## Usage

### Connecting OAuth API keys - `connect`

```bash
$ asana-hub connect
```

You will be prompted by asana api key and github token (for `repo`, `user`, `gist`).
These may also be passed via command line arguments as `-gh-api` and `-as-api`.
These settings will be stored in `~/.asana-hub `.


### Syncing Task Issue Status -> Asana Tasks - `sync`

The main appeal of asana-hub is to **keep issue statuses propogated to asana.**

`asana-hub sync` is responsible for iterating over all issues in a repository,
and ensuring that tasks mentioned inside of issue descriptions are connected and
kept in sync.

```bash
$ git checkout master  # keep master in sync, or potential merge conflicts loom
$ asana-hub sync

collecting github.com issues
    20) better usage docs - no task
    1) Create successful task/issue in correct repo. - no task
    updating #27 (open->closed) - 36700026060600
    updating #27 (open->closed) - 36700026060602
    updating #27 (open->closed) - 36700026060604
    updating #27 (open->closed) - 36700026060606
```

This will iterate over all issues that have closed since the last update, and
complete any corresponding asana tasks.

Issues that have no asana tasks are always reported as `- no task`.

#### Creating new tasks for issues on github

To create tasks automatically for issues that lack tasks, use `--create-missing-tasks`.
This will create asana tasks for issues that do not have `#ASANAID`s annotated.
The tasks are created in the connected project. You can change this project with
the `--project [project]` argument.

#### Limiting sync to newer issues with `--first-issue`

If you don't wish to create tasks for older issues, which is very likely,
you can use the `--first-issue [issue]` argument to limit syncing to issues
including and after an issue of your choice.

For example, if you wanted to start using asana-hub for issues #12 and above,
you would perform:

```bash
$ git checkout master  # keep master in sync, or potential merge conflicts loom
$ asana-hub sync --first-issue 12 --create-missing-tasks

```

After using `first-issue`, its value is stored for subsequent calls to
`asana-hub sync`, and other commands.

### Creating a new issue & task - `issue`

Create a new asana task and github.com issue simultaneously. A connection is kept
between the two by a repo-backed JSON database of issues.

```bash
$ asana-hub issue --title "better usage docs" --body "improve the docs"
$ asana-hub issue  # for prompts

github issue #19 created:
https://github.com/Loudr/asana-hub/issues/19

asana task #36089434604514 created:
https://app.asana.com/0/36084070893405/36089434604514
```

(see how this changed in the history of [77d58c0777045fc82b85e6f94a39db4ea3116b62](https://github.com/Loudr/asana-hub/commit/77d58c0777045fc82b85e6f94a39db4ea3116b62))

`asana-hub sync` updates the asana task status when the issue changes status (open->closed).


#### What about issues I create on github.com?

Creating an issue on github without using `asana-hub` is expected behavior.
Any `#ASANATASKS` named in the body of the issue in the format of `#2394233842334`
are automatically connected.

Connecting your issues and asana tasks is as simple as including all asana task IDs
on the issue body.


### Creating a new pull request & task

Create a pull request and sub-task connected to an original issue.

```bash
$ git checkout -b better-usage-docs  # while on a feature branch
$ git touch changes  # made changes to docs here
$ git commit -am "commit as normal"
$ git push --set-upstream origin better-usage-docs  # sync with github

$ asana-hub pr --issue 19 --branch better-usage-docs
$ asana-hub pr  # for prompts

github pull_request #20 created:
https://github.com/Loudr/asana-hub/pull/20
```

(These are the actual pull requests and issues matching this project - see #19 and #20)

A pull request on github is represented by a sub-task on asana.
The pull request will belong to the task that matched original issue.

Pull requests are managed by linking pull requests directly to issues,
and creating a matching asana task. This sub-task will live under the
issue's task, providing a visable heirachy of `issue` to `pull-request`
on asana.

When `asana-hub sync` is performed, all pull requests that have been merged
will have their tasks updated on asana.

Likewise, if those pull requests include "fixes #19" in the description,
as these pull requests do by default, the issue will be closed and the
issue's task on asana will be completed.


## .asana-hub and .asana-hub.proj

asana-hub creates a settings file in your home folder called `.asana-hub` to store your asana & github api tokens.

a `.asana-hub.proj` exists to maintain sync data in your repository, including:
    * selected github repository id
    * selected asana project id
    * created issues and tasks (for sync)

An obvious future optimization will be to allow multiple projects,
selected by `alias`, to be managed in one repository. (#21)

See an example of the [.asana-hub.proj](https://github.com/Loudr/asana-hub/blob/master/.asana-hub.proj).

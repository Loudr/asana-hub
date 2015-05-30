# hubasana
Github Asana Issue Tool

One-two-three Create an Asana *task* and matching Github *issue* in a repository,
and _eventually_ keep them in sync.

## Setup

Either with `sudo` or in a `virtualenv`:

```bash
$ pip install -r requirements.txt
$ python hubasana.py connect
```

## Usage

```bash
# Connect Asana & Github Accounts
$ python hubasana.py connect
asana linked.
github.com account linked.

$ python hubasana.py create
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

```

## .hubasana and .hubasana.proj

hubasana creates a settings file in your home folder called `.hubasana` to store your asana & github api tokens.

a `.hubasana.proj` exists to maintain sync data in your repository, including:
    * selected github repository id
    * selected asana project id
    * created issues and tasks (for sync)



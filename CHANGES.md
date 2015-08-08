# asana-hub Changelog

## HEAD

- #47 - **Multiprocessing requests.**
    - Enables parallel HTTP requests for `sync`.

- #51 - Github issues now include links to Asana tasks.

- #46 - BUG: fix for missing github issue.

## 0.2.7 - mary-ann

- #45 - BUG: fix for ForbiddenError.

## 0.2.6 - pippin

- **Syncing of milestones to labels**.
    - `asana-hub sync --sync-labels` (or `-l`)

Previous releases:

- **Sync a repositories issues to an asana project**
   - `asana-hub sync`
   - Ability to create tasks for issues that aren't linked in the body with `#ASANAID`.
       - `asana-hub sync --create-missing-tasks` (or `-c`)
   - Picking up linked asana tasks from issue descriptions using `#ASANAID` notation
   - Sync can start at a `--first-issue`
- **Create pull requests & issues from command line**
   - `asana-hub issue`
   - `asana-hub pr`
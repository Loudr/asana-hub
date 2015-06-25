# asana-hub Changelog

## 0.2.6 - pippin

Adds support for:

- Syncing of milestones to comments.
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
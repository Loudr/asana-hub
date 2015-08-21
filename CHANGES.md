# asana-hub Changelog

## HEAD

## 0.2.10 - tailor spiff

- BUG: Fixes regression bug of ForbiddenError on task updates. (#45)

## 0.2.9 - ganondorf prime

- Fixes `asana-hub sync` regression. (#57)

## 0.2.8 - ganondorf

- **Multiprocessing requests.** (#47)
    - Enables parallel HTTP requests for `sync`.

- Github issues now include links to Asana tasks. (#51)
    - Issues are now updated with task links on initial connection. (#54)

- BUG: fix for missing github issue. (#46)

## 0.2.7 - mary-ann

- BUG: fix for ForbiddenError. (#45)

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
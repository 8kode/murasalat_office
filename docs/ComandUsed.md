# GitHub — Project Development Setup

## 1. Navigate to the Project Directory

```bash
cd ~/frappe-bench/apps/murasalat_office
# Navigate to the Murasalat Office application directory.
# All Git operations below will be performed within this project.
```

## 2. Check the Current Git Status

```bash
git status
# Display the current status of the Git repository.
# This shows modified, added, deleted, or untracked files.
# It also indicates the current branch.
```

## 3. Create and Switch to the `develop` Branch

```bash
git checkout -b develop
# Create a new Git branch named "develop".
# The command automatically switches the working directory to the new branch.
# This branch will be used for ongoing development work.
```

## 4. Stage All Project Changes

```bash
git add .
# Add all new, modified, and deleted files in the project directory
# to the Git staging area in preparation for committing them.
```

## 5. Commit the Changes

```bash
git commit -m "Add Plan To Project"
# Create a Git commit containing all staged changes.
# The message describes the purpose of this commit.
```

## 6. Create the Documentation Directory

```bash
mkdir -p docs
# Create a directory named "docs" for project documentation.
# The "-p" option ensures that the command does not return an error
# if the directory already exists.
```

## 7. Create the Data Model Documentation File

```bash
touch docs/data-model.md
# Create an empty Markdown file named "data-model.md".
# This file will be used to document the project's data model,
# including DocTypes, relationships, fields, and other database structures.
```


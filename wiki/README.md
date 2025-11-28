# Wiki Source

This folder contains the source files for the GitHub Wiki.

**DO NOT EDIT THE WIKI DIRECTLY** - Edit files here and push to main.

The `publish-wiki.yml` workflow automatically syncs this folder to:
https://github.com/jbcom/jbcom-control-center/wiki

## Structure

- `Home.md` → Wiki home page
- `_Sidebar.md` → Navigation sidebar
- `Memory-Bank-*.md` → Current context and progress
- `Agentic-Rules-*.md` → Agent guidelines
- `Agent-Instructions-*.md` → Per-agent instructions
- `Documentation-*.md` → Technical docs
- `Recovery-*.md` → Session recovery logs

## Local Preview

Files are standard Markdown. Use any Markdown previewer.

## Workflow

1. Edit files in `wiki/`
2. Commit and push to `main`
3. Workflow syncs to wiki automatically

# Agent Task: Migrate Slack Operations to vendor-connectors

## Objective
Migrate Slack operations from `terraform-modules` to `vendor-connectors/slack/` package.

## Source Methods (from terraform_data_source.py)
- `get_slack_users` (line ~8302) - List Slack workspace users
- `get_slack_usergroups` (line ~8446) - List Slack usergroups with members
- `get_slack_conversations` (line ~8602) - List Slack conversations/channels

## Target Location
`/workspace/packages/vendor-connectors/src/vendor_connectors/slack/__init__.py`

## Migration Guidelines

### 1. Pattern to Follow
```python
def list_users(
    self,
    include_bots: bool = False,
    unhump_users: bool = True,
) -> dict[str, dict[str, Any]]:
    """List Slack workspace users.
    
    Args:
        include_bots: Include bot users. Defaults to False.
        unhump_users: Convert keys to snake_case. Defaults to True.
        
    Returns:
        Dictionary mapping user IDs to user data.
    """
```

### 2. Key Changes
- Remove `exit_run()` wrapper - return data directly
- Remove `exit_on_completion` parameter
- Add Google-style docstrings
- Use `unhump_map` from `extended_data_types` for snake_case conversion
- Use pagination properly (Slack uses cursor-based pagination)

### 3. Existing Code Reference
Check `/workspace/packages/vendor-connectors/src/vendor_connectors/slack/__init__.py` for existing structure.

### 4. Methods to Add
1. `list_users()` - Full user listing with profile data
2. `get_user()` - Get single user by ID
3. `list_usergroups()` - List usergroups with optional member expansion
4. `get_usergroup()` - Get single usergroup
5. `list_conversations()` - List channels/conversations
6. `get_conversation()` - Get single conversation

### 5. Testing
Run: `uv run python -m pytest packages/vendor-connectors/tests -v --no-cov`

### 6. Completion Criteria
- [ ] All methods migrated with proper docstrings
- [ ] Linter passes: `uv run ruff check packages/vendor-connectors/src`
- [ ] Tests pass
- [ ] Create PR with changes

# Ecosystem Repositories

This template manages and coordinates the jbcom Python library ecosystem.

## Managed Repositories

### 1. extended-data-types
**Repository:** https://github.com/jbcom/extended-data-types
**PyPI:** https://pypi.org/project/extended-data-types/
**Latest Version:** 2025.11.164
**Purpose:** Foundation library providing extended data type utilities

**Key Features:**
- `get_unique_signature()` - Generate unique signatures for objects
- `make_raw_data_export_safe()` - Sanitize data for export/logging
- `strtobool()` - Convert strings to booleans reliably
- `strtopath()` - Convert strings to Path objects with validation
- Data type conversions and utilities
- Safe serialization helpers

**Dependencies:** Minimal - this is a foundational library
**Dependents:** lifecyclelogging, directed-inputs-class, vendor-connectors

**Management Tasks:**
- Keep dependencies minimal
- Maintain backward compatibility
- Comprehensive testing (100% coverage goal)
- Performance optimization
- Type hint completeness

### 2. lifecyclelogging
**Repository:** https://github.com/jbcom/lifecyclelogging  
**PyPI:** https://pypi.org/project/lifecyclelogging/
**Purpose:** Structured logging library with lifecycle management

**Key Features:**
- Lifecycle-aware logging (start, progress, completion, error states)
- Automatic data sanitization using extended-data-types
- Context managers for log lifecycle
- Structured log output formats
- Integration with Python logging module

**Dependencies:**
- extended-data-types (for sanitization)

**Management Tasks:**
- Ensure all logged data is sanitized
- Maintain logging performance
- Keep API simple and intuitive
- Documentation with examples
- Integration tests

### 3. directed-inputs-class
**Repository:** https://github.com/jbcom/directed-inputs-class
**PyPI:** TBD (upcoming)
**Purpose:** Input validation and processing with type safety

**Key Features:**
- Declarative input validation
- Type coercion and conversion
- Dependency-based field processing
- Error aggregation and reporting
- Integration with extended-data-types

**Dependencies:**
- extended-data-types (for type conversions)

**Status:** In development - needs template migration

**Management Tasks:**
- Migrate to python-library-template structure
- Add comprehensive tests
- Complete type hints
- Documentation and examples
- Release initial version to PyPI

### 4. vendor-connectors
**Repository:** https://github.com/jbcom/vendor-connectors
**PyPI:** TBD (upcoming)
**Purpose:** Unified interface for third-party service integrations

**Key Features:**
- Abstract connector interface
- Common authentication patterns
- Rate limiting and retry logic
- Error handling and logging
- Vendor-specific implementations

**Dependencies:**
- extended-data-types (for data handling)
- lifecyclelogging (for connection lifecycle)

**Status:** Planning/early development

**Management Tasks:**
- Design unified connector interface
- Implement core abstract classes
- Add vendor-specific connectors
- Comprehensive testing with mocks
- Security audit for credential handling

## Ecosystem Dependencies

```
extended-data-types (foundation)
  ↓
  ├── lifecyclelogging
  ├── directed-inputs-class
  └── vendor-connectors
       ↑
       └── uses lifecyclelogging
```

## Coordination Guidelines

### Version Compatibility
- All libraries use CalVer (YYYY.MM.BUILD)
- Pin to minimum versions: `extended-data-types>=2025.11.0`
- Test against latest versions in CI
- Document breaking changes in CHANGELOG.md

### Cross-Repository Changes

When a change in one library affects others:

1. **Plan the change:**
   - Identify affected repositories
   - Check if it's a breaking change
   - Plan migration path if needed

2. **Implementation order:**
   - Update foundation libraries first (extended-data-types)
   - Update dependent libraries in dependency order
   - Test each library's CI passes

3. **Release coordination:**
   - Release foundation library first
   - Wait for PyPI availability (~5 minutes)
   - Update dependents to require new version
   - Release dependent libraries

4. **Communication:**
   - Update CHANGELOG.md in each repo
   - Document breaking changes
   - Update this ecosystem doc

### Adding New Ecosystem Libraries

1. Create from python-library-template
2. Follow the TEMPLATE_USAGE.md guide
3. Add to this ecosystem document
4. Configure PyPI trusted publishing
5. First release via main branch push

### Centralized Management Tasks

From this repository, agents can:

**Update dependencies across ecosystem:**
```bash
# Update security patches
for repo in extended-data-types lifecyclelogging directed-inputs-class vendor-connectors; do
  cd ../$repo
  # Update pyproject.toml dependencies
  # Run tests
  # Create PR if needed
done
```

**Run ecosystem-wide checks:**
```bash
# Check all repos have consistent tooling
# Verify all use same ruff/mypy/pytest configs
# Ensure all CIs are up to date
```

**Coordinate releases:**
```bash
# When updating template CI
# Push updates to all managed repos
# Ensure compatibility
```

## Ecosystem Maintenance Schedule

### Weekly
- Check for dependency updates
- Run security audits
- Monitor PyPI download stats
- Review open issues/PRs

### Monthly  
- Update Python version support
- Refresh documentation
- Performance benchmarks
- Dependency cleanup

### Quarterly
- Major feature planning
- Breaking change coordination
- Ecosystem health review
- Documentation overhaul

## Agent Instructions for Ecosystem Work

### When Working on extended-data-types

This is the foundation - be extra careful:
- All changes must maintain backward compatibility
- 100% test coverage required
- Performance regressions not acceptable
- Breaking changes require ecosystem-wide coordination

### When Working on dependent libraries

- Always use extended-data-types utilities
- Don't reimplement what extended-data-types provides
- Keep dependencies minimal
- Document any extended-data-types features you rely on

### Cross-repo refactoring

1. Start in this template repo
2. Test changes in extended-data-types first
3. Roll out to other libs in dependency order
4. Create PRs, don't auto-merge
5. Verify each library's CI independently

### Emergency fixes

For security issues or critical bugs:
1. Fix in affected library immediately
2. Create hotfix PR
3. Fast-track review and merge
4. Release immediately
5. Update dependent libraries if needed
6. Document in CHANGELOG.md

---

**Ecosystem Health:** All libraries production-ready and actively maintained
**Coordination:** Centralized via this template repository
**Next Library:** vendor-connectors (in planning)

# Standard CI/CD Workflow for jbcom Python Libraries

**This is the canonical CI workflow deployed to all jbcom Python library repositories.**

## Deployment

This workflow is deployed from the jbcom management hub to:
- extended-data-types
- lifecyclelogging
- directed-inputs-class
- vendor-connectors

## Version

**Version:** 1.0.0
**Last Updated:** 2025-11-25

## Changes from Template

This workflow is MAINTAINED here and DEPLOYED to managed repositories. When you update this file:

1. Test changes in this repository first
2. Run validation: `python tools/validate_workflows.py`
3. Deploy to managed repos: `python tools/deploy_workflows.py standard-ci.yml`
4. Monitor CI results across ecosystem
5. Update version number and date above

## Workflow Features

- **Multi-version testing**: Python 3.10, 3.11, 3.12, 3.13
- **Type checking**: pyright
- **Linting**: ruff with pre-commit
- **Coverage**: pytest-cov with reporting
- **Auto-versioning**: CalVer (YYYY.MM.BUILD)
- **PyPI publishing**: Trusted publishing with attestations

## Customization Per Repository

Some repositories may need slight variations. Handle via:
- Environment variables in repository secrets
- Conditional steps based on repository context
- Repository-specific tox environments

## Deployment Instructions

See `../tools/README.md` for deployment procedures.

---

**DO NOT manually edit this file in managed repositories.** Changes should be made here and deployed via management tools.

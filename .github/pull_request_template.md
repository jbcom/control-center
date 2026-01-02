## Description
<!-- Describe your changes in detail -->

## Type of Change
<!-- Mark relevant items with an [x] -->
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update
- [ ] Refactoring (no functional changes)
- [ ] Performance improvement
- [ ] Test coverage improvement

## Testing
<!-- Describe the tests you ran and their results -->

### Test Coverage
```bash
# Run these commands and paste the output
go test -coverprofile=coverage.out ./...
go tool cover -func=coverage.out | grep total
```

**Coverage Results:**
- [ ] All tests pass
- [ ] Coverage is ≥70% for new/modified code
- [ ] No race conditions detected (`go test -race`)

### Manual Testing
- [ ] Tested locally
- [ ] Tested in Docker
- [ ] Tested in CI/CD

## Checklist
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)
<!-- Add screenshots to help explain your changes -->

## Related Issues
<!-- Link to related issues: Closes #123, Fixes #456 -->

Closes #

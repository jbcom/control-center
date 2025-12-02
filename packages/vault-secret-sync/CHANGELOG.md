# Changelog

All notable changes to vault-secret-sync will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Integration into jbcom monorepo with full CI/CD pipeline
- Multi-architecture Docker builds (linux/amd64, linux/arm64)
- SBOM and provenance attestation for Docker images
- Helm OCI artifact publishing to Docker Hub
- Comprehensive test suite with libsodium support

### Changed
- **OWNERSHIP TRANSITION**: This package is now maintained by jbcom as part of the jbcom-control-center monorepo
- Docker images now published to `docker.io/jbcom/vault-secret-sync`
- Helm charts published to `oci://docker.io/jbcom`

### Fixed
- Removed dead code: `countRegexMatches`, `countDeleteRegexMatches` (internal/sync/utils.go)
- Removed dead code: `updateSecret` (stores/gcp/gcp.go)
- Removed dead code: `tokenEnvTemplate` (stores/vault/vault.go)
- Fixed `context.Background()` usage in kube.go - now properly uses passed context
- Fixed error handling in server.go goroutine - errors are now logged
- Fixed `AnnotationOperations` to accept and use context parameter
- Fixed dangerous `os.Exit(1)` in goroutine - now uses proper logging
- Fixed duplicate `rand` import conflict in stores/github/github.go
- Fixed incorrect type reference in cmd/vss/main.go (`EventsConfig` → `EventServer`)
- Fixed `metrics.Start()` call in main.go (function doesn't return error)
- Fixed README typos ("syncronization" → "synchronization", "authoratative" → "authoritative")
- Fixed README copy-paste error in Suspended section (showed wrong YAML example)

---

## Ownership & Attribution

### Current Maintainer
- **Organization**: jbcom
- **Repository**: [jbcom/jbcom-control-center](https://github.com/jbcom/jbcom-control-center)
- **Package Path**: `packages/vault-secret-sync`

### Original Source
- **Author**: Robert Lestak
- **Repository**: [robertlestak/vault-secret-sync](https://github.com/robertlestak/vault-secret-sync)
- **License**: MIT

### Fork Rationale

**WHY**: The jbcom infrastructure requires robust secret synchronization from HashiCorp Vault to multiple cloud providers (AWS, GCP, Azure, Doppler). The original vault-secret-sync provides an excellent foundation, but we needed:
- Custom enhancements for Doppler integration
- AWS Identity Center (SSO) account discovery
- Tighter integration with our CI/CD and release processes
- Code quality improvements and dead code removal

**WHAT**: This fork includes all original functionality plus:
- Doppler secret store support
- AWS Identity Center dynamic account discovery
- Enhanced error handling and context propagation
- Comprehensive Helm charts for Kubernetes deployment

**WHERE**: Integrated as a Go package within the jbcom-control-center monorepo at `packages/vault-secret-sync`.

**HOW**: 
1. Forked from upstream at commit `<original-commit>`
2. Integrated into monorepo with proper CI/CD
3. Applied code quality fixes addressing all AI reviewer feedback
4. Enhanced with jbcom-specific features

**WHEN**: December 2025

### Contributing Back Upstream

Fixes and improvements in this fork that would benefit the broader community should be contributed back to the original repository. Each contribution should be:
- Isolated to a single concern
- Well-documented with clear reasoning
- Tested independently
- Submitted as a targeted PR with appropriate context

Candidates for upstream contribution:
- Dead code removal (utils.go, gcp.go, vault.go)
- Context propagation fixes (kube.go)
- Error handling improvements (server.go)
- Documentation fixes (README typos)

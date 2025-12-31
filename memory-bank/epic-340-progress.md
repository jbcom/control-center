# EPIC #340: Agentic Ecosystem Refactor Progress

This document tracks the progress of the architectural refactor outlined in issue #340.

## Phase 1: Documentation & Scoping (Control Center) - ✅ COMPLETE

- [x] Updated `docs/agentic-ecosystem.md` to be the canonical source of truth for the new architecture.
- [x] Updated `AGENTS.md` to remove redundant architectural information and link to the canonical docs.
- [x] Updated `README.md` to provide a high-level overview and link to the canonical docs.
- [x] This progress file has been created to track the next steps.

## Phase 2: Implement `vendor-connectors` Changes - 🟡 PENDING

**Repository**: [jbcom/python-vendor-connectors](https://github.com/jbcom/python-vendor-connectors)

- [ ] **Create Cursor Connector**: Port the TypeScript Cursor API client from `agentic-control/src/fleet/cursor-api.ts` to a new Python module in `vendor-connectors`.
- [ ] **Create Anthropic Connector**: Create a new Python module in `vendor-connectors` that wraps the `@anthropic-ai/claude-agent-sdk`.
- [ ] **CI/CD**: Ensure that the new connectors are included in the `vendor-connectors` PyPI package.

## Phase 3: Create `agentic-crew` Repository - 🟡 PENDING

**Repository**: New repository `jbcom/python-agentic-crew` to be created.

- [ ] **Create Repository**: Create the new repository under the `jbcom` organization.
- [ ] **Move CrewAI Code**: Move the CrewAI-specific code from `agentic-control/python/` to the new `agentic-crew` repository.
- [ ] **CI/CD**: Set up CI/CD for the new repository to publish the `agentic-crew` PyPI package.

## Phase 4: Refactor `agentic-control` - 🟡 PENDING

**Repository**: [jbcom/nodejs-agentic-control](https://github.com/jbcom/nodejs-agentic-control)

- [ ] **Define Provider Interface**: Create a formal provider interface in `agentic-control` that will be used to interact with the `vendor-connectors`.
- [ ] **Remove Vendor-Specific Code**: Remove `cursor-api.ts` and any direct usage of the Claude SDK from `agentic-control`.
- [ ] **Implement Provider Abstraction**: Implement the provider abstraction layer that uses the `vendor-connectors` package.
- [ ] **Define Agent Protocols**: Document the agent registration and agent-to-agent communication protocols.

## Phase 5: Integration & Final Documentation - 🟡 PENDING

- [ ] **Update READMEs**: Update the READMEs of all three repositories to reflect the final architecture.
- [ ] **Create Integration Guide**: Create a comprehensive integration guide that explains how to use the three repositories together.
- [ ] **Update Control Center Configs**: Update any sync configurations in `jbcom-control-center` to reflect the new repository structure.

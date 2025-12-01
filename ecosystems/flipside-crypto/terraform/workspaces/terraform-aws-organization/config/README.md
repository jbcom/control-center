# AWS Configuration

This directory contains AWS-specific configurations organized in a hierarchical structure that mirrors AWS Organizations:

## Directory Structure

- `organization/`: Top-level organization configuration
  - `config.yaml`: Organization settings and service principals
  - `policies/`: Organization-level policies
  - `access/`: Permission sets and policy templates
  - `root/`: Root-level accounts
  - `units/`: Organizational Units, each with their own subdirectory:
    - Each unit has a `unit.yaml` file and an `accounts/` directory containing account definitions

This hierarchical structure provides better organization, clearer separation of concerns, and more accurately mirrors the AWS Organizations structure.

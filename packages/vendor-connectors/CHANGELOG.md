# CHANGELOG

<!-- version list -->

## v202511.11.0 (2025-11-30)

### Documentation

- Align instructions with SemVer ([#263](https://github.com/jbcom/jbcom-control-center/pull/263),
  [`1d3d830`](https://github.com/jbcom/jbcom-control-center/commit/1d3d83033aaf2d0b16b7355559dbda208ee20dd7))

### Features

- Migrate remaining terraform helpers
  ([#264](https://github.com/jbcom/jbcom-control-center/pull/264),
  [`f52e41d`](https://github.com/jbcom/jbcom-control-center/commit/f52e41dad26a44b9f5a2ee2e59d02d4942c481ac))


## v202511.10.0 (2025-11-30)

### Documentation

- Update PR_PLAN with agent fleet assignments
  ([`80845b1`](https://github.com/jbcom/jbcom-control-center/commit/80845b1531f900a81786489ce77c030429d4c362))

- Update wiki and orchestration for architectural evolution
  ([`8ad2f99`](https://github.com/jbcom/jbcom-control-center/commit/8ad2f997f41dffb1910c07398a779d1d7c2a9302))

### Features

- Add python-terraform-bridge package
  ([#248](https://github.com/jbcom/jbcom-control-center/pull/248),
  [`2d3cd6f`](https://github.com/jbcom/jbcom-control-center/commit/2d3cd6f05502fe02c0a0178829d871a955ae6b35))

- Complete terraform-modules migration gaps - 100% feature parity
  ([#245](https://github.com/jbcom/jbcom-control-center/pull/245),
  [`e360209`](https://github.com/jbcom/jbcom-control-center/commit/e36020912358426fee9d02cca2091bef81230ced))


## v202511.9.0 (2025-11-29)

### Documentation

- Add FSC Control Center counterparty awareness
  ([#220](https://github.com/jbcom/jbcom-control-center/pull/220),
  [`a0e9ff9`](https://github.com/jbcom/jbcom-control-center/commit/a0e9ff96aefd947266753fb8e8f460463eb8dc8f))

- Update orchestration with completion status
  ([`f0737b5`](https://github.com/jbcom/jbcom-control-center/commit/f0737b52b44300f8ba7d376fc1a32da2ee7035de))

### Features

- Add AWS Secrets Manager create, update, delete operations
  ([#236](https://github.com/jbcom/jbcom-control-center/pull/236),
  [`76b8243`](https://github.com/jbcom/jbcom-control-center/commit/76b82433cc4ff8e2842e0ea2313fba4bfedbc19c))

- Add filtering and transformation to Google user/group listing
  ([#241](https://github.com/jbcom/jbcom-control-center/pull/241),
  [`33feb1c`](https://github.com/jbcom/jbcom-control-center/commit/33feb1ca1ba61df049879eaeb75e46b112542560))

- Add Slack usergroup and conversation listing
  ([#237](https://github.com/jbcom/jbcom-control-center/pull/237),
  [`ef1aea7`](https://github.com/jbcom/jbcom-control-center/commit/ef1aea7eb469df998e9d0fe93722b6af0af8267b))

- Add terraform-aligned Google constants and idempotent create methods
  ([#244](https://github.com/jbcom/jbcom-control-center/pull/244),
  [`66d5457`](https://github.com/jbcom/jbcom-control-center/commit/66d545725c9552190b03f6cf14765e6fc9b1547c))

- Add Vault AWS IAM role helpers ([#239](https://github.com/jbcom/jbcom-control-center/pull/239),
  [`bc7c8aa`](https://github.com/jbcom/jbcom-control-center/commit/bc7c8aa2c9b27dac2748e038ceff34a4b0f5572d))


## v202511.8.0 (2025-11-29)

### Features

- Add cloud_params module with API parameter utilities
  ([#228](https://github.com/jbcom/jbcom-control-center/pull/228),
  [`a6cee10`](https://github.com/jbcom/jbcom-control-center/commit/a6cee103952d0ef49333633cea5ad86a689d647f))
- Extend Vault connector with AWS IAM role helpers migrated from terraform-modules
  ([#233](https://github.com/jbcom/jbcom-control-center/issues/233))


## v202511.7.0 (2025-11-29)

### Features

- Add FSC fleet coordination support
  ([`7a046b6`](https://github.com/jbcom/jbcom-control-center/commit/7a046b6578cd2216542e893d61ecd501d8305a8c))

- Add list_secrets to AWS and Vault connectors
  ([#223](https://github.com/jbcom/jbcom-control-center/pull/223),
  [`755ce0d`](https://github.com/jbcom/jbcom-control-center/commit/755ce0dab6e1ffe5c133495cc0d41d9717e43b6e))


## v202511.6.2 (2025-11-28)

### Features

- Add Vault/AWS secret listing helpers with prefix filtering and path normalization
  ([#202](https://github.com/FlipsideCrypto/terraform-modules/issues/202))


## v202511.6.1 (2025-11-28)

### Bug Fixes

- Use correct PYPI_TOKEN secret for PyPI publishing
  ([`093feb1`](https://github.com/jbcom/jbcom-control-center/commit/093feb1c87add9d7890fa9dd84a02ea7d2a6d110))


## v202511.6.0 (2025-11-28)

### Code Style

- Fix formatting
  ([`5069b71`](https://github.com/jbcom/jbcom-control-center/commit/5069b71c56a2a20a94d2fdecc33b53d35fba229d))

### Features

- Trigger release with PYPI_API_TOKEN configured
  ([`cab7c2c`](https://github.com/jbcom/jbcom-control-center/commit/cab7c2ca43d6286f521e2e47ecd6911f6bf106df))


## v202511.5.0 (2025-11-28)

### Features

- Force new release to sync with PyPI
  ([`a42f125`](https://github.com/jbcom/jbcom-control-center/commit/a42f125d42c449ecec5b11e89ed8ac632353d043))


## v202511.4.1 (2025-11-28)

### Bug Fixes

- Disable GitHub release creation for vendor-connectors
  ([`f28a25b`](https://github.com/jbcom/jbcom-control-center/commit/f28a25b541f36c2cc0a35f716d57254c34f09a77))


## v202511.4.0 (2025-11-28)

### Features

- Trigger vendor-connectors 202511.4.0 release
  ([`5618c52`](https://github.com/jbcom/jbcom-control-center/commit/5618c5258d6b08b29ac2b2681b8a179710a56115))


## v202511.3.0 (2025-11-28)

- Initial Release

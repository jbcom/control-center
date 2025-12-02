# vault-secret-sync (jbcom fork)

Real-time secret synchronization from OpenBao/Vault to multiple destinations.

## Architecture

```
jbcom-control-center (monorepo)
└── ecosystems/jbcom/vault-secret-sync/
    └── [Go source code]
            ↓
    [CI builds & publishes]
            ↓
    Docker Hub: docker.io/jbcom/vault-secret-sync
    Helm OCI:   oci://docker.io/jbcom/vault-secret-sync
            ↓
    [Syncs to fork]
            ↓
    github.com/jbcom/vault-secret-sync
            ↓
    [Future: upstream contributions]
            ↓
    github.com/robertlestak/vault-secret-sync
```

## Destinations Supported

| Destination | Status | Description |
|-------------|--------|-------------|
| AWS Secrets Manager | ✅ Upstream | Sync to AWS SM |
| GitHub Org Secrets | ✅ Upstream | Sync to GitHub |
| Doppler | ✅ jbcom fork | Sync to Doppler projects |
| AWS Identity Center | ✅ jbcom fork | Dynamic account discovery |

## Publishing

**Docker Image**: `docker.io/jbcom/vault-secret-sync`
```bash
docker pull jbcom/vault-secret-sync:latest
docker pull jbcom/vault-secret-sync:v0.1.0
```

**Helm Chart** (OCI):
```bash
helm pull oci://docker.io/jbcom/vault-secret-sync --version 0.1.0
helm install vault-secret-sync oci://docker.io/jbcom/vault-secret-sync
```

## Development

Code lives in this monorepo directory. Changes trigger:
1. CI builds Docker image + Helm chart
2. Publishes to Docker Hub
3. Syncs to jbcom/vault-secret-sync fork

## Upstream Contributions

When contributing back to upstream:
1. Create PR in jbcom/vault-secret-sync fork
2. Test with FSC infrastructure
3. Open upstream PR to robertlestak/vault-secret-sync
4. Reference jbcom fork PR for context

## Related

- [Upstream](https://github.com/robertlestak/vault-secret-sync)
- [Fork](https://github.com/jbcom/vault-secret-sync)
- [Docker Hub](https://hub.docker.com/r/jbcom/vault-secret-sync)

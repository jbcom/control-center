package sync

import (
	"context"
	"fmt"

	"github.com/robertlestak/vault-secret-sync/internal/backend"
	"github.com/robertlestak/vault-secret-sync/internal/transforms"
	log "github.com/sirupsen/logrus"
)

// shouldFilterSecret checks if the secret should be filtered based on configuration
func shouldFilterSecret(j SyncJob, sourcePath, destPath string) bool {
	l := log.WithFields(log.Fields{
		"action":     "shouldFilterSecret",
		"sourcePath": sourcePath,
		"destPath":   destPath,
	})
	if j.SyncConfig.Spec.Filters != nil && transforms.ShouldFilterString(j.SyncConfig, sourcePath) {
		l.Debug("filtering secret")
		return true
	}
	return false
}

// shouldDryRun checks if the sync should be a dry run
func shouldDryRun(ctx context.Context, j SyncJob, dest SyncClient, sourcePath, destPath string) bool {
	l := log.WithFields(log.Fields{
		"action":     "shouldDryRun",
		"sourcePath": sourcePath,
		"destPath":   destPath,
	})
	if j.SyncConfig.Spec.Suspend != nil && *j.SyncConfig.Spec.Suspend {
		l.Info("sync suspended")
		if err := backend.SetSyncStatus(ctx, j.SyncConfig, backend.SyncStatusSuspended); err != nil {
			l.WithError(err).Error("failed to set sync status")
		}
		if err := backend.WriteEvent(
			ctx,
			j.SyncConfig.Namespace,
			j.SyncConfig.Name,
			"Normal",
			string(backend.SyncStatusSuspended),
			fmt.Sprintf("sync suspended: %s to %s: %s", sourcePath, dest.Driver(), destPath),
		); err != nil {
			l.WithError(err).Error("failed to write event")
		}
		return true
	}
	if j.SyncConfig.Spec.DryRun != nil && *j.SyncConfig.Spec.DryRun {
		l.Info("dry run")
		if err := backend.SetSyncStatus(ctx, j.SyncConfig, backend.SyncStatusDryRun); err != nil {
			l.WithError(err).Error("failed to set sync status")
		}
		if err := backend.WriteEvent(
			ctx,
			j.SyncConfig.Namespace,
			j.SyncConfig.Name,
			"Normal",
			string(backend.SyncStatusDryRun),
			fmt.Sprintf("dry run: synced %s to %s: %s", sourcePath, dest.Driver(), destPath),
		); err != nil {
			l.WithError(err).Error("failed to write event")
		}
		return true
	}
	return false
}

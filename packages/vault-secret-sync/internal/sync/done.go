package sync

import (
	"context"
	"fmt"
	"time"

	"github.com/robertlestak/vault-secret-sync/api/v1alpha1"
	"github.com/robertlestak/vault-secret-sync/internal/backend"
	"github.com/robertlestak/vault-secret-sync/internal/metrics"
	"github.com/robertlestak/vault-secret-sync/internal/notifications"
	log "github.com/sirupsen/logrus"
)

// handleSyncError handles errors during the sync process
func handleSyncError(ctx context.Context, err error, j SyncJob, startTime time.Time) error {
	l := log.WithFields(log.Fields{"action": "handleSyncError", "error": err})
	l.Error("sync operation failed")

	namespace, name := j.SyncConfig.Namespace, j.SyncConfig.Name
	observeWorkerError(namespace, name, startTime)
	if statusErr := backend.SetSyncStatus(ctx, j.SyncConfig, backend.SyncStatusFailed); statusErr != nil {
		l.WithError(statusErr).Error("failed to set sync status")
	}
	if notifyErr := notifications.Trigger(ctx, v1alpha1.NotificationMessage{
		Message:         fmt.Sprintf("error syncing: %s", err),
		Event:           v1alpha1.NotificationEventSyncFailure,
		VaultSecretSync: j.SyncConfig,
	}); notifyErr != nil {
		l.WithError(notifyErr).Error("failed to send notification")
	}
	return err
}

// handleSyncSuccess handles successful sync completion
func handleSyncSuccess(ctx context.Context, j SyncJob, startTime time.Time) error {
	l := log.WithFields(log.Fields{"action": "handleSyncSuccess"})
	l.Trace("end")

	namespace, name := j.SyncConfig.Namespace, j.SyncConfig.Name
	observeWorkerSuccess(namespace, name, startTime)
	if statusErr := backend.SetSyncStatus(ctx, j.SyncConfig, backend.SyncStatusSuccess); statusErr != nil {
		l.WithError(statusErr).Error("failed to set sync status")
	}
	if notifyErr := notifications.Trigger(ctx, v1alpha1.NotificationMessage{
		Message:         "sync success",
		Event:           v1alpha1.NotificationEventSyncSuccess,
		VaultSecretSync: j.SyncConfig,
	}); notifyErr != nil {
		l.WithError(notifyErr).Error("failed to send notification")
	}
	return nil
}

// observeWorkerSuccess logs metrics for successful sync
func observeWorkerSuccess(namespace, name string, startTime time.Time) {
	metrics.SyncDuration.WithLabelValues(namespace, name).Observe(time.Since(startTime).Seconds())
	metrics.ActiveSyncs.WithLabelValues(namespace, name).Dec()
	metrics.SyncStatus.WithLabelValues(namespace, name).Set(1)
}

// observeWorkerError logs metrics for failed sync
func observeWorkerError(namespace, name string, startTime time.Time) {
	metrics.SyncDuration.WithLabelValues(namespace, name).Observe(time.Since(startTime).Seconds())
	metrics.ActiveSyncs.WithLabelValues(namespace, name).Dec()
	metrics.SyncStatus.WithLabelValues(namespace, name).Set(0)
	metrics.SyncErrors.WithLabelValues(namespace, name).Inc()
}

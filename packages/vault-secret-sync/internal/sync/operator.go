package sync

import (
	"context"

	"github.com/robertlestak/vault-secret-sync/internal/backend"
	"github.com/robertlestak/vault-secret-sync/internal/metrics"
	log "github.com/sirupsen/logrus"
)

func Operator(ctx context.Context, backendParams map[string]any, workerPoolSize, numSubscriptions int) {
	l := log.WithFields(log.Fields{
		"action": "Operator",
	})
	l.Info("starting operator")

	metrics.RegisterServiceHealth("operator", metrics.ServiceHealthStatusOK)
	if err := backend.InitBackend(ctx, backendParams); err != nil {
		l.Error(err)
		return
	}
	// start the event queue with error handling
	go func() {
		if err := EventProcessor(ctx, workerPoolSize, numSubscriptions); err != nil {
			l.WithError(err).Error("event processor failed")
			metrics.RegisterServiceHealth("operator", metrics.ServiceHealthStatusCritical)
		}
	}()
	// wait for context to be done
	<-ctx.Done()
	metrics.RegisterServiceHealth("operator", metrics.ServiceHealthStatusCritical)
	l.Info("stopping operator")
}

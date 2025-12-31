#!/bin/sh
# Control Center Docker/GitHub Action entrypoint
# Converts CONTROL_CENTER_* env vars to CLI arguments

set -e

# Build argument list
ARGS=""

# Command is first positional arg (required)
if [ -n "$1" ]; then
    ARGS="$1"
    shift
else
    # If no command, show help
    exec /usr/local/bin/control-center --help
fi

# Add repo flag if set
if [ -n "$CONTROL_CENTER_REPO" ]; then
    ARGS="$ARGS --repo $CONTROL_CENTER_REPO"
fi

# Add PR flag if set
if [ -n "$CONTROL_CENTER_PR" ]; then
    ARGS="$ARGS --pr $CONTROL_CENTER_PR"
fi

# Add run-id flag if set
if [ -n "$CONTROL_CENTER_RUN_ID" ]; then
    ARGS="$ARGS --run-id $CONTROL_CENTER_RUN_ID"
fi

# Add target flag for gardener
if [ -n "$CONTROL_CENTER_TARGET" ]; then
    ARGS="$ARGS --target $CONTROL_CENTER_TARGET"
fi

# Add decompose flag for gardener
if [ "$CONTROL_CENTER_DECOMPOSE" = "true" ]; then
    ARGS="$ARGS --decompose"
fi

# Add backlog flag for gardener
if [ "$CONTROL_CENTER_BACKLOG" = "false" ]; then
    ARGS="$ARGS --backlog=false"
fi

# Add dry-run if set
if [ "$CONTROL_CENTER_DRY_RUN" = "true" ]; then
    ARGS="$ARGS --dry-run"
fi

# Add log level
if [ -n "$CONTROL_CENTER_LOG_LEVEL" ]; then
    ARGS="$ARGS --log-level $CONTROL_CENTER_LOG_LEVEL"
fi

# Pass any additional args from command line
ARGS="$ARGS $*"

# Execute
echo "🚀 control-center $ARGS"
exec /usr/local/bin/control-center $ARGS

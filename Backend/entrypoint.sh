#!/bin/sh
# ─────────────────────────────────────────────────────────────
# Entrypoint script — fixes volume permissions, then drops to appuser.
#
# Problem: Docker named volumes mount as root, so the non-root
#          appuser cannot write to /tmp/cv_uploads.
# Solution: This script runs as root, fixes ownership, then
#           executes the CMD as appuser via `exec gosu`.
# ─────────────────────────────────────────────────────────────

set -e

# Fix ownership of the upload directory (needed for Docker volumes)
chown -R appuser:appuser /tmp/cv_uploads

# Drop privileges and exec the CMD (passed as arguments to this script)
exec su appuser -s /bin/sh -c "exec $*" -- "$@"

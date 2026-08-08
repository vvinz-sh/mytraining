#!/bin/bash
# send-logger-events.sh
# Usage : ./send-logger-events.sh <count> <tag>
COUNT="$1"
TAG="${2:-tp-pq-fb}"

for ((i=1; i<=COUNT; i++)); do
            echo "SEQ-${TAG}-${i}"
    done | logger -t "$TAG"

    echo "=== Envoyé : $COUNT lignes via logger (tag: $TAG) ==="

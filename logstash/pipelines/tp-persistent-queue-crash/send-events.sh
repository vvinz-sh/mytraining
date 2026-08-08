#!/bin/bash
# send-events.sh
# Usage : ./send-events.sh <host> <port> <count> <rate_par_seconde> [batch_size]
HOST="$1"
PORT="$2"
COUNT="$3"
RATE="$4"
BATCH="${5:-50}"

DELAY_BATCH=$(echo "scale=6; $BATCH/$RATE" | bc)

exec 3<>"/dev/tcp/$HOST/$PORT"
for ((i=1; i<=COUNT; i++)); do
    echo "EVT-${i}-${EPOCHREALTIME}" >&3
    if (( i % BATCH == 0 )); then
        sleep "$DELAY_BATCH"
    fi
done
exec 3<&-
exec 3>&-
echo "=== Envoyé : $COUNT events vers $HOST:$PORT (débit visé : $RATE/s, lot de $BATCH) ==="

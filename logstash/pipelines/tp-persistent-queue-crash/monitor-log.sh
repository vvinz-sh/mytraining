#!/bin/bash
# monitor-log.sh
PIPELINE_ID="beats-tls"
LOG_FILE="/tmp/tp-pq-crash-monitoring.log"

> "$LOG_FILE"
while true; do
    TS=$(date +%H:%M:%S.%3N)
    STATS=$(curl -s localhost:9600/_node/stats/pipelines | jq -c ".pipelines.\"$PIPELINE_ID\" | {queue, input_tp: .flow.input_throughput.current, output_tp: .flow.output_throughput.current, backpressure: .flow.queue_backpressure.current, events_in: .events.in}")
    echo "$TS $STATS" | tee -a "$LOG_FILE"
    sleep 1
done

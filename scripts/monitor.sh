#!/bin/bash
# Simple monitoring script for Automated AI Assessment (AAA)
# Usage: ./scripts/monitor.sh [interval_seconds]

set -e

INTERVAL=${1:-30}  # Default 30 seconds
LOG_FILE="logs/monitor.log"
ALERT_THRESHOLD=3  # Alert after 3 consecutive failures

# Create logs directory if it doesn't exist
mkdir -p logs

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
consecutive_failures=0

echo "🔍 Starting Automated AI Assessment (AAA) monitoring (interval: ${INTERVAL}s)"
echo "📝 Logs will be written to: ${LOG_FILE}"
echo "🚨 Alert threshold: ${ALERT_THRESHOLD} consecutive failures"
echo "Press Ctrl+C to stop"
echo ""

# Function to send alert (customize as needed)
send_alert() {
    local message="$1"
    echo "$(date): ALERT - $message" >> "$LOG_FILE"
    echo -e "${RED}🚨 ALERT: $message${NC}"
    
    # Add your alerting mechanism here:
    # - Send email
    # - Post to Slack
    # - Send to monitoring system
    # - etc.
}

# Function to log message
log_message() {
    local level="$1"
    local message="$2"
    echo "$(date): [$level] $message" >> "$LOG_FILE"
}

# Main monitoring loop
while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    # Run health check
    if python3 scripts/health_check.py --quiet; then
        # Health check passed
        consecutive_failures=0
        echo -e "${GREEN}✅ $timestamp - All services healthy${NC}"
        log_message "INFO" "Health check passed"
    else
        # Health check failed
        consecutive_failures=$((consecutive_failures + 1))
        echo -e "${RED}❌ $timestamp - Health check failed (failure #$consecutive_failures)${NC}"
        log_message "ERROR" "Health check failed (consecutive failures: $consecutive_failures)"
        
        # Get detailed status for logging
        python3 scripts/health_check.py --json >> "$LOG_FILE" 2>&1
        
        # Send alert if threshold reached
        if [ $consecutive_failures -ge $ALERT_THRESHOLD ]; then
            send_alert "Automated AI Assessment (AAA) services unhealthy for $consecutive_failures consecutive checks"
        fi
    fi
    
    sleep "$INTERVAL"
done
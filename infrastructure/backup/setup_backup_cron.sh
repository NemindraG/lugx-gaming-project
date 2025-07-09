#!/bin/bash

# Setup Automated Backup Cron Jobs for Lugx Gaming Platform
# This script configures cron jobs for regular database backups

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Setting up automated backup cron jobs for Lugx Gaming Platform${NC}"

# Get the absolute path to the backup manager
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_MANAGER="$SCRIPT_DIR/backup_manager.py"

# Check if backup manager exists
if [[ ! -f "$BACKUP_MANAGER" ]]; then
    echo -e "${RED}Error: backup_manager.py not found at $BACKUP_MANAGER${NC}"
    exit 1
fi

# Create logs directory
LOGS_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOGS_DIR"

# Create backup configuration if it doesn't exist
CONFIG_FILE="$SCRIPT_DIR/backup_config.json"
if [[ ! -f "$CONFIG_FILE" ]]; then
    echo -e "${YELLOW}Creating default backup configuration...${NC}"
    cat > "$CONFIG_FILE" << EOF
{
    "backup_root": "/var/backups/lugx-gaming",
    "retention_days": 30,
    "compression": true,
    "encryption": false,
    "notification_webhook": null,
    "databases": {
        "postgres": {
            "game_service": {
                "host": "localhost",
                "port": 5432,
                "database": "lugx_games",
                "user": "game_service",
                "password": "game_secure_password_2024"
            },
            "order_service": {
                "host": "localhost",
                "port": 5433,
                "database": "lugx_orders",
                "user": "order_service",
                "password": "order_secure_password_2024"
            }
        },
        "clickhouse": {
            "analytics": {
                "host": "localhost",
                "port": 8123,
                "database": "lugx_analytics",
                "user": "analytics_service",
                "password": "analytics_secure_password_2024"
            }
        },
        "redis": {
            "cache": {
                "host": "localhost",
                "port": 6379,
                "password": "redis_secure_password_2024"
            }
        }
    }
}
EOF
fi

# Create backup script wrapper
BACKUP_SCRIPT="$SCRIPT_DIR/run_backup.sh"
cat > "$BACKUP_SCRIPT" << EOF
#!/bin/bash
# Automated backup script for Lugx Gaming Platform

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Change to script directory
cd "$SCRIPT_DIR"

# Run backup with logging
echo "Starting backup at \$(date)" >> "$LOGS_DIR/backup.log"
python3 "$BACKUP_MANAGER" backup --config "$CONFIG_FILE" >> "$LOGS_DIR/backup.log" 2>&1

# Check exit code
if [ \$? -eq 0 ]; then
    echo "Backup completed successfully at \$(date)" >> "$LOGS_DIR/backup.log"
else
    echo "Backup failed at \$(date)" >> "$LOGS_DIR/backup.log"
fi

# Rotate log files (keep last 7 days)
find "$LOGS_DIR" -name "backup.log.*" -mtime +7 -delete
EOF

chmod +x "$BACKUP_SCRIPT"

# Create health check script
HEALTH_SCRIPT="$SCRIPT_DIR/check_backup_health.sh"
cat > "$HEALTH_SCRIPT" << EOF
#!/bin/bash
# Health check script for backup system

# Set up environment
export PATH="/usr/local/bin:/usr/bin:/bin"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Change to script directory
cd "$SCRIPT_DIR"

# Run health check
python3 "$BACKUP_MANAGER" health --config "$CONFIG_FILE" >> "$LOGS_DIR/health.log" 2>&1
EOF

chmod +x "$HEALTH_SCRIPT"

# Add cron jobs
echo -e "${GREEN}Adding cron jobs...${NC}"

# Create temporary cron file
TEMP_CRON=$(mktemp)

# Get existing cron jobs (excluding our jobs)
crontab -l 2>/dev/null | grep -v "# Lugx Gaming Backup" > "$TEMP_CRON" || true

# Add new cron jobs
cat >> "$TEMP_CRON" << EOF

# Lugx Gaming Backup Jobs
# Full backup every day at 2 AM
0 2 * * * $BACKUP_SCRIPT

# Health check every 4 hours
0 */4 * * * $HEALTH_SCRIPT

# Weekly cleanup (Sundays at 3 AM)
0 3 * * 0 find /var/backups/lugx-gaming -type f -mtime +30 -delete

EOF

# Install new cron jobs
crontab "$TEMP_CRON"
rm "$TEMP_CRON"

echo -e "${GREEN}Cron jobs installed successfully!${NC}"

# Display current cron jobs
echo -e "${YELLOW}Current cron jobs:${NC}"
crontab -l | grep -A 10 "Lugx Gaming Backup"

# Create backup directory structure
echo -e "${GREEN}Creating backup directory structure...${NC}"
sudo mkdir -p /var/backups/lugx-gaming/{postgres,clickhouse,redis}
sudo chown -R $(whoami):$(whoami) /var/backups/lugx-gaming

# Test backup system
echo -e "${GREEN}Testing backup system...${NC}"
python3 "$BACKUP_MANAGER" health --config "$CONFIG_FILE"

echo -e "${GREEN}Setup complete!${NC}"
echo -e "${YELLOW}Backup schedule:${NC}"
echo "  • Full backup: Daily at 2:00 AM"
echo "  • Health check: Every 4 hours"
echo "  • Cleanup: Weekly on Sundays at 3:00 AM"
echo "  • Retention: 30 days"
echo ""
echo -e "${YELLOW}Log files:${NC}"
echo "  • Backup logs: $LOGS_DIR/backup.log"
echo "  • Health logs: $LOGS_DIR/health.log"
echo ""
echo -e "${YELLOW}Manual commands:${NC}"
echo "  • Full backup: python3 $BACKUP_MANAGER backup"
echo "  • Health check: python3 $BACKUP_MANAGER health"
echo "  • List backups: python3 $BACKUP_MANAGER list"
#!/usr/bin/env python3
"""
Production Backup Manager
Comprehensive backup solution for all Lugx Gaming databases.
"""

import asyncio
import json
import logging
import os
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
import tarfile
import gzip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BackupManager:
    """
    Production-grade backup manager for PostgreSQL, ClickHouse, and Redis.
    Supports automated backups, retention policies, and disaster recovery.
    """
    
    def __init__(self, config_path: str = "backup_config.json"):
        self.config = self._load_config(config_path)
        self.backup_root = Path(self.config.get('backup_root', '/var/backups/lugx-gaming'))
        self.backup_root.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each service
        for service in ['postgres', 'clickhouse', 'redis']:
            (self.backup_root / service).mkdir(exist_ok=True)
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load backup configuration."""
        default_config = {
            "backup_root": "/var/backups/lugx-gaming",
            "retention_days": 30,
            "compression": True,
            "encryption": False,
            "notification_webhook": None,
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
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
                # Merge with defaults
                default_config.update(config)
        
        return default_config
    
    async def backup_postgres(self, service_name: str) -> bool:
        """Backup PostgreSQL database."""
        try:
            db_config = self.config['databases']['postgres'][service_name]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_root / 'postgres' / f"{service_name}_{timestamp}.sql"
            
            # Create pg_dump command
            cmd = [
                'pg_dump',
                '-h', db_config['host'],
                '-p', str(db_config['port']),
                '-U', db_config['user'],
                '-d', db_config['database'],
                '--verbose',
                '--no-password',
                '--format=custom',
                '--compress=9',
                '--file', str(backup_file)
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            # Execute backup
            logger.info(f"Starting PostgreSQL backup for {service_name}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL backup completed: {backup_file}")
                
                # Compress if enabled
                if self.config.get('compression', True):
                    await self._compress_file(backup_file)
                
                return True
            else:
                logger.error(f"PostgreSQL backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL backup error: {e}")
            return False
    
    async def backup_clickhouse(self, service_name: str) -> bool:
        """Backup ClickHouse database."""
        try:
            db_config = self.config['databases']['clickhouse'][service_name]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_root / 'clickhouse' / f"{service_name}_{timestamp}.sql"
            
            # Create clickhouse-client command for backup
            cmd = [
                'clickhouse-client',
                '--host', db_config['host'],
                '--port', str(db_config['port']),
                '--user', db_config['user'],
                '--password', db_config['password'],
                '--database', db_config['database'],
                '--query', f"BACKUP DATABASE {db_config['database']} TO Disk('default', '{backup_file}')"
            ]
            
            logger.info(f"Starting ClickHouse backup for {service_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"ClickHouse backup completed: {backup_file}")
                
                # Compress if enabled
                if self.config.get('compression', True):
                    await self._compress_file(backup_file)
                
                return True
            else:
                logger.error(f"ClickHouse backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"ClickHouse backup error: {e}")
            return False
    
    async def backup_redis(self, service_name: str) -> bool:
        """Backup Redis database."""
        try:
            db_config = self.config['databases']['redis'][service_name]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_root / 'redis' / f"{service_name}_{timestamp}.rdb"
            
            # Create redis-cli command for backup
            cmd = [
                'redis-cli',
                '-h', db_config['host'],
                '-p', str(db_config['port']),
                '-a', db_config['password'],
                '--rdb', str(backup_file)
            ]
            
            logger.info(f"Starting Redis backup for {service_name}")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"Redis backup completed: {backup_file}")
                
                # Compress if enabled
                if self.config.get('compression', True):
                    await self._compress_file(backup_file)
                
                return True
            else:
                logger.error(f"Redis backup failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Redis backup error: {e}")
            return False
    
    async def backup_all(self) -> Dict[str, bool]:
        """Backup all databases."""
        logger.info("Starting full backup of all databases")
        results = {}
        
        # Backup PostgreSQL databases
        for service_name in self.config['databases']['postgres']:
            results[f"postgres_{service_name}"] = await self.backup_postgres(service_name)
        
        # Backup ClickHouse databases
        for service_name in self.config['databases']['clickhouse']:
            results[f"clickhouse_{service_name}"] = await self.backup_clickhouse(service_name)
        
        # Backup Redis databases
        for service_name in self.config['databases']['redis']:
            results[f"redis_{service_name}"] = await self.backup_redis(service_name)
        
        # Send notification
        await self._send_notification(results)
        
        # Clean up old backups
        await self._cleanup_old_backups()
        
        return results
    
    async def restore_postgres(self, service_name: str, backup_file: str) -> bool:
        """Restore PostgreSQL database from backup."""
        try:
            db_config = self.config['databases']['postgres'][service_name]
            backup_path = Path(backup_file)
            
            if not backup_path.exists():
                # Try to find in backup directory
                backup_path = self.backup_root / 'postgres' / backup_file
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_file}")
                return False
            
            # Decompress if needed
            if backup_path.suffix == '.gz':
                decompressed_file = backup_path.with_suffix('')
                await self._decompress_file(backup_path, decompressed_file)
                backup_path = decompressed_file
            
            # Create pg_restore command
            cmd = [
                'pg_restore',
                '-h', db_config['host'],
                '-p', str(db_config['port']),
                '-U', db_config['user'],
                '-d', db_config['database'],
                '--verbose',
                '--no-password',
                '--clean',
                '--if-exists',
                str(backup_path)
            ]
            
            # Set environment variables
            env = os.environ.copy()
            env['PGPASSWORD'] = db_config['password']
            
            logger.info(f"Starting PostgreSQL restore for {service_name}")
            result = subprocess.run(cmd, env=env, capture_output=True, text=True)
            
            if result.returncode == 0:
                logger.info(f"PostgreSQL restore completed for {service_name}")
                return True
            else:
                logger.error(f"PostgreSQL restore failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"PostgreSQL restore error: {e}")
            return False
    
    async def list_backups(self, service_type: str = None) -> Dict[str, List[str]]:
        """List available backups."""
        backups = {}
        
        if service_type is None:
            service_types = ['postgres', 'clickhouse', 'redis']
        else:
            service_types = [service_type]
        
        for svc_type in service_types:
            backup_dir = self.backup_root / svc_type
            if backup_dir.exists():
                backups[svc_type] = sorted([
                    f.name for f in backup_dir.iterdir() 
                    if f.is_file() and not f.name.startswith('.')
                ], reverse=True)
            else:
                backups[svc_type] = []
        
        return backups
    
    async def get_backup_info(self, backup_file: str) -> Dict[str, Any]:
        """Get information about a backup file."""
        backup_path = Path(backup_file)
        
        if not backup_path.exists():
            # Try to find in backup directories
            for service_type in ['postgres', 'clickhouse', 'redis']:
                test_path = self.backup_root / service_type / backup_file
                if test_path.exists():
                    backup_path = test_path
                    break
        
        if not backup_path.exists():
            return {}
        
        stat = backup_path.stat()
        return {
            'filename': backup_path.name,
            'size': stat.st_size,
            'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
            'compressed': backup_path.suffix == '.gz'
        }
    
    async def _compress_file(self, file_path: Path) -> Path:
        """Compress a backup file."""
        compressed_path = file_path.with_suffix(file_path.suffix + '.gz')
        
        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # Remove original file
        file_path.unlink()
        
        logger.info(f"Compressed backup: {compressed_path}")
        return compressed_path
    
    async def _decompress_file(self, compressed_path: Path, output_path: Path):
        """Decompress a backup file."""
        with gzip.open(compressed_path, 'rb') as f_in:
            with open(output_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        logger.info(f"Decompressed backup: {output_path}")
    
    async def _cleanup_old_backups(self):
        """Remove old backups based on retention policy."""
        retention_days = self.config.get('retention_days', 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for service_type in ['postgres', 'clickhouse', 'redis']:
            backup_dir = self.backup_root / service_type
            if not backup_dir.exists():
                continue
            
            for backup_file in backup_dir.iterdir():
                if backup_file.is_file():
                    file_date = datetime.fromtimestamp(backup_file.stat().st_mtime)
                    if file_date < cutoff_date:
                        backup_file.unlink()
                        logger.info(f"Removed old backup: {backup_file}")
    
    async def _send_notification(self, results: Dict[str, bool]):
        """Send backup notification."""
        webhook_url = self.config.get('notification_webhook')
        if not webhook_url:
            return
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        message = {
            'timestamp': datetime.now().isoformat(),
            'status': 'success' if success_count == total_count else 'partial_failure',
            'total_backups': total_count,
            'successful_backups': success_count,
            'failed_backups': total_count - success_count,
            'results': results
        }
        
        try:
            # Send webhook notification (implement based on your notification system)
            logger.info(f"Backup notification: {message}")
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Check backup system health."""
        health = {
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'backup_root': str(self.backup_root),
            'backup_root_exists': self.backup_root.exists(),
            'services': {}
        }
        
        # Check each service
        for service_type, services in self.config['databases'].items():
            health['services'][service_type] = {}
            
            for service_name, config in services.items():
                try:
                    # Test connection (simplified)
                    if service_type == 'postgres':
                        cmd = ['pg_isready', '-h', config['host'], '-p', str(config['port'])]
                    elif service_type == 'clickhouse':
                        cmd = ['clickhouse-client', '--host', config['host'], '--port', str(config['port']), '--query', 'SELECT 1']
                    elif service_type == 'redis':
                        cmd = ['redis-cli', '-h', config['host'], '-p', str(config['port']), 'ping']
                    
                    result = subprocess.run(cmd, capture_output=True, timeout=10)
                    health['services'][service_type][service_name] = {
                        'status': 'healthy' if result.returncode == 0 else 'unhealthy',
                        'last_backup': await self._get_last_backup_time(service_type, service_name)
                    }
                    
                except Exception as e:
                    health['services'][service_type][service_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
        
        return health
    
    async def _get_last_backup_time(self, service_type: str, service_name: str) -> Optional[str]:
        """Get the timestamp of the last backup for a service."""
        backup_dir = self.backup_root / service_type
        if not backup_dir.exists():
            return None
        
        # Find the most recent backup file for this service
        backup_files = [
            f for f in backup_dir.iterdir()
            if f.is_file() and f.name.startswith(service_name)
        ]
        
        if not backup_files:
            return None
        
        latest_file = max(backup_files, key=lambda f: f.stat().st_mtime)
        return datetime.fromtimestamp(latest_file.stat().st_mtime).isoformat()


# CLI interface
async def main():
    """Command-line interface for backup manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Lugx Gaming Backup Manager')
    parser.add_argument('command', choices=['backup', 'restore', 'list', 'health', 'info'])
    parser.add_argument('--service', help='Service name (postgres, clickhouse, redis)')
    parser.add_argument('--name', help='Specific service name')
    parser.add_argument('--file', help='Backup file for restore/info')
    parser.add_argument('--config', default='backup_config.json', help='Config file path')
    
    args = parser.parse_args()
    
    backup_manager = BackupManager(args.config)
    
    if args.command == 'backup':
        if args.service and args.name:
            if args.service == 'postgres':
                result = await backup_manager.backup_postgres(args.name)
            elif args.service == 'clickhouse':
                result = await backup_manager.backup_clickhouse(args.name)
            elif args.service == 'redis':
                result = await backup_manager.backup_redis(args.name)
            print(f"Backup {'successful' if result else 'failed'}")
        else:
            results = await backup_manager.backup_all()
            print(f"Backup results: {results}")
    
    elif args.command == 'restore':
        if args.service == 'postgres' and args.name and args.file:
            result = await backup_manager.restore_postgres(args.name, args.file)
            print(f"Restore {'successful' if result else 'failed'}")
        else:
            print("Restore requires --service postgres --name <service_name> --file <backup_file>")
    
    elif args.command == 'list':
        backups = await backup_manager.list_backups(args.service)
        for service_type, files in backups.items():
            print(f"\n{service_type.upper()} Backups:")
            for file in files:
                print(f"  {file}")
    
    elif args.command == 'health':
        health = await backup_manager.health_check()
        print(json.dumps(health, indent=2))
    
    elif args.command == 'info':
        if args.file:
            info = await backup_manager.get_backup_info(args.file)
            print(json.dumps(info, indent=2))
        else:
            print("Info requires --file <backup_file>")

if __name__ == "__main__":
    asyncio.run(main())
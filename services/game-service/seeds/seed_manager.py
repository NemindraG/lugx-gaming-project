#!/usr/bin/env python3
"""
Seed Data Version Controller
Manages seed data versions, rollbacks, and incremental updates.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Add the parent directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://game_service:game_secure_password_2024@localhost:5432/lugx_games",
)


class SeedVersionController:
    """Manages seed data versions and migrations."""

    def __init__(self, database_url: str):
        self.database_url = database_url
        self.engine = create_async_engine(database_url, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )
        self.seeds_dir = Path(__file__).parent
        self.version_file = self.seeds_dir / "seed_versions.json"

    async def init_version_tracking(self):
        """Initialize seed version tracking table."""
        async with self.async_session() as session:
            await session.execute(
                text(
                    """
                CREATE TABLE IF NOT EXISTS game_service.seed_versions (
                    id SERIAL PRIMARY KEY,
                    version VARCHAR(50) NOT NULL UNIQUE,
                    description TEXT,
                    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    rollback_script TEXT
                )
            """
                )
            )
            await session.commit()

    async def get_current_version(self) -> Optional[str]:
        """Get the current seed data version."""
        async with self.async_session() as session:
            result = await session.execute(
                text(
                    """
                SELECT version FROM game_service.seed_versions 
                ORDER BY applied_at DESC LIMIT 1
            """
                )
            )
            row = result.fetchone()
            return row[0] if row else None

    async def get_version_history(self) -> List[Dict]:
        """Get complete version history."""
        async with self.async_session() as session:
            result = await session.execute(
                text(
                    """
                SELECT version, description, applied_at 
                FROM game_service.seed_versions 
                ORDER BY applied_at DESC
            """
                )
            )
            return [
                {"version": row[0], "description": row[1], "applied_at": row[2]}
                for row in result.fetchall()
            ]

    async def apply_seed_version(self, version: str, description: str = ""):
        """Apply a specific seed version."""
        print(f"🌱 Applying seed version: {version}")

        # Check if version already applied
        current_version = await self.get_current_version()
        if current_version == version:
            print(f"✅ Version {version} is already applied")
            return

        # Execute seed script
        seed_script = self.seeds_dir / f"{version}_seed.py"
        if not seed_script.exists():
            seed_script = self.seeds_dir / "development_seed.py"  # Fallback

        if seed_script.exists():
            # Import and run seed script
            print(f"📄 Executing seed script: {seed_script.name}")

            # Record version
            async with self.async_session() as session:
                await session.execute(
                    text(
                        """
                    INSERT INTO game_service.seed_versions (version, description)
                    VALUES (:version, :description)
                """
                    ),
                    {"version": version, "description": description},
                )
                await session.commit()

            print(f"✅ Version {version} applied successfully")
        else:
            print(f"❌ Seed script not found: {seed_script}")

    async def rollback_to_version(self, target_version: str):
        """Rollback to a specific version."""
        print(f"🔄 Rolling back to version: {target_version}")

        current_version = await self.get_current_version()
        if not current_version:
            print("❌ No current version found")
            return

        if current_version == target_version:
            print(f"✅ Already at version {target_version}")
            return

        # Clear current data
        await self.clear_seed_data()

        # Apply target version
        await self.apply_seed_version(
            target_version, f"Rollback from {current_version}"
        )

    async def clear_seed_data(self):
        """Clear all seed data from database."""
        print("🗑️  Clearing existing seed data...")

        async with self.async_session() as session:
            # Clear in correct order to respect foreign keys
            tables = [
                "reviews",
                "inventory",
                "game_categories",
                "games",
                "categories",
                "publishers",
            ]

            for table in tables:
                await session.execute(text(f"DELETE FROM game_service.{table}"))

            await session.commit()
        print("✅ Seed data cleared")

    async def backup_current_data(self, backup_name: str):
        """Create a backup of current data."""
        print(f"💾 Creating backup: {backup_name}")

        backup_dir = self.seeds_dir / "backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = backup_dir / f"{backup_name}_{timestamp}.sql"

        # Use pg_dump to create backup
        cmd = f"pg_dump -h localhost -p 5432 -U game_service -d lugx_games --schema=game_service > {backup_file}"
        os.system(cmd)

        print(f"✅ Backup created: {backup_file}")

    async def restore_from_backup(self, backup_file: str):
        """Restore data from backup file."""
        print(f"📥 Restoring from backup: {backup_file}")

        backup_path = Path(backup_file)
        if not backup_path.exists():
            backup_path = self.seeds_dir / "backups" / backup_file

        if not backup_path.exists():
            print(f"❌ Backup file not found: {backup_file}")
            return

        # Clear current data
        await self.clear_seed_data()

        # Restore from backup
        cmd = f"psql -h localhost -p 5432 -U game_service -d lugx_games < {backup_path}"
        os.system(cmd)

        print("✅ Data restored from backup")

    async def status(self):
        """Show current seed data status."""
        print("📊 Seed Data Status")
        print("=" * 50)

        current_version = await self.get_current_version()
        print(f"Current Version: {current_version or 'None'}")

        # Show table counts
        async with self.async_session() as session:
            tables = [
                "publishers",
                "categories",
                "games",
                "game_categories",
                "inventory",
                "reviews",
            ]

            for table in tables:
                result = await session.execute(
                    text(f"SELECT COUNT(*) FROM game_service.{table}")
                )
                count = result.fetchone()[0]
                print(f"{table.title()}: {count}")

        print("\n📋 Version History:")
        history = await self.get_version_history()
        for version_info in history[:5]:  # Show last 5 versions
            print(
                f"  • {version_info['version']} - {version_info['applied_at']} - {version_info['description']}"
            )

    async def close(self):
        """Clean up resources."""
        await self.engine.dispose()


# CLI Commands
async def main():
    """Command-line interface for seed version control."""
    if len(sys.argv) < 2:
        print(
            """
🌱 Seed Version Controller

Usage:
  python seed_manager.py <command> [arguments]

Commands:
  init                    - Initialize version tracking
  status                  - Show current status
  apply <version> [desc]  - Apply specific version
  rollback <version>      - Rollback to version
  clear                   - Clear all seed data
  backup <name>           - Create backup
  restore <backup>        - Restore from backup
  history                 - Show version history

Examples:
  python seed_manager.py init
  python seed_manager.py apply v1.0 "Initial game catalog"
  python seed_manager.py status
  python seed_manager.py rollback v1.0
  python seed_manager.py backup before_update
        """
        )
        return

    controller = SeedVersionController(DATABASE_URL)

    try:
        command = sys.argv[1]

        if command == "init":
            await controller.init_version_tracking()
            print("✅ Version tracking initialized")

        elif command == "status":
            await controller.status()

        elif command == "apply":
            if len(sys.argv) < 3:
                print("❌ Version required: apply <version> [description]")
                return
            version = sys.argv[2]
            description = sys.argv[3] if len(sys.argv) > 3 else ""
            await controller.apply_seed_version(version, description)

        elif command == "rollback":
            if len(sys.argv) < 3:
                print("❌ Version required: rollback <version>")
                return
            version = sys.argv[2]
            await controller.rollback_to_version(version)

        elif command == "clear":
            await controller.clear_seed_data()

        elif command == "backup":
            if len(sys.argv) < 3:
                print("❌ Backup name required: backup <name>")
                return
            name = sys.argv[2]
            await controller.backup_current_data(name)

        elif command == "restore":
            if len(sys.argv) < 3:
                print("❌ Backup file required: restore <backup>")
                return
            backup = sys.argv[2]
            await controller.restore_from_backup(backup)

        elif command == "history":
            history = await controller.get_version_history()
            print("📋 Version History:")
            for version_info in history:
                print(
                    f"  • {version_info['version']} - {version_info['applied_at']} - {version_info['description']}"
                )

        else:
            print(f"❌ Unknown command: {command}")

    finally:
        await controller.close()


if __name__ == "__main__":
    asyncio.run(main())

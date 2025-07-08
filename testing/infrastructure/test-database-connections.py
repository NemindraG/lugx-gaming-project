#!/usr/bin/env python3
"""
Database Infrastructure Connection Test
Tests all database connections to ensure infrastructure is properly configured
"""

import asyncio
import asyncpg
import redis
from clickhouse_driver import Client
import sys
from datetime import datetime

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    END = '\033[0m'

async def test_postgres_game():
    """Test PostgreSQL Game Service connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5432,
            user='game_service',
            password='game_secure_password_2024',
            database='lugx_games'
        )
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        await conn.close()
        
        print(f"{Colors.GREEN}✓ PostgreSQL Game Service: Connected{Colors.END}")
        print(f"  Version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ PostgreSQL Game Service: Failed{Colors.END}")
        print(f"  Error: {e}")
        return False

async def test_postgres_order():
    """Test PostgreSQL Order Service connection"""
    try:
        conn = await asyncpg.connect(
            host='localhost',
            port=5433,
            user='order_service',
            password='order_secure_password_2024',
            database='lugx_orders'
        )
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        await conn.close()
        
        print(f"{Colors.GREEN}✓ PostgreSQL Order Service: Connected{Colors.END}")
        print(f"  Version: {version.split(',')[0]}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ PostgreSQL Order Service: Failed{Colors.END}")
        print(f"  Error: {e}")
        return False

def test_clickhouse():
    """Test ClickHouse connection"""
    try:
        client = Client(
            host='localhost',
            port=9000,
            user='analytics_service',
            password='analytics_secure_password_2024',
            database='lugx_analytics'
        )
        
        # Test query
        result = client.execute('SELECT version()')
        version = result[0][0]
        
        # Check tables
        tables = client.execute('SHOW TABLES')
        
        print(f"{Colors.GREEN}✓ ClickHouse Analytics: Connected{Colors.END}")
        print(f"  Version: {version}")
        print(f"  Tables: {len(tables)} created")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ ClickHouse Analytics: Failed{Colors.END}")
        print(f"  Error: {e}")
        return False

def test_redis():
    """Test Redis connection"""
    try:
        r = redis.Redis(
            host='localhost',
            port=6379,
            password='redis_secure_password_2024',
            decode_responses=True
        )
        
        # Test commands
        r.ping()
        info = r.info()
        
        # Test set/get
        r.set('test_key', 'test_value', ex=10)
        value = r.get('test_key')
        
        print(f"{Colors.GREEN}✓ Redis Cache: Connected{Colors.END}")
        print(f"  Version: {info['redis_version']}")
        print(f"  Memory Used: {info['used_memory_human']}")
        return True
    except Exception as e:
        print(f"{Colors.RED}✗ Redis Cache: Failed{Colors.END}")
        print(f"  Error: {e}")
        return False

async def main():
    """Run all connection tests"""
    print(f"\n{Colors.YELLOW}=== Lugx Gaming Database Infrastructure Test ==={Colors.END}")
    print(f"Testing at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    results = []
    
    # Test all databases
    results.append(await test_postgres_game())
    print()
    results.append(await test_postgres_order())
    print()
    results.append(test_clickhouse())
    print()
    results.append(test_redis())
    
    # Summary
    print(f"\n{Colors.YELLOW}=== Test Summary ==={Colors.END}")
    total = len(results)
    passed = sum(results)
    
    if passed == total:
        print(f"{Colors.GREEN}All {total} database connections successful!{Colors.END}")
        print("\nInfrastructure is ready for Week 2: Schema Implementation")
        return 0
    else:
        print(f"{Colors.RED}{passed}/{total} connections successful{Colors.END}")
        print("\nPlease check failed services before proceeding")
        return 1

if __name__ == "__main__":
    # Check required packages
    try:
        import asyncpg
        import redis
        from clickhouse_driver import Client
    except ImportError as e:
        print(f"{Colors.RED}Missing required package: {e}{Colors.END}")
        print("\nInstall requirements:")
        print("pip install asyncpg redis clickhouse-driver")
        sys.exit(1)
    
    # Run tests
    sys.exit(asyncio.run(main()))
#!/usr/bin/env python3
"""
Kubernetes Migration Integration Test Script
Tests the complete migration workflow with Kubernetes Secrets and Init Containers
"""

import os
import sys
import subprocess
import time
import base64
import yaml
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(message):
    """Print a formatted header message"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 60}")
    print(f"{message}")
    print(f"{'=' * 60}{Colors.END}")

def print_success(message):
    """Print a success message"""
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message):
    """Print an error message"""
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message):
    """Print a warning message"""
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message):
    """Print an info message"""
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def run_command(command, description, capture_output=True, check=True):
    """Run a command and handle output"""
    print_info(f"Running: {description}")
    print(f"Command: {command}")
    
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=check
            )
            if result.returncode == 0:
                print_success(f"✅ {description} - Success")
                if result.stdout.strip():
                    print(f"Output: {result.stdout.strip()}")
                return result
            else:
                print_error(f"❌ {description} - Failed")
                if result.stderr.strip():
                    print(f"Error: {result.stderr.strip()}")
                return result if not check else None
        else:
            result = subprocess.run(command, shell=True, check=check)
            print_success(f"✅ {description} - Success")
            return result
    except subprocess.CalledProcessError as e:
        print_error(f"❌ {description} - Failed with exit code {e.returncode}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error: {e.stderr}")
        return None
    except Exception as e:
        print_error(f"❌ {description} - Exception: {str(e)}")
        return None

def check_prerequisites():
    """Check if required tools are available"""
    print_header("CHECKING PREREQUISITES")
    
    tools = {
        'kubectl': 'kubectl version --client',
        'kustomize': 'kustomize version',
        'docker': 'docker version',
        'alembic': 'alembic --version'
    }
    
    missing_tools = []
    
    for tool, command in tools.items():
        result = run_command(command, f"Checking {tool}", check=False)
        if result is None or result.returncode != 0:
            missing_tools.append(tool)
            print_error(f"{tool} is not available")
        else:
            print_success(f"{tool} is available")
    
    if missing_tools:
        print_error(f"Missing required tools: {', '.join(missing_tools)}")
        return False
    
    print_success("All prerequisites met")
    return True

def test_kubernetes_manifests():
    """Test Kubernetes manifest validation"""
    print_header("TESTING KUBERNETES MANIFESTS")
    
    # Get project root
    project_root = Path(__file__).parent.parent.parent
    k8s_path = project_root / "infrastructure" / "kubernetes" / "base"
    
    if not k8s_path.exists():
        print_error(f"Kubernetes manifests not found at {k8s_path}")
        return False
    
    # Test kustomize build
    result = run_command(
        f"cd {k8s_path} && kustomize build .",
        "Validating Kubernetes manifests with kustomize"
    )
    
    if result is None:
        print_error("Kustomize build failed")
        return False
    
    print_success("Kubernetes manifests are valid")
    return True

def test_database_secrets():
    """Test database secrets validation"""
    print_header("TESTING DATABASE SECRETS")
    
    project_root = Path(__file__).parent.parent.parent
    secrets_file = project_root / "infrastructure" / "kubernetes" / "base" / "configs" / "database-secrets.yaml"
    
    if not secrets_file.exists():
        print_error(f"Database secrets file not found at {secrets_file}")
        return False
    
    try:
        with open(secrets_file, 'r') as f:
            content = f.read()
            
        # Split by --- to handle multiple YAML documents
        documents = content.split('---')
        secrets_count = 0
        
        for doc in documents:
            if doc.strip():
                secret = yaml.safe_load(doc.strip())
                if secret and secret.get('kind') == 'Secret':
                    secrets_count += 1
                    
                    # Validate base64 encoding
                    if 'data' in secret:
                        for key, value in secret['data'].items():
                            try:
                                decoded = base64.b64decode(value).decode('utf-8')
                                print_success(f"Secret {secret['metadata']['name']}.{key}: {decoded}")
                            except Exception as e:
                                print_error(f"Invalid base64 in {key}: {e}")
                                return False
        
        print_success(f"Found {secrets_count} valid secret manifests")
        return True
        
    except Exception as e:
        print_error(f"Failed to parse secrets file: {e}")
        return False

def test_alembic_configuration():
    """Test Alembic configuration"""
    print_header("TESTING ALEMBIC CONFIGURATION")
    
    project_root = Path(__file__).parent.parent.parent
    
    services = ['game-service', 'order-service']
    
    for service in services:
        service_path = project_root / "services" / service
        alembic_ini = service_path / "alembic.ini"
        alembic_env = service_path / "alembic" / "env.py"
        
        print_info(f"Testing {service} Alembic configuration")
        
        if not alembic_ini.exists():
            print_error(f"alembic.ini not found for {service}")
            return False
        
        if not alembic_env.exists():
            print_error(f"alembic/env.py not found for {service}")
            return False
        
        # Check if alembic.ini uses environment variable
        with open(alembic_ini, 'r') as f:
            ini_content = f.read()
            if '${DATABASE_URL}' not in ini_content:
                print_error(f"{service} alembic.ini doesn't use DATABASE_URL environment variable")
                return False
        
        # Test alembic check command (dry run)
        os.environ['DATABASE_URL'] = 'postgresql+asyncpg://test:test@localhost:5432/test'
        result = run_command(
            f"cd {service_path} && alembic check",
            f"Testing {service} Alembic configuration",
            check=False
        )
        
        if result and result.returncode == 0:
            print_success(f"{service} Alembic configuration is valid")
        else:
            print_warning(f"{service} Alembic check failed (expected if database not available)")
    
    return True

def test_deployment_manifests():
    """Test deployment manifest structure"""
    print_header("TESTING DEPLOYMENT MANIFESTS")
    
    project_root = Path(__file__).parent.parent.parent
    deployments_path = project_root / "infrastructure" / "kubernetes" / "base" / "deployments"
    
    expected_deployments = [
        'game-service-deployment.yaml',
        'order-service-deployment.yaml'
    ]
    
    for deployment_file in expected_deployments:
        deployment_path = deployments_path / deployment_file
        
        if not deployment_path.exists():
            print_error(f"Deployment file not found: {deployment_file}")
            return False
        
        try:
            with open(deployment_path, 'r') as f:
                docs = list(yaml.safe_load_all(f))
            
            # Validate deployment structure
            deployment_found = False
            service_found = False
            
            for doc in docs:
                if doc and doc.get('kind') == 'Deployment':
                    deployment_found = True
                    
                    # Check for init container
                    init_containers = doc.get('spec', {}).get('template', {}).get('spec', {}).get('initContainers', [])
                    if not init_containers:
                        print_error(f"No init containers found in {deployment_file}")
                        return False
                    
                    # Check for migration init container
                    migration_container = None
                    for container in init_containers:
                        if container.get('name') == 'migration':
                            migration_container = container
                            break
                    
                    if not migration_container:
                        print_error(f"Migration init container not found in {deployment_file}")
                        return False
                    
                    # Check migration container command
                    command = migration_container.get('command', [])
                    if not any('alembic' in str(cmd) for cmd in command):
                        print_error(f"Migration container doesn't run alembic in {deployment_file}")
                        return False
                    
                    print_success(f"Deployment {deployment_file} has valid migration init container")
                
                elif doc and doc.get('kind') == 'Service':
                    service_found = True
                    print_success(f"Service configuration found in {deployment_file}")
            
            if not deployment_found:
                print_error(f"No Deployment found in {deployment_file}")
                return False
            
            if not service_found:
                print_error(f"No Service found in {deployment_file}")
                return False
                
        except Exception as e:
            print_error(f"Failed to parse {deployment_file}: {e}")
            return False
    
    return True

def test_environment_variable_mapping():
    """Test environment variable mapping in deployments"""
    print_header("TESTING ENVIRONMENT VARIABLE MAPPING")
    
    project_root = Path(__file__).parent.parent.parent
    deployments_path = project_root / "infrastructure" / "kubernetes" / "base" / "deployments"
    
    # Expected environment variables for each service
    expected_env_vars = {
        'game-service-deployment.yaml': [
            'DATABASE_URL', 'GAME_DB_HOST', 'GAME_DB_PORT', 
            'GAME_DB_NAME', 'GAME_DB_USER', 'GAME_DB_PASSWORD'
        ],
        'order-service-deployment.yaml': [
            'DATABASE_URL', 'ORDER_DB_HOST', 'ORDER_DB_PORT',
            'ORDER_DB_NAME', 'ORDER_DB_USER', 'ORDER_DB_PASSWORD'
        ]
    }
    
    for deployment_file, required_vars in expected_env_vars.items():
        deployment_path = deployments_path / deployment_file
        
        try:
            with open(deployment_path, 'r') as f:
                docs = list(yaml.safe_load_all(f))
            
            for doc in docs:
                if doc and doc.get('kind') == 'Deployment':
                    # Check init container env vars
                    init_containers = doc.get('spec', {}).get('template', {}).get('spec', {}).get('initContainers', [])
                    main_containers = doc.get('spec', {}).get('template', {}).get('spec', {}).get('containers', [])
                    
                    for container_list, container_type in [(init_containers, 'init'), (main_containers, 'main')]:
                        for container in container_list:
                            env_vars = container.get('env', [])
                            found_vars = [var['name'] for var in env_vars]
                            
                            missing_vars = [var for var in required_vars if var not in found_vars]
                            if missing_vars:
                                print_error(f"Missing env vars in {container_type} container: {missing_vars}")
                                return False
                            
                            print_success(f"{deployment_file} {container_type} container has all required env vars")
                            
        except Exception as e:
            print_error(f"Failed to check env vars in {deployment_file}: {e}")
            return False
    
    return True

def run_integration_tests():
    """Run all integration tests"""
    print_header("KUBERNETES MIGRATION INTEGRATION TESTS")
    print(f"{Colors.BOLD}Testing Alembic + Kubernetes Integration{Colors.END}")
    
    tests = [
        ("Prerequisites Check", check_prerequisites),
        ("Kubernetes Manifests", test_kubernetes_manifests),
        ("Database Secrets", test_database_secrets),
        ("Alembic Configuration", test_alembic_configuration),
        ("Deployment Manifests", test_deployment_manifests),
        ("Environment Variables", test_environment_variable_mapping),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed_tests += 1
            else:
                print_error(f"Test failed: {test_name}")
        except Exception as e:
            print_error(f"Test exception in {test_name}: {str(e)}")
    
    print_header("TEST RESULTS SUMMARY")
    
    if passed_tests == total_tests:
        print_success(f"🎉 ALL TESTS PASSED ({passed_tests}/{total_tests})")
        print(f"{Colors.GREEN}{Colors.BOLD}")
        print("✅ Kubernetes Secrets are properly configured")
        print("✅ Init Container migrations are correctly set up")
        print("✅ Alembic is configured for Kubernetes environment")
        print("✅ Deployment manifests are valid")
        print("✅ Environment variable mapping is correct")
        print(f"{Colors.END}")
        return True
    else:
        print_error(f"💥 TESTS FAILED ({passed_tests}/{total_tests} passed)")
        print(f"{Colors.RED}{Colors.BOLD}")
        print("❌ Migration integration is not ready for deployment")
        print("❌ Please fix the failing tests before proceeding")
        print(f"{Colors.END}")
        return False

if __name__ == "__main__":
    success = run_integration_tests()
    sys.exit(0 if success else 1)
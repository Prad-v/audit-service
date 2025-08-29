#!/usr/bin/env python3
"""
Helm Chart Test Script

This script tests the Helm chart locally by:
1. Linting the chart
2. Validating templates
3. Testing with different values files
4. Checking for common issues
"""

import os
import sys
import subprocess
import yaml
import tempfile
from pathlib import Path
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=check, cwd=cwd)
        return result.stdout.strip(), result.stderr.strip(), result.returncode
    except subprocess.CalledProcessError as e:
        return e.stdout.strip(), e.stderr.strip(), e.returncode

def print_header(title):
    """Print a formatted header."""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}{title:^60}")
    print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")

def print_success(message):
    """Print a success message."""
    print(f"{Fore.GREEN}✅ {message}{Style.RESET_ALL}")

def print_error(message):
    """Print an error message."""
    print(f"{Fore.RED}❌ {message}{Style.RESET_ALL}")

def print_info(message):
    """Print an info message."""
    print(f"{Fore.BLUE}ℹ️  {message}{Style.RESET_ALL}")

def check_helm_installed():
    """Check if Helm is installed."""
    print_header("Checking Helm Installation")
    
    stdout, stderr, returncode = run_command(["helm", "version"], check=False)
    
    if returncode == 0:
        print_success("Helm is installed")
        print_info(f"Version: {stdout}")
        return True
    else:
        print_error("Helm is not installed or not in PATH")
        print_info("Please install Helm: https://helm.sh/docs/intro/install/")
        return False

def lint_chart(chart_path):
    """Lint the Helm chart."""
    print_header("Linting Helm Chart")
    
    stdout, stderr, returncode = run_command(["helm", "lint", chart_path], check=False)
    
    if returncode == 0:
        print_success("Chart linting passed")
        return True
    else:
        print_error("Chart linting failed")
        print_info("Lint output:")
        print(stdout)
        if stderr:
            print(stderr)
        return False

def validate_templates(chart_path, values_file=None):
    """Validate Helm templates."""
    print_header("Validating Helm Templates")
    
    cmd = ["helm", "template", "test-release", chart_path]
    if values_file:
        cmd.extend(["--values", values_file])
    
    stdout, stderr, returncode = run_command(cmd, check=False)
    
    if returncode == 0:
        print_success("Template validation passed")
        return True
    else:
        print_error("Template validation failed")
        print_info("Template output:")
        print(stdout)
        if stderr:
            print(stderr)
        return False

def check_chart_structure(chart_path):
    """Check Helm chart structure."""
    print_header("Checking Chart Structure")
    
    required_files = [
        "Chart.yaml",
        "values.yaml",
        "templates/",
        "templates/_helpers.tpl",
        "templates/namespace.yaml",
        "templates/backend-deployment.yaml",
        "templates/frontend-deployment.yaml",
        "templates/worker-deployment.yaml",
        "templates/services.yaml",
        "templates/ingress.yaml",
        "templates/hpa.yaml",
        "templates/rbac.yaml",
        "templates/configmap.yaml",
        "templates/secret.yaml"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = os.path.join(chart_path, file_path)
        if not os.path.exists(full_path):
            missing_files.append(file_path)
        else:
            print_success(f"✓ {file_path}")
    
    if missing_files:
        print_error("Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False
    
    return True

def validate_chart_yaml(chart_path):
    """Validate Chart.yaml file."""
    print_header("Validating Chart.yaml")
    
    chart_yaml_path = os.path.join(chart_path, "Chart.yaml")
    
    try:
        with open(chart_yaml_path, 'r') as f:
            chart_data = yaml.safe_load(f)
        
        required_fields = ['apiVersion', 'name', 'description', 'version', 'appVersion']
        missing_fields = []
        
        for field in required_fields:
            if field not in chart_data:
                missing_fields.append(field)
            else:
                print_success(f"✓ {field}: {chart_data[field]}")
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        return True
        
    except Exception as e:
        print_error(f"Error reading Chart.yaml: {e}")
        return False

def test_values_files(chart_path):
    """Test different values files."""
    print_header("Testing Values Files")
    
    values_dir = os.path.join(chart_path, "values")
    if not os.path.exists(values_dir):
        print_info("No values directory found, skipping values file tests")
        return True
    
    values_files = [
        "values-dev.yaml",
        "values-staging.yaml", 
        "values-prod.yaml"
    ]
    
    all_passed = True
    
    for values_file in values_files:
        values_path = os.path.join(values_dir, values_file)
        if os.path.exists(values_path):
            print_info(f"Testing {values_file}...")
            
            cmd = ["helm", "template", "test-release", chart_path, "--values", values_path]
            stdout, stderr, returncode = run_command(cmd, check=False)
            
            if returncode == 0:
                print_success(f"✓ {values_file} - Template validation passed")
            else:
                print_error(f"✗ {values_file} - Template validation failed")
                all_passed = False
        else:
            print_info(f"Skipping {values_file} - file not found")
    
    return all_passed

def package_chart(chart_path):
    """Package the Helm chart."""
    print_header("Packaging Helm Chart")
    
    # Change to chart directory
    chart_dir = os.path.dirname(chart_path)
    chart_name = os.path.basename(chart_path)
    
    stdout, stderr, returncode = run_command(["helm", "package", chart_name], cwd=chart_dir, check=False)
    
    if returncode == 0:
        print_success("Chart packaged successfully")
        # Find the generated .tgz file
        tgz_files = list(Path(chart_dir).glob("*.tgz"))
        if tgz_files:
            print_info(f"Generated package: {tgz_files[0].name}")
        return True
    else:
        print_error("Chart packaging failed")
        print_info("Package output:")
        print(stdout)
        if stderr:
            print(stderr)
        return False

def check_security_best_practices(chart_path):
    """Check for security best practices."""
    print_header("Checking Security Best Practices")
    
    issues = []
    
    # Check for non-root containers
    templates_dir = os.path.join(chart_path, "templates")
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.yaml'):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Skip HPA files for security checks
                    if 'hpa' in file.lower():
                        continue
                    
                    # Check for security context
                    if 'securityContext' not in content and 'Deployment' in content:
                        issues.append(f"Missing securityContext in {file}")
                    
                    # Check for resource limits
                    if 'resources:' not in content and 'Deployment' in content:
                        issues.append(f"Missing resource limits in {file}")
                        
                except Exception as e:
                    issues.append(f"Error reading {file}: {e}")
    
    if issues:
        print_error("Security issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print_success("Security best practices check passed")
        return True

def main():
    """Main function."""
    print_header("Helm Chart Test Suite")
    
    # Get chart path
    chart_path = "helm/audit-service"
    if not os.path.exists(chart_path):
        print_error(f"Chart path not found: {chart_path}")
        return False
    
    results = []
    
    # Run tests
    results.append(("Helm Installation", check_helm_installed()))
    results.append(("Chart Structure", check_chart_structure(chart_path)))
    results.append(("Chart.yaml Validation", validate_chart_yaml(chart_path)))
    results.append(("Chart Linting", lint_chart(chart_path)))
    results.append(("Template Validation", validate_templates(chart_path)))
    results.append(("Values Files", test_values_files(chart_path)))
    results.append(("Security Best Practices", check_security_best_practices(chart_path)))
    results.append(("Chart Packaging", package_chart(chart_path)))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Fore.GREEN}PASS{Style.RESET_ALL}" if result else f"{Fore.RED}FAIL{Style.RESET_ALL}"
        print(f"{status} {test_name}")
    
    print(f"\n{Fore.CYAN}Results: {passed}/{total} tests passed{Style.RESET_ALL}")
    
    if passed == total:
        print_success("🎉 All Helm chart tests passed!")
        print_info("\nNext steps:")
        print_info("1. Review the generated chart package")
        print_info("2. Test deployment in a local Kubernetes cluster")
        print_info("3. Push to your Helm repository")
    else:
        print_error(f"❌ {total - passed} tests failed. Please fix the issues above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)

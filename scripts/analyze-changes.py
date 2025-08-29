#!/usr/bin/env python3
"""
Change Analysis Script

This script analyzes changes in the repository and provides a summary
similar to what the CI pipeline generates.
"""

import os
import sys
import subprocess
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

def run_command(cmd: List[str]) -> str:
    """Run a command and return the output."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command {' '.join(cmd)}: {e}")
        return ""

def get_changed_files(prev_commit: str = None) -> List[str]:
    """Get list of changed files."""
    if prev_commit:
        cmd = ["git", "diff", "--name-only", prev_commit, "HEAD"]
    else:
        cmd = ["git", "diff", "--name-only", "HEAD~1", "HEAD"]
    
    output = run_command(cmd)
    if output:
        return output.split('\n')
    return []

def get_commit_info() -> Dict[str, str]:
    """Get current commit information."""
    info = {}
    
    # Get current branch
    info['branch'] = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    
    # Get current commit hash
    info['commit'] = run_command(["git", "rev-parse", "HEAD"])
    
    # Get commit message
    info['message'] = run_command(["git", "log", "-1", "--pretty=format:%s"])
    
    # Get author
    info['author'] = run_command(["git", "log", "-1", "--pretty=format:%an"])
    
    # Get commit date
    info['date'] = run_command(["git", "log", "-1", "--pretty=format:%cd"])
    
    return info

def get_recent_commits(count: int = 5) -> List[str]:
    """Get recent commit messages."""
    cmd = ["git", "log", f"-{count}", "--oneline"]
    output = run_command(cmd)
    if output:
        return output.split('\n')
    return []

def analyze_change_types(files: List[str]) -> Dict[str, int]:
    """Analyze what types of changes were made."""
    change_types = {
        'backend': 0,
        'frontend': 0,
        'infrastructure': 0,
        'documentation': 0,
        'tests': 0,
        'other': 0
    }
    
    for file_path in files:
        if not file_path:
            continue
            
        if file_path.startswith('backend/') or file_path.endswith('.py'):
            change_types['backend'] += 1
        elif file_path.startswith('frontend/') or file_path.endswith(('.tsx', '.ts', '.jsx', '.js', '.css', '.html')):
            change_types['frontend'] += 1
        elif any(file_path.startswith(prefix) for prefix in ['docker-compose', 'Dockerfile', 'k8s/', 'terraform/', '.github/']):
            change_types['infrastructure'] += 1
        elif file_path.endswith(('.md', '.txt', '.rst')):
            change_types['documentation'] += 1
        elif file_path.startswith('tests/') or file_path.startswith('test_'):
            change_types['tests'] += 1
        else:
            change_types['other'] += 1
    
    return change_types

def generate_summary(commit_info: Dict[str, str], change_types: Dict[str, int], 
                    changed_files: List[str], recent_commits: List[str]) -> str:
    """Generate a comprehensive change summary."""
    summary = []
    summary.append("## 📊 Change Analysis")
    summary.append("")
    
    # Basic information
    summary.append(f"**Repository:** {os.getcwd().split('/')[-1]}")
    summary.append(f"**Branch:** {commit_info.get('branch', 'unknown')}")
    summary.append(f"**Commit:** {commit_info.get('commit', 'unknown')}")
    summary.append(f"**Author:** {commit_info.get('author', 'unknown')}")
    summary.append(f"**Date:** {commit_info.get('date', 'unknown')}")
    summary.append("")
    
    # Change statistics
    summary.append("### 📈 Change Statistics")
    summary.append("")
    summary.append(f"- **Backend Changes:** {change_types['backend']} files")
    summary.append(f"- **Frontend Changes:** {change_types['frontend']} files")
    summary.append(f"- **Infrastructure Changes:** {change_types['infrastructure']} files")
    summary.append(f"- **Documentation Changes:** {change_types['documentation']} files")
    summary.append(f"- **Test Changes:** {change_types['tests']} files")
    summary.append(f"- **Other Changes:** {change_types['other']} files")
    summary.append("")
    
    # Change types
    modified_areas = [area for area, count in change_types.items() if count > 0]
    summary.append("### 🔄 Change Types")
    summary.append("")
    summary.append(f"**Areas Modified:** {', '.join(modified_areas)}")
    summary.append("")
    
    # Recent commits
    summary.append("### 📝 Recent Commits")
    summary.append("")
    summary.append("```")
    for commit in recent_commits[:5]:
        summary.append(commit)
    summary.append("```")
    summary.append("")
    
    # Changed files
    summary.append("### 📁 Changed Files")
    summary.append("")
    summary.append("```")
    for file_path in changed_files[:20]:
        summary.append(file_path)
    if len(changed_files) > 20:
        summary.append(f"... and {len(changed_files) - 20} more files")
    summary.append("```")
    summary.append("")
    
    return '\n'.join(summary)

def main():
    """Main function."""
    print("🔍 Analyzing changes in the repository...")
    print("=" * 60)
    
    # Get commit information
    commit_info = get_commit_info()
    
    # Get changed files
    changed_files = get_changed_files()
    
    if not changed_files:
        print("No changes detected or this is the initial commit.")
        return
    
    # Get recent commits
    recent_commits = get_recent_commits()
    
    # Analyze change types
    change_types = analyze_change_types(changed_files)
    
    # Generate summary
    summary = generate_summary(commit_info, change_types, changed_files, recent_commits)
    
    # Print summary
    print(summary)
    
    # Save to file
    output_file = "change-analysis.md"
    with open(output_file, 'w') as f:
        f.write(summary)
    
    print(f"\n📄 Change analysis saved to: {output_file}")
    
    # Print statistics
    total_changes = sum(change_types.values())
    print(f"\n📊 Total files changed: {total_changes}")
    
    if total_changes > 0:
        print("\n📈 Change Distribution:")
        for change_type, count in change_types.items():
            if count > 0:
                percentage = (count / total_changes) * 100
                print(f"  {change_type.capitalize()}: {count} files ({percentage:.1f}%)")

if __name__ == "__main__":
    main()

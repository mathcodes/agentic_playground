#!/usr/bin/env python3
"""
Agent Training Script

Uploads all knowledge base files to train the AI agents.
"""

import requests
import json
import os
from pathlib import Path

# Configuration
API_URL = "http://127.0.0.1:5001/api/training"
KNOWLEDGE_BASE_DIR = Path(__file__).parent / "knowledge_base"

# Training files mapping (path -> agent_type, title)
TRAINING_FILES = [
    # SQL Agent Training
    ("sql/database_best_practices.md", "sql", "SQL Database Best Practices"),
    ("sql/query_optimization.md", "sql", "SQL Query Optimization Guide"),
    ("sql/common_patterns.md", "sql", "SQL Common Patterns"),
    
    # C# Agent Training
    ("csharp/linq_patterns.md", "csharp", "C# LINQ Query Patterns"),
    ("csharp/async_await_patterns.md", "csharp", "C# Async/Await Patterns"),
    ("csharp/entity_framework_tips.md", "csharp", "Entity Framework Core Tips"),
    
    # Shared Training (all agents)
    ("shared/common_errors.md", "general", "Common Errors and Solutions"),
]


def upload_training_data(file_path: Path, agent_type: str, title: str):
    """Upload a single training file."""
    try:
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Prepare request
        payload = {
            "agent_type": agent_type,
            "title": title,
            "content": content
        }
        
        print(f"\n{'='*70}")
        print(f"Uploading: {title}")
        print(f"Agent Type: {agent_type}")
        print(f"File: {file_path}")
        print(f"Size: {len(content):,} characters")
        print(f"{'='*70}")
        
        # Send request
        response = requests.post(
            API_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        # Handle response
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"[SUCCESS] Uploaded successfully!")
                print(f"  - Document ID: {result.get('document_id')}")
                print(f"  - Chunks created: {result.get('chunks')}")
                print(f"  - Processing time: {result.get('processing_time_ms')}ms")
                return True
            else:
                print(f"[ERROR] Upload failed: {result.get('error')}")
                return False
        else:
            print(f"[ERROR] HTTP {response.status_code}: {response.text}")
            return False
            
    except FileNotFoundError:
        print(f"[ERROR] File not found: {file_path}")
        return False
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {str(e)}")
        return False
    except Exception as e:
        print(f"[ERROR] Unexpected error: {str(e)}")
        return False


def main():
    """Main training function."""
    print("\n" + "="*70)
    print("AGENT TRAINING SYSTEM")
    print("="*70)
    print(f"\nKnowledge Base Directory: {KNOWLEDGE_BASE_DIR}")
    print(f"API Endpoint: {API_URL}")
    print(f"Total Files to Upload: {len(TRAINING_FILES)}")
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:5001/api/config", timeout=5)
        if response.status_code != 200:
            print("\n[ERROR] Server is not responding correctly!")
            print("Please ensure the web server is running: python web_ui.py")
            return
    except requests.exceptions.RequestException:
        print("\n[ERROR] Cannot connect to server!")
        print("Please ensure the web server is running: python web_ui.py")
        return
    
    print("\n[OK] Server is running\n")
    
    # Upload all files
    success_count = 0
    failed_count = 0
    
    for relative_path, agent_type, title in TRAINING_FILES:
        file_path = KNOWLEDGE_BASE_DIR / relative_path
        
        if upload_training_data(file_path, agent_type, title):
            success_count += 1
        else:
            failed_count += 1
    
    # Summary
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    print(f"Successfully uploaded: {success_count}")
    print(f"Failed: {failed_count}")
    print(f"Total: {len(TRAINING_FILES)}")
    
    if failed_count == 0:
        print("\n[SUCCESS] All training data uploaded successfully!")
        print("\nYour agents are now trained with:")
        print("  - SQL best practices and optimization")
        print("  - C# LINQ, async/await, and Entity Framework")
        print("  - Common error patterns and solutions")
        print("\nThe AI agents will now use this knowledge to provide better responses!")
    else:
        print(f"\n[WARNING] {failed_count} file(s) failed to upload.")
        print("Please check the errors above and retry if needed.")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    main()

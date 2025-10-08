#!/usr/bin/env python3
"""
Setup script for the complete Prompt2Figma project.
This installs both the backend and MCP server dependencies.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, cwd=None):
    """Run a shell command and handle errors."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            cwd=cwd,
            capture_output=True,
            text=True
        )
        print(f"✅ {command}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        print(f"Error: {e.stderr}")
        return None


def check_node_dependencies():
    """Check if Node.js dependencies are installed."""
    if not os.path.exists("node_modules"):
        print("📦 Installing Node.js dependencies...")
        result = run_command("npm install")
        if not result:
            print("⚠️  Node.js dependencies failed to install. AST validation may not work.")
    else:
        print("✅ Node.js dependencies already installed")


def install_python_dependencies():
    """Install Python dependencies."""
    print("🐍 Installing Python dependencies...")
    
    # Install main requirements
    result = run_command(f"{sys.executable} -m pip install -r requirements.txt")
    if not result:
        print("❌ Failed to install main requirements")
        return False
    
    # Install MCP server
    mcp_path = Path("prompt2figma-mcp")
    if mcp_path.exists():
        print("🔧 Installing MCP server...")
        result = run_command(f"{sys.executable} -m pip install -e .", cwd=mcp_path)
        if not result:
            print("❌ Failed to install MCP server")
            return False
    
    return True


def setup_environment():
    """Set up environment files."""
    env_example = Path(".env.example")
    env_file = Path(".env")
    
    if env_example.exists() and not env_file.exists():
        print("📝 Creating .env file from example...")
        import shutil
        shutil.copy(env_example, env_file)
        print("⚠️  Please update .env with your actual API keys and configuration")
    elif env_file.exists():
        print("✅ .env file already exists")
    else:
        print("⚠️  No .env.example found. You may need to create environment configuration manually.")


def main():
    """Main setup function."""
    print("🚀 Setting up Prompt2Figma Project")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install dependencies
    if not install_python_dependencies():
        print("❌ Setup failed during Python dependency installation")
        sys.exit(1)
    
    # Check Node.js dependencies
    check_node_dependencies()
    
    # Setup environment
    setup_environment()
    
    print("\n🎉 Setup complete!")
    print("\nNext steps:")
    print("1. Update your .env file with proper API keys")
    print("2. Start Redis server: redis-server")
    print("3. Start Celery worker: celery -A app.tasks.celery_app worker --loglevel=info")
    print("4. Start the backend: uvicorn app.main:app --reload")
    print("5. Test MCP server: python prompt2figma-mcp/test_mcp.py")
    print("\nFor MCP integration with Kiro:")
    print("- The MCP configuration is already set up in .kiro/settings/mcp.json")
    print("- Make sure your backend is running before using MCP tools")


if __name__ == "__main__":
    main()
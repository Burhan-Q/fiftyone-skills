#!/usr/bin/env python3
"""
Comprehensive test suite for fiftyone-skills package.

This script tests all functionality of the package including:
- CLI commands
- All agent types
- Local and global installation
- Update from GitHub
- Error handling
"""

import subprocess
import tempfile
import sys
from pathlib import Path


def run_command(cmd, cwd=None, timeout=60):
    """Run a command and return result."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        timeout=timeout
    )
    return result


def test_help():
    """Test help command."""
    print("Testing --help...")
    result = run_command(["fiftyone-skills", "--help"])
    assert result.returncode == 0, "Help command failed"
    assert "Install FiftyOne Skills" in result.stdout
    print("  ✓ Help command works")


def test_version():
    """Test version command."""
    print("Testing --version...")
    result = run_command(["fiftyone-skills", "--version"])
    assert result.returncode == 0, "Version command failed"
    assert "0.1.0" in result.stdout
    print("  ✓ Version command works")


def test_local_installation(agent="claude"):
    """Test local installation for a specific agent."""
    print(f"Testing local installation for {agent}...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_command(
            ["fiftyone-skills", "env=local", f"agent={agent}"],
            cwd=tmpdir
        )
        
        if result.returncode != 0:
            print(f"  ✗ Failed: {result.stderr}")
            return False
        
        # Determine expected directory
        if agent.lower() == "none":
            skills_dir = Path(tmpdir) / ".agents" / "skills"
        else:
            agent_dirs = {
                "claude": ".claude/skills",
                "cursor": ".cursor/skills",
                "codex": ".codex/skills",
                "copilot": ".github/copilot/skills"
            }
            skills_dir = Path(tmpdir) / agent_dirs[agent.lower()]
        
        if not skills_dir.exists():
            print(f"  ✗ Skills directory not created: {skills_dir}")
            return False
        
        skills = list(skills_dir.iterdir())
        if len(skills) == 0:
            print("  ✗ No skills installed")
            return False
        
        print(f"  ✓ Installed {len(skills)} skills to {skills_dir.relative_to(tmpdir)}")
        return True


def test_global_installation():
    """Test global installation path resolution."""
    print("Testing global installation path resolution...")
    
    # Import the module directly to test the path logic
    from fiftyone_skills import get_install_dir
    from pathlib import Path
    
    # Test that global installation uses home directory
    install_dir = get_install_dir("global", "claude")
    expected = Path.home() / ".claude" / "skills"
    
    if install_dir != expected:
        print(f"  ✗ Wrong path: {install_dir} != {expected}")
        return False
    
    # Test different agents
    for agent in ["cursor", "codex", "copilot"]:
        install_dir = get_install_dir("global", agent)
        if not str(install_dir).startswith(str(Path.home())):
            print(f"  ✗ Global path for {agent} doesn't use home: {install_dir}")
            return False
    
    # Test None agent
    install_dir = get_install_dir("global", None)
    expected = Path.home() / ".agents" / "skills"
    if install_dir != expected:
        print(f"  ✗ Wrong path for None: {install_dir} != {expected}")
        return False
    
    print(f"  ✓ Global installation path logic works")
    return True


def test_update_flag():
    """Test --update flag (downloads from GitHub)."""
    print("Testing --update flag...")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        result = run_command(
            ["fiftyone-skills", "env=local", "agent=claude", "--update"],
            cwd=tmpdir,
            timeout=120
        )
        
        if result.returncode != 0:
            print(f"  ✗ Failed: {result.stderr}")
            return False
        
        if "Downloading skills from" not in result.stdout:
            print("  ✗ No download message found")
            return False
        
        skills_dir = Path(tmpdir) / ".claude" / "skills"
        if not skills_dir.exists():
            print("  ✗ Skills directory not created")
            return False
        
        skills = list(skills_dir.iterdir())
        print(f"  ✓ Downloaded and installed {len(skills)} skills")
        return True


def test_error_handling():
    """Test error handling for invalid inputs."""
    print("Testing error handling...")
    
    # Test invalid env
    result = run_command(["fiftyone-skills", "env=invalid"])
    if result.returncode == 0:
        print("  ✗ Should fail with invalid env")
        return False
    if "env must be" not in result.stderr:
        print("  ✗ Wrong error message for invalid env")
        return False
    print("  ✓ Invalid env handled")
    
    # Test invalid agent
    result = run_command(["fiftyone-skills", "env=local", "agent=invalid"])
    if result.returncode == 0:
        print("  ✗ Should fail with invalid agent")
        return False
    if "agent must be one of" not in result.stderr:
        print("  ✗ Wrong error message for invalid agent")
        return False
    print("  ✓ Invalid agent handled")
    
    # Test invalid key
    result = run_command(["fiftyone-skills", "invalid_key=value"])
    if result.returncode == 0:
        print("  ✗ Should fail with invalid key")
        return False
    if "Unknown argument" not in result.stderr:
        print("  ✗ Wrong error message for invalid key")
        return False
    print("  ✓ Invalid key handled")
    
    # Test missing env
    result = run_command(["fiftyone-skills", "agent=claude"])
    if result.returncode == 0:
        print("  ✗ Should fail with missing env")
        return False
    if "env" not in result.stderr.lower():
        print("  ✗ Wrong error message for missing env")
        return False
    print("  ✓ Missing env handled")
    
    return True


def main():
    """Run all tests."""
    print("=" * 70)
    print("FiftyOne Skills Package - Comprehensive Test Suite")
    print("=" * 70)
    print()
    
    tests = [
        ("Help Command", test_help),
        ("Version Command", test_version),
        ("Local Installation (Claude)", lambda: test_local_installation("claude")),
        ("Local Installation (Cursor)", lambda: test_local_installation("cursor")),
        ("Local Installation (Codex)", lambda: test_local_installation("codex")),
        ("Local Installation (Copilot)", lambda: test_local_installation("copilot")),
        ("Local Installation (None)", lambda: test_local_installation("None")),
        ("Global Installation", test_global_installation),
        ("Update from GitHub", test_update_flag),
        ("Error Handling", test_error_handling),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        print(f"\n[{passed + failed + 1}/{len(tests)}] {name}")
        print("-" * 70)
        try:
            result = test_func()
            if result is None or result is True:
                passed += 1
            else:
                failed += 1
                print(f"  ✗ Test failed")
        except Exception as e:
            failed += 1
            print(f"  ✗ Exception: {e}")
    
    print()
    print("=" * 70)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 70)
    
    if failed > 0:
        print("\n❌ Some tests failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()

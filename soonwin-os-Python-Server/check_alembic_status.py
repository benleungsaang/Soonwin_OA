import subprocess
import sys
import os

# 首先尝试使用alembic直接查看状态
try:
    result = subprocess.run([
        sys.executable, "-m", "alembic", "history", "--verbose"
    ], cwd="migrations", capture_output=True, text=True, timeout=30)
    
    print("History command result:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
except subprocess.TimeoutExpired:
    print("Command timed out")
except Exception as e:
    print(f"Error running history command: {e}")

# 尝试检查当前状态
try:
    result = subprocess.run([
        sys.executable, "-m", "alembic", "current"
    ], cwd=".", capture_output=True, text=True, timeout=30)
    
    print("\nCurrent command result:")
    print("STDOUT:", result.stdout)
    print("STDERR:", result.stderr)
    print("Return code:", result.returncode)
except subprocess.TimeoutExpired:
    print("Command timed out")
except Exception as e:
    print(f"Error running current command: {e}")
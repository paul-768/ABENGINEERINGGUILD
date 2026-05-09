# clean_run.py
import os
import subprocess
import time

# Kill any existing processes
print("🔄 Stopping any existing servers...")
os.system('taskkill /f /im python.exe 2>nul')
time.sleep(2)

print("🚀 Starting clean server...")
os.system('python run.py')
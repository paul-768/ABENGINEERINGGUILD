# start_app.py
import os
import sys
import subprocess
import time
import signal

def kill_existing_process(port=5000):
    """Kill any existing process on port 5000"""
    try:
        # For Windows
        if os.name == 'nt':
            result = subprocess.run(
                ['netstat', '-ano', '|', 'findstr', f':{port}'],
                capture_output=True, text=True, shell=True
            )
            if result.stdout:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if f':{port}' in line:
                        parts = line.split()
                        pid = parts[-1]
                        subprocess.run(['taskkill', '/F', '/PID', pid])
                        print(f"✅ Killed process {pid} on port {port}")
                        time.sleep(2)
        else:
            # For Linux/Mac
            subprocess.run(['fuser', '-k', f'{port}/tcp'])
    except Exception as e:
        print(f"Note: {e}")

def main():
    print("🚀 Starting AgriQuest Application...")
    
    # Step 1: Kill any existing process
    print("1. Checking for existing processes...")
    kill_existing_process(5000)
    
    # Step 2: Fix database migration
    print("2. Applying database fixes...")
    try:
        from fix_migration import fix_database
        fix_database()
    except Exception as e:
        print(f"Database fix skipped: {e}")
    
    # Step 3: Start the application
    print("3. Starting Flask application...")
    os.system("python run.py")

if __name__ == "__main__":
    main()
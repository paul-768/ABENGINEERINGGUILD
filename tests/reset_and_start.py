# reset_and_start.py
import os
import subprocess
import time

def main():
    print("🔄 Nuclear reset and start...")
    
    # Kill all Python processes (be careful with this)
    if os.name == 'nt':  # Windows
        os.system('taskkill /f /im python.exe 2>nul')
        os.system('taskkill /f /im flask.exe 2>nul')
    else:  # Linux/Mac
        os.system('pkill -f python 2>/dev/null')
        os.system('pkill -f flask 2>/dev/null')
    
    time.sleep(2)
    
    # Apply database fix
    print("🔧 Fixing database...")
    os.system('python fix_migration.py')
    
    # Start app
    print("🚀 Starting application...")
    os.system('python run.py')

if __name__ == "__main__":
    main()
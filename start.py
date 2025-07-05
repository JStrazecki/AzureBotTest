# start.py
import subprocess
import sys
import os

# Set up the environment
os.environ['PORT'] = os.environ.get('PORT', '8000')

# Start gunicorn
subprocess.run([
    sys.executable, '-m', 'gunicorn',
    '--bind', f"0.0.0.0:{os.environ['PORT']}",
    '--worker-class', 'aiohttp.GunicornWebWorker',
    '--timeout', '600',
    '--workers', '1',
    'app:APP'
])
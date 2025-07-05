#!/bin/bash
# startup.sh
echo "Starting SQL Assistant Bot..."
cd /home/site/wwwroot

# Extract tar.gz if it exists
if [ -f output.tar.gz ]; then
    echo "Extracting output.tar.gz..."
    tar -xzf output.tar.gz
fi

# Set up environment with all the paths we discovered
export LD_LIBRARY_PATH="/tmp/oryx/platforms/python/3.11.12/lib:$LD_LIBRARY_PATH"
export PATH="/tmp/oryx/platforms/python/3.11.12/bin:/home/.local/bin:$PATH"
export PYTHONPATH="/home/site/wwwroot:/home/.local/lib/python3.11/site-packages:/home/site/wwwroot/antenv/lib/python3.11/site-packages:$PYTHONPATH"

# Use the full Python path that works
exec /tmp/oryx/platforms/python/3.11.12/bin/python3.11 -m gunicorn --bind 0.0.0.0:8000 --worker-class aiohttp.GunicornWebWorker --timeout 600 --workers 1 app:APP
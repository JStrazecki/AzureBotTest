# startup.sh
#!/bin/bash
cd /home/site/wwwroot
export LD_LIBRARY_PATH="/tmp/oryx/platforms/python/3.11.12/lib:$LD_LIBRARY_PATH"
export PYTHONPATH="/home/site/wwwroot/antenv/lib/python3.11/site-packages:/home/site/wwwroot:$PYTHONPATH"
exec python -m gunicorn --bind 0.0.0.0:8000 --worker-class aiohttp.GunicornWebWorker --timeout 600 --workers 1 app:APP
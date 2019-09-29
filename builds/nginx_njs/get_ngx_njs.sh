#!/bin/sh
echo 'Building dockerfile'
docker build -t karstenf/endpoint_monitor:latest . 
echo 'Running dockerfile'
docker run --name endpointContainerKF -d karstenf/endpoint_monitor:latest
sleep 40s
RUNING=$(docker inspect -f '{{.State.Running}}' endpointContainerKF)
while [ $RUNING = true ]; do
    echo 'Container not finished running, sleeping for 10 seconds'
    sleep 10s
    RUNING=$(docker inspect -f '{{.State.Running}}' endpointContainerKF)
done
docker cp endpointContainerKF:/nginx-1.14.1/objs/ngx_http_js_module.so .
docker rm endpointContainerKF 
if [ -f ./ngx_http_js_module.so ]; then
    echo 'Container removed, ngx_http_js_module.so file copied to current directory'
else
    echo 'Container removed, ngx_http_js_module.so failed to copy to current directory'
fi

af=/var/opt/streams-endpoint-monitor/job-configs/actions
echo 'Starting action reader for' ${af}
(
while true
do
    if [[ ! -p ${af} ]]; then
        sleep 1
        continue
    fi

    if read line < ${af}; then
        nginx -s "${line}"
    fi
done
) &

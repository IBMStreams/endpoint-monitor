SECRET_HTACCESS=/var/run/secrets/streams-endpoint-monitor/server-auth/.htaccess
if  -f "${SECRET_HTACCESS}" ]; then
    /bin/cp \
        /opt/app-root/src/nginx-optional-cfg/auth_basic.conf \
        /var/opt/streams-endpoint-monitor/authentication.basic.conf
fi

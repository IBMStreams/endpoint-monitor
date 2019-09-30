#!/bin/sh

# Download the neccessary files
wget https://nginx.org/download/nginx-1.14.1.tar.gz
wget https://ftp.pcre.org/pub/pcre/pcre-8.43.tar.gz
wget https://www.zlib.net/zlib-1.2.11.tar.gz
wget https://github.com/nginx/njs/archive/0.3.5.tar.gz

# Unpack the files
tar -xzvf nginx-1.14.1.tar.gz
tar -xzvf pcre-8.43.tar.gz
tar -xzvf zlib-1.2.11.tar.gz
tar -xzvf 0.3.5.tar.gz

# Build the PCRE library
cd  pcre-8.43
./configure
make
make install

# Build the ngx_http_js_module.so file
cd ../nginx-1.14.1/
make clean
./configure --with-pcre=../pcre-8.43/ --with-zlib=../zlib-1.2.11 \
    --add-dynamic-module=../njs-0.3.5/nginx/ \
    --with-file-aio \
    --with-http_ssl_module \
    --with-http_realip_module \
    --with-http_dav_module \
    --with-cc-opt='-DNGX_HTTP_HEADERS'
make modules

#!/bin/sh

# Download the neccessary files
wget http://nginx.org/download/nginx-1.14.0.tar.gz
wget https://ftp.pcre.org/pub/pcre/pcre-8.43.tar.gz
wget https://www.zlib.net/zlib-1.2.11.tar.gz
git clone https://github.com/nginx/njs.git

# Unpack the files
tar -xzvf nginx-1.14.0.tar.gz
tar -xzvf pcre-8.43.tar.gz
tar -xzvf zlib-1.2.11.tar.gz

# Build the PCRE library
cd  pcre-8.43
./configure
make
make install

# Build the ngx_http_js_module.so file
cd ../nginx-1.14.0/
make clean
./configure --with-compat --with-pcre=../pcre-8.43/ --with-zlib=../zlib-1.2.11 --add-dynamic-module=../njs/nginx/
make modules
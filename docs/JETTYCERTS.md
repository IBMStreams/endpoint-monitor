# Streams endpoints certificates

## Overview

The endpoints running within a Streams job are Jetty web servers and can be configured to support HTTP or HTTPS.

**When using HTTP there is no authentication and no encryption** between the Nginx server that is the endpoint-monitor's reverse proxy and the Jetty web servers. This means the Jetty web servers are open to any pod within the same cluster namespace. **Use of HTTP is not recommended** but may be suitable for demos, PoCs or controlled environments where performance may be a concern.

**HTTPS is recommended** and is configured by creating a Kubernetes generic secret that defines certificates for Jetty servers. Endpoint-monitor configures Nginx to use the certificates when communicating with the Jetty servers and creates a Streams application configuration that provides the certificates to the Jetty servers. The Streams application configures the endpoints with the monitor name ([Python](https://github.com/IBMStreams/endpoint-monitor/blob/master/README.md#python-topology-applications)) or application configuration name ([SPL](https://github.com/IBMStreams/endpoint-monitor/blob/master/README.md#spl-applications) to enable HTTPS.

A single instance of endpoint-monitor supports HTTP and HTTPS endpoints concurrently.

## Certificates secret

The certificates used for HTTPS between Nginx and Jetty web-servers are defined in a Kubernetes generic secret with name  `${NAME}-streams-certs` (see [Setup](https://github.com/IBMStreams/endpoint-monitor#setup)) e.g. `buses-em-streams-certs`.

The secret must contain these keys and values:

* `client.pfx` - Client certificate & key used by Nginx server to connect to Jetty web servers.
* `server.jks` - Java key store containing the server certificate (alias `emrestops`) for the Jetty web servers
* `cacerts.jks` - Java trust store containing the client certificates trusted by the Jetty web servers (including the certificate from `client.pfx`) 
* `server.pass` - Password for `server.jks` (and its key) and `cacerts.jks`.
* `client.pass` - Password for `client.pfx`

Note these certificates are for Niginx (the *client*) connecting to the Jetty web servers (the *server*).

An example script to create a secret of the correct layout is in https://github.com/IBMStreams/endpoint-monitor/blob/master/scripts/build_jetty_certs.sh

## Application configuration

When endpoint-monitor runs it creates/updates a corresponding Streams application configuration called `${NAME}-streams-certs` with these properties:

* `server.jks` - Base 64 encoded representation of the Java key store from the secret.
* `cacerts.jks` - Base 64 encoded representation of the Java trust store from the secret.
* `server.pass` - Password for `server.jks` (and its key) and `cacerts.jks`.

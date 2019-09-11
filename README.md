# endpoint-monitor
Nginx reverse proxy sample application to Streams REST operators.

# UNDER DEVELOPMENT

**Application is under development, apis, behavior etc. are subject to change.**

# Overview

Endpoint-monitor is an Openshift application that monitors running jobs in a single Streams instance (within the same cluster) for REST SPL operators, such as `com.ibm.streamsx.inet.rest::HTTPJSONInjection` and `com.ibm.streamsx.inet.rest::HTTPTupleView`.

The endpoints from the REST operators are then exposed with fixed URLs through a service using an Nginx reverse proxy. Thus if a PE hosting a REST operator restarts and changes its IP address and/or server port number endpoint-monitor will update the nginx configuration to allow the fixed URL to find the operator correctly.

# Setup

1. Using an Openshift cluster run `oc new-app` to build and deploy the *endpoint-moinitor* application:

```
oc new-app \
 -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/master/openshift/templates/streams-endpoints.json -p NAME=<application-name>
```

2. Define the Streams instance to be monitored.

In the deployment configuration for *application-name* add the environment variable ``STREAMS_ENDPOINT_INSTANCE_URL`` to the container streams-endpoint-monitor.


3. Create a kubernetes secret that identifies a Streams instance user that has authorization to view job information through the Streams REST api:

 * `STREAMS_USERNAME` - User identifier for Streams user.
 * `STREAMS_PASSWORD` - Password for Streams user.
 
 <img width="236" alt="image" src="https://user-images.githubusercontent.com/3769612/64719622-7d516e80-d47d-11e9-9cb3-c90bc4406de5.png">

4. Add the secret from step 3. to the environment of container streams-endpoint-monitor in the deployment configuration for *application-name*.

After steps 2,3,4 the configuration for container streams-endpoint-monitor should look like:

<img width="1244" alt="image" src="https://user-images.githubusercontent.com/3769612/64719577-5e52dc80-d47d-11e9-97d3-cada3f817525.png">

# URL mapping

Current support is limited to:

 * HTTP operators only
 * Single web-server per job
     * The web-server can be hosting multiple REST operators that are fused into a single PE
 * Port number should be zero or a non-system port.

For a web-server in a job its URLs are exposed with prefix path:

 * `streams/job/`*jobid*`/`
 
 (plan is to support job names as the fixed path).
 
 For example with a web-server in job 7:
 
 * `streams/job/7/ports/info`
 
 The path is against the service *application-name*.



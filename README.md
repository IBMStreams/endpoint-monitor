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
 -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/master/openshift/templates/streams-endpoints.json \
 -p NAME=<application-name> \
 -p STREAMS_INSTANCE_NAME=<IBMStreamsInstance name> \
 -p JOB_GROUP=<job group pattern>
```

* `NAME` - Name of the openshift/kubernetes service that provides access to the REST endpointd
* `STREAMS_INSTANCE_NAME` - Name of the Kubernetes object `IBMStreamsInstance` defined in the yaml file when creating the Streams instance.
* `JOB_GROUP` - Job group pattern. Only jobs with groups that match this pattern will be monitored for REST operators. **Currently only a actual job group can be supplied, not a regular expression.**

The containers in the created pods (once the builds complete) will fail until steps 2,3,4 are completed. There is no additional action required after steps 2,3,4 , Openshift will restart the pod due to the change in configuraiton.

2. Create a kubernetes secret that identifies a Streams instance user that has authorization to view job information for the selected job group(s) through the Streams REST api:

 * `STREAMS_USERNAME` - User identifier for Streams user.
 * `STREAMS_PASSWORD` - Password for Streams user.
 
 <img width="236" alt="image" src="https://user-images.githubusercontent.com/3769612/64719622-7d516e80-d47d-11e9-9cb3-c90bc4406de5.png">

3. Add the secret from step 3. to the environment of container streams-endpoint-monitor in the deployment configuration for *application-name*.

After steps 2,3 the configuration for container streams-endpoint-monitor should look like:

_image is out of date - the environment variable is now STREAMSX_ENDPOINT_INSTANCE and is set automatically_

<img width="1244" alt="image" src="https://user-images.githubusercontent.com/3769612/64719577-5e52dc80-d47d-11e9-97d3-cada3f817525.png">

# URL mapping

Current support is limited to:

 * HTTP & HTTPS operators
 * Single web-server per job
     * The web-server can be hosting multiple REST operators that are fused into a single PE
 * Port number should be zero or a non-system port.
 * Currently all jobs are monitored for endpoints, job filtering will be added.

For a web-server in a job its URLs are exposed with prefix path:

 * `streams/job/`*jobid*`/`
 
 (plan is to support job names as the fixed path).
 
 For example with a web-server in job 7:
 
 * `streams/job/7/ports/info`
 
 The path is against the service *application-name*.

# Implementation notes

The template uses the nginx and python 3.6 source to image (s2i) setups to define two containers (nginx & python) within a single pod. The two containers share a local volume (`/opt/streams_job_configs`) and communicate through a named pipe on the volume.
 * nginx 1.12 s2i - https://github.com/sclorg/nginx-container/tree/master/1.12
 * python 3.6 s2i - tbd

The python container monitors the Streams instance using the REST api through its sws service and as jobs are submitted and canceled it updates each job's reverse proxy configuration in `/opt/streams_job_configs`. Once a job configuration has been written it sends a `reload` action through the named pipe.

The nginx container runs nginx pulling configuration from job endpoint `/opt/streams_job_configs/*.conf`. It also has a shell script that monitors the named pipe and executes its actions using `nginx -s`, e.g. `nginx -s reload`. (currently only `reload` is sent as an action).

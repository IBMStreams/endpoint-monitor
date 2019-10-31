## endpoint-monitor OpenShift application

Nginx reverse proxy sample application to Streams REST endpoints.

# UNDER DEVELOPMENT

**Application is under development, apis, behavior etc. are subject to change.**

## Overview

Endpoint-monitor is an Openshift application that monitors running jobs in a single Streams Cloud Pak for Data instance (within the same cluster and namespace) for REST endpoints, such as injection of tuples from a REST POST into a stream.
Streams Cloud Pak for Data integrated and standalone instances are supported.

The endpoints from the REST operators are then exposed with fixed URLs through a service using an Nginx reverse proxy. Thus if a PE hosting a REST operator restarts and changes its IP address and/or server port number endpoint-monitor will update the nginx configuration to allow the fixed URL to find the operator correctly.

## Streams application endpoints

The Streams application containing endpoints must be submitted to a job group that the endpoint-monitor is configured to monitor. See Setup.

### Python topology applications

Endpoints are supported by the `streamsx.endpoint` package, installable from pip:

   * PyPi - https://pypi.org/project/streamsx.endpoint/
   * Documentation - https://streamsxendpoint.readthedocs.io
   
Example of an application endpoint that supports HTTP POST requests that insert the body of the POST as JSON into the stream as a single tuple.

```
from streamsx.topology.topology import Topology
import streamsx.endpoint as endpoint

topo = Topology()

positions = endpoint.inject(topo, context='vehicles', name='position', monitor='buses-em')
```

### SPL applications

Endpoints are instances of the REST operators from the [com.ibm.streamsx.inetserver](https://ibmstreams.github.io/streamsx.inetserver/) toolkit.

The operators should be configured with these parameters:
 * `port: 0` - Uses a port from the ephemeral range, ensures multiple rest operators within the same PE share a Jetty server.
 * `context:` *context* - Context lead in for the exposed paths. Ensures the paths remain fixed regardless of SPL application changes, such as refactoring into multiple composites.
 * `sslAppConfigName:` *${NAME}*`-streams-certs` - Optional - set if connections between the endpoint-monitor and the Streams endpoints must use HTTPS/SSL. `${NAME}` is the name of the endpoint-monitor application, see Setup.

All REST operators within the application must use the same settings for `port` (0) and `sslAppConfigName` which ensures
operators fused into the same PE share a single Jetty server. Only a single Jetty server is supported per-PE.

Multiple Jetty servers within the same job are supported, by means of the REST operators being in multiple PEs. Thus for example an injection operator as the source of the application need not be fused with an instance of `HTTPTupleView` at the end of the graph.

Endpoint-monitor creates shortened paths for these operators in `com.ibm.streamsx.inet.rest` namespace:

* `HTTPJSONInjection`
   * *context*/*name*/`inject` - Injection of tuples to output port 0
* `HTTPTupleInjection`
   * *context*/*name*/`inject` - Injection of tuples to output port 0
   * *context*/*name*/`form` - Simple HTML form to injecti tuples to output port 0
* `HTTPTupleView`
   * *context*/*name*/`tuples` - Access to tuples exposed by the operator

For example with an endpoint-monitor name `buses-em` this is the URL  for an injection endpoint with context `buses`, name `locations` in in job named `transit`:

``https://buses-em.myproject.svc:8443/transit/buses/locations/inject``

The corresponding SPL code for the operator would be:

```
stream<Json> locations = com.ibm.streamsx.inet.rest::HTTPJSONInjection() {
    param
       port: 0;
       context: 'buses';
       sslAppConfigName: 'buses-em-streams-certs';
}
```

## Setup

Pick a name for the application (e.g. `buses-em`), this will be passed to *oc new-app* as the parameter `NAME` and will also be the name of the Kubernetes service exposes the REST endpoints. This name is referred to a `${NAME}` in the following steps.

1. Create a kubernetes generic secret that identifies a Streams instance user that has authorization to view job information for the selected job group(s) through the Streams REST api:

 * `STREAMS_USERNAME` - User identifier for Streams user.
 * `STREAMS_PASSWORD` - Password for Streams user.
 
 <img width="236" alt="image" src="https://user-images.githubusercontent.com/3769612/64719622-7d516e80-d47d-11e9-9cb3-c90bc4406de5.png">

The name of the secret is used in step 4 as the `STREAMS_USER_SECRET` parameter.

2. If your `openshift` project does not contain the image `nginx:1.14` then add it using.

```
oc login system:admin
oc project openshift
oc tag docker.io/centos/nginx-114-centos7:latest nginx:1.14
```

If you your image streams are in different namespace to `openshift` then use that as the project and set the `NAMESPACE`
parameter when invoking `oc new-app`.

3. Optional - Create a kubernetes generic secret that defines authentication for the endpoint-monitor service.

The name of the secret is `${NAME}-authentication` e.g. `buses-em-authentication`.

For signature verification of POST, PUT, PATCH requests create the property `signature-secret` with the value of secret.
(See #8 for details of signature).

<img width="394" alt="image" src="https://user-images.githubusercontent.com/3769612/65935654-b6229a80-e3ce-11e9-92ff-a13ace0f7cf6.png">

4. Optional - Create a kubernetes generic secret that defines certificates for Streams Jetty operators

This step allows HTTPS between nginx and the Streams operators.

The name of the secret is `${NAME}-streams-certs` e.g. `buses-em-streams-certs`.

See issue #30 for details on this work in progress


5. Using an Openshift cluster run `oc new-app` to build and deploy the *endpoint-monitor* application:

```
oc new-app \
 -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/master/openshift/templates/streams-endpoints.json \
 -p NAME=<application-name> \
 -p STREAMS_INSTANCE_NAME=<IBMStreamsInstance name> \
 -p JOB_GROUP=<job group pattern> \
 -p STREAMS_USER_SECRET=<streams user secret>
```

* `NAME` - Name of the openshift/kubernetes service that provides access to the REST endpointd
* `STREAMS_INSTANCE_NAME` - Name of the Kubernetes object `IBMStreamsInstance` defined in the yaml file when creating the Streams instance.
* `JOB_GROUP` - Job group pattern. Only jobs with groups that match this pattern will be monitored for REST operators. **Currently only a actual job group can be supplied, not a regular expression.**
* `STREAMS_USER_SECRET` - Name of the secret from step 1, defaults to `streams-user`.

## URL mapping

For a web-server in a job its URLs are exposed with prefix path:

 * *jobname*`/` - When a job name was explictly set. Job names should be simple mapping to a single path element.
 * `streams/jobs/`*jobid*`/` - When a job name was not explicitly set.

The path is against the service *application-name* (``${NAME}``)
 
Example URLs within the cluster for *application-name* of `buses-em` in project `myproject` are:
 
 * `https://buses-em.myproject.svc:8443/transit/ports/info`for a job named `transit`:
 * `https://buses-em.myproject.svc:8443/streams/jobs/7/ports/info` for job 7 without an explicitly set job name:
 * `https://buses-em.myproject.svc:8443/transit/buses/locations/inject` for an injection endpoint with context `buses`, name `locations` in in job named `transit`.
 
## Implementation notes

The template uses the nginx and python 3.6 source to image (s2i) setups to define two containers (nginx & python) within a single pod. The two containers share a local volume (`/opt/streams_job_configs`) and communicate through a named pipe on the volume.
 * nginx 1.14 s2i - https://github.com/sclorg/nginx-container/tree/master/1.14
 * python 3.6 s2i - tbd

The python container monitors the Streams instance using the REST api through its sws service and as jobs are submitted and canceled it updates each job's reverse proxy configuration in `/opt/streams_job_configs`. Once a job configuration has been written it sends a `reload` action through the named pipe.

 * `https://em.myoproject.svc:8443/streams/jobs/7/ports/info` with a web-server in job 7:


The nginx container runs nginx pulling configuration from job endpoint `/opt/streams_job_configs/*.conf`. It also has a shell script that monitors the named pipe and executes its actions using `nginx -s`, e.g. `nginx -s reload`. (currently only `reload` is sent as an action).

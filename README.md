## endpoint-monitor OpenShift application

Nginx reverse proxy sample application to Streams REST endpoints.

## Overview

Endpoint-monitor is an Openshift application that monitors running jobs in a single Streams Cloud Pak for Data instance (within the same cluster and namespace) for RESTful endpoints, such as injection of tuples from a REST POST into a stream, and exposes them through a OpenShift Nginx service.

Streams Cloud Pak for Data (3.0) integrated and standalone instances are supported.

This then bridges the gap between traditional HTTP RESTful microservices and streaming applications. A RESTful microservice can inject tuples into a stream, access the contents of windows etc.

The endpoints are exposed with fixed URLs through a Kubernetes service using an Nginx reverse proxy. If a PE hosting an endpoint (REST operator) restarts and changes its IP address and/or server port number, endpoint-monitor will update the nginx configuration to allow the fixed URL to find the operator correctly.

The endpoint service is available within the cluster and may be exposed outside of the cluster using standard Openshift/Kubernetes techniques, such as `oc expose`. For webhook use by other services the service must be reachable through a public internet address.

Multiple endpoint-monitors can be running against a single Streams instance, for example one that exposes endpoints to applications within the cluster and one that exposes a limited set of endpoints externally. Separation is provided through
Streams job groups, e.g. the internal monitor might be monitoring jobs in the `green` job group while the external is monitoring the `red` job group.

Here's a diagram showing the interaction of clients, endpoint-monitor and Streams jobs.

<img width="932" alt="image" src="https://user-images.githubusercontent.com/3769612/68225608-8b1b0000-ffa5-11e9-895e-331a0acebb51.png">

## Streams application endpoints

The Streams application containing endpoints must be submitted to a job group that the endpoint-monitor is configured to monitor. See Setup.

### Python topology applications

Endpoints are supported by the `streamsx.endpoint` package, installable from pip:

   * PyPi - https://pypi.org/project/streamsx.endpoint/
   * Documentation - https://streamsxendpoint.readthedocs.io
   
Example of an application endpoint that supports HTTPS POST requests that insert the body of the POST as JSON into the stream as a single tuple.

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

All REST operators within the application **must use the same settings** for `port` (0) and `sslAppConfigName` which ensures
operators fused into the same PE share a single Jetty server. Only a single Jetty server is supported per-PE.

Multiple Jetty servers within the same job are supported, by means of the REST operators being in multiple PEs. Thus for example an injection operator as the source of the application need not be fused with an instance of `HTTPTupleView` at the end of the graph.

Endpoint-monitor creates shortened paths for these operators in `com.ibm.streamsx.inet.rest` namespace:

* `HTTPJSONInjection`
   * *context*/*name*/`inject` - Injection of tuples to output port 0
* `HTTPTupleInjection`
   * *context*/*name*/`inject` - Injection of tuples to output port 0
   * *context*/*name*/`form` - Simple HTML form to inject tuples to output port 0
* `HTTPTupleView`
   * *context*/*name*/`tuples` - Access to tuples exposed by the operator

For example with an endpoint-monitor name `buses-em` this is the URL for an injection endpoint with context `buses`, name `locations` in in job named `transit`:

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

**Tip**: You can run the `setupProxy.sh` script which has automated these steps. The only step you would need to do manually is create the job group in the Streams Console.


Pick a name for the application (e.g. `buses-em`), this will be passed to *oc new-app* as the parameter `NAME` and will also be the name of the Kubernetes service exposing the REST endpoints.

This name is referred to a `${NAME}` in the following steps.

The service is an Nginx HTTPS server on port 8443, for example its service URL within the cluster would be
`https://buses-em.myproject.svc:8443`.

HTTPS is the only supported protocol for clients connecting to the Nginx service. The server certificate is obtained from the cluster using this technique: https://docs.openshift.com/container-platform/3.6/dev_guide/secrets.html#service-serving-certificate-secrets

### 1. Define Streams user

Create a kubernetes generic secret that identifies a Streams instance user that has authorization to:
 * view job information for the selected job group(s) through the Streams REST api
 * create Streams application configurations that can be read by Streams users submitting jobs to the selected job group(s).

The secret must contain these two keys and values:

 * `STREAMS_USERNAME` - User identifier for Streams user.
 * `STREAMS_PASSWORD` - Password for Streams user.
 
 <img width="236" alt="image" src="https://user-images.githubusercontent.com/3769612/64719622-7d516e80-d47d-11e9-9cb3-c90bc4406de5.png">

You can use the following command sequence to create the secret:
```
echo -n '<username>' > user.txt
echo -n '<password>' > passwd.txt
kubectl create secret generic streams-user --from-file=STREAMS_USERNAME=./user.txt --from-file=STREAMS_PASSWORD=./passwd.txt
rm user.txt passwd.txt
```

The name of the secret is used in step 5 as the `STREAMS_USER_SECRET` parameter.

### 2. Define images

If your `openshift` project does not contain the image `nginx:1.14` or the python:3.6 images then add either of them  using:

```
oc login system:admin
oc project openshift
oc tag docker.io/centos/nginx-114-centos7:latest nginx:1.14
oc tag docker.io/centos/python-36-centos7:latest python:3.6 

```

If image `nginx:1.14` is not in project `openshift`, make sure that one project contains the image.
If you your image streams are in different namespace to `openshift` then use that as the project and set the `NAMESPACE`
parameter when invoking `oc new-app`.

### 3. Endpoint service authentication

By default the endpoint-monitor's RESTful service **does not require authentication**, authentication is enabled by creating a Kubernetes generic secret that configures authentication mechanisms. The name of the secret is `{$NAME}-authentication`, e.g. `buses-em-authentication`.

#### Basic authentication

Basic authentication can be configured for all requests.

Click here to see details on [basic authentication](https://github.com/IBMStreams/endpoint-monitor/blob/develop/docs/BASICAUTH.md)

#### Webhook signature authentication

Requests with a body can be authenticated using a signature and a shared secret.

Click here to see details on [enabling signature authentication](https://github.com/IBMStreams/endpoint-monitor/blob/develop/docs/signature_auth.md)

Signature authentication can be an additional layer to other authentication mechanisms, such as basic authenication.

### 4. Define HTTPS certificates used by Streams applications

Optional - Create a kubernetes generic secret `${NAME}-streams-certs` that defines certificates to enable HTTPS between the Nginx reverse proxy and the endpoints within the Streams jobs.

Click here to see details on [creating the certificates secret](https://github.com/IBMStreams/endpoint-monitor/blob/develop/docs/JETTYCERTS.md).

### 5. Deploy application

#### Create a job group in the Streams instance first

From the Streams console application dashboard, open the menu, expand the instance, select Job Groups, and  click **Make job group**. Provide a name, such as "WebApps".

Using an Openshift cluster run `oc new-app` to build and deploy the *endpoint-monitor* application. Use the same project where the streams is installed.
The following command creates a *endpoint-monitor* application with name *streams-endpoint-monitor*

```
oc new-app \
 -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/develop/openshift/templates/streams-endpoints.json \
 -p STREAMS_INSTANCE_NAME=<IBMStreamsInstance name> \
 -p JOB_GROUP=<job group> \
```

* `STREAMS_INSTANCE_NAME` - Name of the Kubernetes object `IBMStreamsInstance` defined in the yaml file when creating the Streams instance.
* `JOB_GROUP` - Job group name. Only jobs submitted to the specified group will be monitored for REST operators. **Currently only a actual job group can be supplied, not a regular expression.** 

The command may be used with additional parameters:
* `NAME` - Name of the openshift/kubernetes service that provides access to the REST endpoint, defaults to `streams-endpoint-monitor`
* `STREAMS_USER_SECRET` - Name of the secret from step 1, defaults to `streams-user`.
* `NAMESPACE` - The OpenShift Namespace where the ImageStream resides, defaults to `openshift`
* `SOURCE_REPOSITORY_URL` - The URL of the repository with your application source code, defaults to `https://github.com/IBMStreams/endpoint-monitor`

### 6. Create a Route

Create a route where the service is exposed. Use the Openshift Console and use menu:
```
Networking -> Routes -> Create Route
```
Choose your created service with `${NAME}` and choose as TLS Termination `Passthrough`.
Public hostname for the route. If not specified, a hostname is generated.

## URL mapping

For a web-server in a job its URLs are exposed with prefix path:

 * *jobname*`/` - When a job name was explictly set. Job names should be simple mapping to a single path element.
 * `streams/jobs/`*jobid*`/` - When a job name was not explicitly set.

The path is against the service *application-name* (``${NAME}``)
 
Example URLs within the cluster for *application-name* of `buses-em` in project `myproject` are:
 
 * `https://buses-em.myproject.svc:8443/transit/ports/info`for a job named `transit`:
 * `https://buses-em.myproject.svc:8443/streams/jobs/7/ports/info` for job 7 without an explicitly set job name:
 * `https://buses-em.myproject.svc:8443/transit/buses/locations/inject` for an injection endpoint with context `buses`, name `locations` in in job named `transit`.

To acces the service from the outside, use the genereated hostname of the route.
 
## Swagger - EXPERIMENTAL

The path `swagger-ui.html` (e.g. `https://buses-em.myproject.svc:8443/swagger-ui.html`) provides [Swagger UI](https://swagger.io/tools/swagger-ui) to visualize and interact with the endpoints. An OpenAPI specification (Swagger) is provided for each monitored job at:

 * `swagger-defs/`*jobname*.json - When a job name is explicitly set
 * `swagger-defs/`*jobid*`.json` - When a job name was not explicitly set
 
 The OpenAPi specification is generated based upon the job and its endpoints.
 
 ***Generation may only be supported for a limited number of endpoints.***

## Implementation notes

The template uses the nginx and python 3.6 source to image (s2i) setups to define two containers (nginx & python) within a single pod. The two containers share a local volume (`/opt/streams_job_configs`) and communicate through a named pipe on the volume.
 * nginx 1.14 s2i - https://github.com/sclorg/nginx-container/tree/master/1.14
 * python 3.6 s2i - https://github.com/sclorg/s2i-python-container/tree/master/3.6

The python container monitors the Streams instance using the REST api through its sws service and as jobs are submitted and canceled it updates each job's reverse proxy configuration in `/opt/streams_job_configs`. Once a job configuration has been written it sends a `reload` action through the named pipe.

 * `https://em.myoproject.svc:8443/streams/jobs/7/ports/info` with a web-server in job 7:


The nginx container runs nginx pulling configuration from job endpoint `/opt/streams_job_configs/*.conf`. It also has a shell script that monitors the named pipe and executes its actions using `nginx -s`, e.g. `nginx -s reload`. (currently only `reload` is sent as an action).

Click here to see the internal details on how [signature authentication](https://github.com/IBMStreams/endpoint-monitor/blob/develop/docs/internal/signature_verification.md) works

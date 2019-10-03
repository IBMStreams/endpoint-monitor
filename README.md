# endpoint-monitor
Nginx reverse proxy sample application to Streams REST operators.

# UNDER DEVELOPMENT

**Application is under development, apis, behavior etc. are subject to change.**

# Overview

Endpoint-monitor is an Openshift application that monitors running jobs in a single Streams instance (within the same cluster) for REST SPL operators, such as `com.ibm.streamsx.inet.rest::HTTPJSONInjection` and `com.ibm.streamsx.inet.rest::HTTPTupleView`.

The endpoints from the REST operators are then exposed with fixed URLs through a service using an Nginx reverse proxy. Thus if a PE hosting a REST operator restarts and changes its IP address and/or server port number endpoint-monitor will update the nginx configuration to allow the fixed URL to find the operator correctly.

# Setup

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

3. Optional - Create a kubernetes secret that defines authentication for the endpoint-monitor service.

The name of the secret is `<application-name>-authentication` e.g. `em-authentication`.

For signature verification of POST, PUT, PATCH requests create the property `signature-secret` with the value of secret.
(See #8 for details of signature).

<img width="394" alt="image" src="https://user-images.githubusercontent.com/3769612/65935654-b6229a80-e3ce-11e9-92ff-a13ace0f7cf6.png">


4. Using an Openshift cluster run `oc new-app` to build and deploy the *endpoint-monitor* application:

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

# URL mapping

Current support is limited to:

 * HTTP & HTTPS operators
 * Single web-server per job
     * The web-server can be hosting multiple REST operators that are fused into a single PE
 * Port number should be zero or a non-system port.

For a web-server in a job its URLs are exposed with prefix path:

 * *jobname*`/` - When a job name was explictly set. Job names should be simple mapping to a single path element.
 * `streams/jobs/`*jobid*`/` - When a job name was not explicitly set.

The path is against the service *application-name*
 
Example URLs within the cluster for *application-name* of `em` in project `myproject` are:
 
 * `https://em.myproject.svc:8443/transit/ports/info` with a web-server in job named `transit`:
 * `https://em.myproject.svc:8443/streams/jobs/7/ports/info` with a web-server in job 7:
 

# Implementation notes

The template uses the nginx and python 3.6 source to image (s2i) setups to define two containers (nginx & python) within a single pod. The two containers share a local volume (`/opt/streams_job_configs`) and communicate through a named pipe on the volume.
 * nginx 1.12 s2i - https://github.com/sclorg/nginx-container/tree/master/1.12
 * python 3.6 s2i - tbd

The python container monitors the Streams instance using the REST api through its sws service and as jobs are submitted and canceled it updates each job's reverse proxy configuration in `/opt/streams_job_configs`. Once a job configuration has been written it sends a `reload` action through the named pipe.

 * `https://em.myoproject.svc:8443/streams/jobs/7/ports/info` with a web-server in job 7:
 

# Implementation notes

The template uses the nginx and python 3.6 source to image (s2i) setups to define two containers (nginx & python) within a single pod. The two containers share a local volume (`/opt/streams_job_configs`) and communicate through a named pipe on the volume.
 * nginx 1.12 s2i - https://github.com/sclorg/nginx-container/tree/master/1.12
 * python 3.6 s2i - tbd

The python container monitors the Streams instance using the REST api through its sws service and as jobs are submitted and canceled it updates each job's reverse proxy configuration in `/opt/streams_job_configs`. Once a job configuration has been written it sends a `reload` action through the named pipe.

The nginx container runs nginx pulling configuration from job endpoint `/opt/streams_job_configs/*.conf`. It also has a shell script that monitors the named pipe and executes its actions using `nginx -s`, e.g. `nginx -s reload`. (currently only `reload` is sent as an action).

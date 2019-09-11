# endpoint-monitor
Nginx reverse proxy sample application to Streams REST operators.

# Under development

**Application is under development, apis etc. are subject to change.**

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





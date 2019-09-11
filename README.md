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
 
 <img width="236" alt="image" src="https://user-images.githubusercontent.com/3769612/64719622-7d516e80-d47d-11e9-9cb3-c90bc4406de5.png">

4. Add the secret from step 3. to the environment of container streams-endpoint-monitor in the deployment configuration for *application-name*.

After steps 2,3,4 the configuration for container streams-endpoint-monitor should look like:

<img width="1244" alt="image" src="https://user-images.githubusercontent.com/3769612/64719577-5e52dc80-d47d-11e9-97d3-cada3f817525.png">



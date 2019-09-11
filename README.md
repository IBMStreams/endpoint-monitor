# endpoint-monitor
Nginx reverse proxy sample application to Streams REST operators.

# Under development

**Application is under development, apis etc. are subject to change.**

# Setup

Using an Openshift cluster run `oc new-app` to build and deploy the *endpoint-moinitor* application:

```
oc new-app \
 -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/master/openshift/templates/streams-endpoints.json -p NAME=<application-name>
```

Create a kubernetes secret with these values:

TBD




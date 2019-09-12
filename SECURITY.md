# Endpoint security

## Creation of endpoints

Endpoint-monitor automatically creates endpoints that proxy to Streams REST operators.
So if a job is submitted that *endpoint-monitor* has visibility to then an endpoint is created automatically.
If the *endpoint-monitor* nginx service is visible outside of the Openshift cluster (and potentially all the way
to the public internet) then these new endpoints will be externally visible. Thus there needs to be control over
who can create endpoints.

Authorization for endpoint creation is by:

1. Openshift permissions
  * Ability to create (using `oc new-app`) the *endpoint-monitor* application
  * Ability to expose the *endpoint-monitor* nginx service externally
1. Streams permissions
  * Ability for the Streams user monitoring the Streams instance to obtain job information.
     * If the user only see a subset of jobs (e.g. a single job group) then only those Streams users who can
       submit jobs into that group can create endpoints.
  * Job filtering by job group
     * The `JOB_GROUP` parameter restricts the processing of jobs by *endpoint-monitor*, for example the monitoring
       can be limited to a single Streams job group `endpoint`.
  * Ability for a Streams user to submit a job
     * Then Streams user/group permissions can limit who can submit a job to the job group `endpoint.
     
## Security of the Streams operators (Jetty servers)

A Streams REST operator is a Streams Java primitive operator that embeds an Eclipse Jetty webserver listening on its
pod's local IP address and configured or ephemeral port.

Visibility of this webserver (ip address/port combination) is limited by Kubernetes visibility of pods and their ip addresses.
https://kubernetes.io/docs/concepts/cluster-administration/networking/

At the very least pods within the same namespace are likely to have visibility into the pod containing a Streams REST operator,
so a pod within the same namespace could try to maliciously inject tuples or access tuples from a Streams REST operator.

Since a pod containing a Streams REST operator has a variable ip address (and port will also be variable if `port:0` is used)
direct access should not be used by non-malicious applications, only through the *endpoint-monitor* nginx service.

So the only authorized user for the Jetty server should be its intended *endpoint-monitor*.

**Details to be added on client certs.**

## Security of the application endpoints

Creation of an *endpoint-monitor* through `oc new-app` does **not** expose the service outside of the cluster.

The endpoints created by *endpoint-monitor* are visble within the cluster through the nginx service endpoint according to Kubernetes networking for services. https://kubernetes.io/docs/concepts/services-networking/service/

**Details to be added on client certs/niginx authentication.**

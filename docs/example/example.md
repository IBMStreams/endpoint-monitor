To help you understand how to use endpoint-monitor, the following example shows a basic use case, where a simple streams job is submitted, and publicly exposed outside of the openshift cluster. 

## Instructions

NOTE: This assumes you have an openshift cluster with CP4D and streams installed

### 1. Deploy endpoint-monitor

- In CP4D
  - Provision a streams instance. More info [here](https://www.ibm.com/support/producthub/icpdata/docs/content/SSQNUZ_current/cpd/svc/streams/provision.html)
  - Create a streams user with password. More info [here](https://www.ibm.com/support/producthub/icpdata/docs/content/SSQNUZ_current/cpd/svc/streams/managing-access.html)
- Log into the openshift cluster
  - This will usually be a command of the form `oc login --token=<TOKEN> --server=<SERVER>`
    - For more info on this, click [here](https://docs.openshift.com/container-platform/4.5/cli_reference/openshift_cli/getting-started-cli.html#cli-logging-in_cli-developer-commands)
- Change into the Kubernetes namespace / openshift project where CP4D Is installed
  - `oc project <PROJECT>`
- Create a kubernetes generic secret for the streams user created above using the following command
  ```
  echo -n '<username>' > user.txt
  echo -n '<password>' > passwd.txt
  kubectl create secret generic streams-user --from-file=STREAMS_USERNAME=./user.txt --from-file=STREAMS_PASSWORD=./passwd.txt
  rm user.txt passwd.txt
  ```
  - More info [here](https://github.com/IBMStreams/endpoint-monitor#1-define-streams-user)
- While still in the current namespace, add the `Nginx:1.14` container image using the following command
  ```
  oc tag docker.io/centos/nginx-114-centos7:latest nginx:1.14
  ```
- Deploy the application
  - Copy and fill in the following command, replacing `<IBMStreamsInstance name>` with the name of the streams instance you defined above.
  - For this example, we are using the `default` job group. 
  - The rest of the optional parameters will be the same as defined [here](https://github.com/IBMStreams/endpoint-monitor#5-deploy-application)
  ```
   oc new-app \
   -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/develop/openshift/templates/streams-endpoints.json \
   -p STREAMS_INSTANCE_NAME=<IBMStreamsInstance name> \
   -p JOB_GROUP=default \
  ```
- Create a route
  - To expose your kubernetes service externally (and thus connect to endpoint-monitor outside the cluster), openshift requires you create route. 
    - For more info on this, click [here](https://docs.openshift.com/enterprise/3.0/architecture/core_concepts/routes.html)
  - To create the route, go to the openshift web UI->administrator tab->Networking->Routes->Create Route
  - For the route name, pick anything
  - We can leave the hostname section blank. Openshift will auto generate one for us
  - Since we didn't specify a name when deploying endpoint-monitor, the service name defaults to `streams-endpoint-monitor`
  - Leave path blank 
  - For the target port, we want to forward incoming connections on port 8443 to port 8443 inside the cluster
  - Leave the 'insecure traffic' as it is, and click create to create the route
  - Assuming everything went according to plan, back on the page describing the router you just created, the status should be green
  - Copy the location
  
    
### 2. Submit the streams application
- TBC...
  

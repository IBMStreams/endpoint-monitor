To help you understand how to use endpoint-monitor, the following example shows a basic example, where a simple streams job is submitted, and publically exposed outside of the openshift cluster. 

## Instructions

NOTE: This assumes you have an openshift cluster with CP4D and streams installed

### 1. Deploy endpoint-monitor

- In CP4D
  - Provision a streams instance. More info [here](https://www.ibm.com/support/producthub/icpdata/docs/content/SSQNUZ_current/cpd/svc/streams/provision.html)
  - Create a streams user with password. More info [here](https://www.ibm.com/support/producthub/icpdata/docs/content/SSQNUZ_current/cpd/svc/streams/managing-access.html)
- Log into the openshift cluster
  - This will usually be a command of the form `oc login --token=<TOKEN> --server=<SERVER>`
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
    
### 2. Submit the streams application
- TBC...
  

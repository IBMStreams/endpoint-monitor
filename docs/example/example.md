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
- Download and run the install script, instructions [here](https://github.com/IBMStreams/endpoint-monitor#setup)
  - Keep in mind the `hostname` field from the output. We will need this later

### 2. Submit the streams application
- For this sample, we will be using the Streams-Rolling average app available [here](https://github.com/IBMStreams/sample.starter_notebooks/blob/latest/Streams-RollingAverageSample.ipynb)
- This app has been included in the `sample_app.ipynb`, located [here](./sample_app.ipynb)
- Download and open the file `sample_app.ipynb` in a python 3.6 environment
- In the second cell under the title '3. Build and submit the application', change the cell values, adding in the streams user, the CP4D URL and the name of the streams instance you defined above
- In the cell under the title '4. Connect to endpoint', change the cell value by adding the hostname from above
- Finally, run the last cell to view the data in real time.
- If you have the openshift web interface running, you can see under the route you created, the details. Of particular notability is the traffic in, and traffic out. These should correspond to the cell retrieving data
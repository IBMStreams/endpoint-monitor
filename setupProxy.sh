APP_NAME=$1
NAMESPACE=$2
INSTANCE=$3
JOB_GROUP=$4

if [ ! $APP_NAME ] || [ ! $INSTANCE ] || [ ! $JOB_GROUP ] || [ ! $NAMESPACE ]
then
   echo "Usage: setupProxy.sh app_name namespace instance job_group [user] [password]"
   echo "User and password default is admin/password"
else
  CPD_USER=$5
  CPD_PASSWORD=$6
  if [ ! $CPD_USER ]
  then
      CPD_USER=admin
  fi

  if [ ! $CPD_PASSWORD]
  then
        CPD_PASSWORD=password
  fi

  echo  "Switching to namespace $NAMESPACE"
  oc project $NAMESPACE
#  oc tag docker.io/centos/python-36-centos7:latest python:3.6  -- Uncomment out if the tag isn't present
#  oc tag docker.io/centos/nginx-114-centos7:latest nginx:1.14

  echo "$CPD_USER" > user.txt
  echo  "$CPD_PASSWORD" > passwd.txt
  echo "Creating secret"
  kubectl create secret generic streams-user --from-file=user.txt --from-file=password.txt
  rm user.txt passwd.txt
  oc new-app \
    -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/develop/openshift/templates/streams-endpoints.json \
    -p NAME=$APP_NAME \
    -p STREAMS_INSTANCE_NAME=$INSTANCE \
    -p JOB_GROUP=$JOB_GROUP \
    -p STREAMS_USER_SECRET=streams-user \
    -p NAMESPACE=$NAMESPACE
  oc create route passthrough --port="8443" -n $NAMESPACE --service="$APP_NAME"  -o=json

  echo "Check host attribute in JSON output above for the proxy URL"
  echo "Might take a few minutes to be active."
  echo "Use oc get pods | grep $APP_NAME to get list of pods for this service"
  echo "Then use oc logs <podname> to see the logs, specify container with -c, e.g. oc logs app-pod -c streams-nginx "

fi
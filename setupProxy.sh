NAMESPACE=$1
INSTANCE=$2

if [ ! $NAMESPACE ] || [ ! $INSTANCE ]; then
    echo "Usage: setupProxy.sh namespace streams_instance [app_name] [job_group] [user] [password]"
    echo "app_name default is streams-endpoint-monitor"
    echo "job_group default is default"
    echo "User and password default is admin/password"
else
    APP_NAME=$3
    JOB_GROUP=$4
    CPD_USER=$5
    CPD_PASSWORD=$6
    if [ ! $APP_NAME ]; then
        APP_NAME=streams-endpoint-monitor
    fi

    if [ ! $JOB_GROUP ]; then
        JOB_GROUP=default
    fi

    if [ ! $CPD_USER ]; then
        CPD_USER=admin
    fi

    if [ ! $CPD_PASSWORD ]; then
        CPD_PASSWORD=password
    fi

    echo "Switching to namespace $NAMESPACE"
    oc project $NAMESPACE

    echo "Tagging Nginx and Python images"
    oc tag docker.io/centos/python-36-centos7:latest python:3.6 # Uncomment if the tag isn't present
    oc tag docker.io/centos/nginx-114-centos7:latest nginx:1.14

    echo -n "$CPD_USER" >user.txt
    echo -n "$CPD_PASSWORD" >passwd.txt
    echo "Creating secret"
    oc create secret generic streams-user --from-file=STREAMS_USERNAME=./user.txt --from-file=STREAMS_PASSWORD=./passwd.txt
    # rm user.txt passwd.txt
    oc new-app \
        -f https://raw.githubusercontent.com/IBMStreams/endpoint-monitor/develop/openshift/templates/streams-endpoints.json \
        -p NAME=$APP_NAME \
        -p STREAMS_INSTANCE_NAME=$INSTANCE \
        -p JOB_GROUP=$JOB_GROUP \
        -p STREAMS_USER_SECRET=streams-user \
        -p NAMESPACE=$NAMESPACE

    oc create route passthrough --port="8443" -n $NAMESPACE --service="$APP_NAME" -o=json

    echo "Check host attribute in JSON output above for the proxy URL"
    echo "Might take a few minutes to be active."
    echo "Use oc get pods | grep $APP_NAME to get list of pods for this service"
    echo "Then use oc logs <podname> to see the logs, specify container with -c, e.g. oc logs app-pod -c streams-nginx "

fi

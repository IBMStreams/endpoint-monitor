# Creates HTTPS certifcates for endpoint operators.

# Argument is name of the endpoint-monitor application
# (parameter NAME when oc new-app was executed)

# Only supported on macos.
#
#


emname=$1

tmp=$(mktemp -d -t em-keys)
server_pass=`openssl rand -base64 32`
client_pass=`openssl rand -base64 8`

# Server key
keytool -genkeypair -keyalg RSA \
    -keystore ${tmp}/server.jks\
    -storepass "${server_pass}" \
    -keypass "${server_pass}" \
    -alias emrestops \
    -dname "CN=endpoint-monitor-jetty" \
    -validity 1000

keytool -export -rfc \
     -keystore ${tmp}/server.jks \
     -storepass "${server_pass}" \
     -keypass "${server_pass}" \
     -alias emrestops \
     -file ${tmp}/servercert.pem

# Client cert
keytool -genkeypair -keyalg RSA \
    -keystore ${tmp}/client.pfx \
    -storetype PKCS12 \
    -storepass "${client_pass}" \
    -alias emnginx \
    -dname "CN=endpoint-monitor-nginx" \
    -validity 1000

# Export for server
keytool -export -rfc -alias emnginx \
    -keystore ${tmp}/client.pfx \
    -storepass "${client_pass}" \
    -file ${tmp}/client.pem

keytool -import \
    --noprompt \
    -keystore ${tmp}/cacerts.jks \
    -storepass "${server_pass}" \
    -trustcacerts \
    -file ${tmp}/client.pem

kubectl create secret generic ${emname}-streams-certs \
    --from-file=${tmp}/client.pfx \
    --from-file=${tmp}/server.jks \
    --from-file=${tmp}/cacerts.jks \
    --from-literal="server.pass=${server_pass}" \
    --from-literal="client.pass=${client_pass}"

rm -fr ${tmp}

FROM centos:centos7
LABEL maintainer="Karsten Fonseca <karsten.fonseca@ibm.com>"

ENV nginxversion="1.14.0-1" \
    os="centos" \
    osversion="7" \
    elversion="7_4"

RUN yum install -y wget openssl openssl-devel sed &&\
    yum -y autoremove &&\
    yum -y install gcc &&\
    yum -y group install "Development Tools" &&\
    yum -y install which &&\
    yum clean all

ADD docker_script.sh /docker_script.sh

RUN chmod +x /docker_script.sh
CMD ["/docker_script.sh"]

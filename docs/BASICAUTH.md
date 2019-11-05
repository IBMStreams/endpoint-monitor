# Service basic authentication

Basic authentication is enabled by having an authentication secret `${NAME}-authentication`
(e.g. `buses-em-authentication`) and including a key `.htpasswd` (name includes leading dot) that defines
users and hashed passwords.

The key's value is created from a `.htpasswd` file and is a common format for web servers,
e.g. see http://www.htaccesstools.com/articles/htpasswd/ .

The files contents can be created using tools such as
[`htpasswd`](https://httpd.apache.org/docs/current/programs/htpasswd.html) or online generations such as:
http://www.htaccesstools.com/htpasswd-generator/


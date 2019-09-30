function readSecret(r) {
    var key;
    try {
        key = require('fs').readFileSync('/var/run/secrets/streams-endpoint-monitor/server-auth/signature-secret');
    } catch (e) {
        // If file doesn't exist, set secret to dummy key, and skip signature verification
        key = '';
    }
    return key.toString();
}

function checkHTTP(r) {
    // HTTP method of the request
    var method = r.method;
    // HTTP method we want to do signature check for
    var checkMethods = ['POST', 'PUT', 'PATCH'];

    if (checkMethods.includes(method)) {
        // request is a POST/PUT/PATCH, invoke signature check
        if (checkSignature(r) == false) {
            // if not authed, return error page
            r.return(401, "Not authorized to access this page");
        };
    }
    // Request is either a GET or an authorized POST/PUT/PATCH, redirect to internal proxy_pass location
    r.internalRedirect(r.variables.redirectLocation);
}

function checkSignature(r) {
    var reqBody = r.requestBody;
    var secret_key = r.variables.signatureSecret;
    var signature = r.headersIn['x-signature'];

    var digest = require('crypto').createHmac('sha1', secret_key).update(JSON.stringify(reqBody)).digest('hex');

    if (signature === digest) {
        // Authorized
        return true;
    } else {
        // Not authorized
        return false;
    }
}
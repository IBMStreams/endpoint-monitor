# Internal details for Signature Verification


In endpoint-monitor, for each job we care about, we create, update and delete Nginx configurations dynamically.
At startup time, if there is a signature-secret located at `/var/run/secrets/streams-endpoint-monitor/server-auth/signature-secret`, the function `_has_signature_secret()` in `app.py` will set the boolean value `self._signature` to true in `file_config.py`
(which writes each job’s Nginx config), and thus the signature verification call `js_content checkHTTP;` will be added to each job’s Nginx configuration. 

Thus:


* If the line `js_content checkHTTP;` **is present** in a job’s Nginx config, this means there is a signature-secret present, and depending on the request type, its signature will be checked

* If the line `js_content checkHTTP;` **is not present** in a job’s Nginx config, this means no signature-secret is present, and all requests, regardless of type are automatically allowed by default.



For the actual signature verification, when a request is received, the line `js_content checkHTTP;` in the given job’s Nginx config will make a call to the function `checkHTTP()` given in the file `signature.js` located at `/opt/app-root/src/js/signature.js`.
If the request type requires a signature check, it will call the function `check_signature()`, which is located in the same file. From there, it uses a combination of the request body and header and the variable `secret_key`
(which is preset in the Nginx config via the line `js_set $signatureSecret readSecret;` to be the return value of the function `readSecret()` ) to compute and verify the signature. 

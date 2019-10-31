# Signature authentication 


To limit who can input data into your endpoints, you can optionally create a kubernetes secret such that only POST, PUT or PATCH requests with the correct signature in its HTTP header will be allowed through. If this optional kubernetes secret is not given, or is removed, all requests, regardless of type are automatically allowed by default.

To enable this signature verification, create a kubernetes opaque/generic secret `${NAME}-authentication`, with key `signature-secret` and value being the secret of your choice.

<img width="394" alt="image" src="https://user-images.githubusercontent.com/3769612/65935654-b6229a80-e3ce-11e9-92ff-a13ace0f7cf6.png">


The signature is computed as a SHA1 hmac on the request body, using the secret key, and is stored as a hmac hex digest in the request’s `X-Signature` HTTP header. 

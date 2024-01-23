## used libs

https://sqlmodel.tiangolo.com/
https://fastapi-users.github.io/fastapi-users/12.1/

## Important Sources / insporations

https://github.com/tiangolo/full-stack-fastapi-postgresql

https://github.com/tiangolo/fastapi/issues/12#issuecomment-457706256

https://github.com/testdrivenio/fastapi-sqlmodel-alembic
https://testdriven.io/blog/fastapi-sqlmodel/

https://docs.authlib.org/en/latest/client/fastapi.html
https://github.com/authlib/demo-oauth-client/blob/master/starlette-google-login/app.py

https://openid.net/specs/openid-connect-core-1_0.html
https://frankie567.github.io/httpx-oauth/oauth2/
https://fastapi-users.github.io/fastapi-users/12.1/configuration/oauth/#instantiate-an-oauth2-client


## interesting
https://github.com/gmachado-nextreason/example-oidc-server-fastapi

https://intility.github.io/fastapi-azure-auth/multi-tenant/fastapi_configuration

Securing Vue.js with OpenID Connect and OAuth by Bobby Johnson | Armada JS 2019
https://www.youtube.com/watch?v=r0BCki3U2AM

## ditched libs

https://github.com/nextml-code/fastapi-third-party-auth
https://github.com/yezz123/AuthX


## Hardening TODO

introduce and implement "TRUSTED_PROXY" setting


# OIDC Token types

    Authorization Code:
        Purpose: The authorization code is obtained during the authorization process as a result of the user's consent to grant access to their information.
        Usage: It is used by the client application to exchange for an access token and optionally an ID token.

    Access Token:
        Purpose: The access token is a credential that represents the authorization granted to the client application. It is used to access protected resources on behalf of the user.
        Usage: The client includes the access token in API requests to access the user's data or perform actions on their behalf.

    ID Token:
        Purpose: The ID token is a JSON Web Token (JWT) that contains claims about the authentication event and, optionally, other user information.
        Usage: It is used to verify the identity of the user. The client can decode and verify the signature of the ID token to ensure its authenticity.

    Refresh Token:
        Purpose: The refresh token is used to obtain a new access token when the current access token expires, without requiring the user to re-authenticate.
        Usage: The client exchanges the refresh token for a new access token when the current access token becomes invalid.

    Token Endpoint:
        Purpose: The token endpoint is an OAuth 2.0 endpoint that the client uses to exchange the authorization code for an access token, ID token, and optionally, a refresh token.
        Usage: The client sends a request to this endpoint, including the authorization code, to obtain the necessary tokens.

    Token ID (Token Identifier):
        Purpose: Token ID refers to the unique identifier associated with a token (e.g., access token, ID token, refresh token).
        Usage: It helps in uniquely identifying and managing tokens. It can be used to track token usage, revoke tokens, or manage token lifecycle.
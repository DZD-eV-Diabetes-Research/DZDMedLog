# Test Environment for OpenID Connect functionality

## Prepare

> go into the ./test_env folder (if not allready)

```
cd test_env
```

## Start

```
docker compose up -d
```

This will start a local Authentik instance with a prepared configurations (user,oidc-provider,app)

## Check

visit http://http://172.25.0.12:9000 to check if Authentik is running
You can login with:
`akadmin`:`iamastupidtest` for admin access
`devuser`:`password123` for a normal user access


## Use API

Now start the local app 
```
python3 ../MedLog/backend/medlogserver/main.py
```

visit localhost:8888/docs to see the api


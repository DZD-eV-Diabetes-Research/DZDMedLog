# MedLogRestApi.AuthApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**getFreshAccessTokenAuthRefreshPost**](AuthApi.md#getFreshAccessTokenAuthRefreshPost) | **POST** /auth/refresh | Get Fresh Access Token
[**loginForRefreshAndAccessTokenAuthTokenPost**](AuthApi.md#loginForRefreshAndAccessTokenAuthTokenPost) | **POST** /auth/token | Login For Refresh And Access Token



## getFreshAccessTokenAuthRefreshPost

> JWTAccessTokenResponse getFreshAccessTokenAuthRefreshPost(opts)

Get Fresh Access Token

Endpoint to get a new/fresh access token. A valid refresh token must be provided. Accepts the refresh token either as a form field **OR** in the &#39;refresh-token&#39; header field.&lt;br&gt;Returns a new access token on success.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';

let apiInstance = new MedLogRestApi.AuthApi();
let opts = {
  'refreshToken': Bearer S0VLU0UhIExFQ0tFUiEK, // String | Refresh token via `refresh-token` header field
  'refreshTokenForm': "refreshTokenForm_example" // String | 
};
apiInstance.getFreshAccessTokenAuthRefreshPost(opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **refreshToken** | **String**| Refresh token via &#x60;refresh-token&#x60; header field | [optional] 
 **refreshTokenForm** | **String**|  | [optional] 

### Return type

[**JWTAccessTokenResponse**](JWTAccessTokenResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/x-www-form-urlencoded
- **Accept**: application/json


## loginForRefreshAndAccessTokenAuthTokenPost

> JWTBundleTokenResponse loginForRefreshAndAccessTokenAuthTokenPost(username, password, opts)

Login For Refresh And Access Token

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';

let apiInstance = new MedLogRestApi.AuthApi();
let username = "username_example"; // String | 
let password = "password_example"; // String | 
let opts = {
  'grantType': new MedLogRestApi.GrantType(), // GrantType | 
  'scope': "''", // String | 
  'clientId': new MedLogRestApi.ClientId(), // ClientId | 
  'clientSecret': new MedLogRestApi.ClientSecret() // ClientSecret | 
};
apiInstance.loginForRefreshAndAccessTokenAuthTokenPost(username, password, opts, (error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters


Name | Type | Description  | Notes
------------- | ------------- | ------------- | -------------
 **username** | **String**|  | 
 **password** | **String**|  | 
 **grantType** | [**GrantType**](GrantType.md)|  | [optional] 
 **scope** | **String**|  | [optional] [default to &#39;&#39;]
 **clientId** | [**ClientId**](ClientId.md)|  | [optional] 
 **clientSecret** | [**ClientSecret**](ClientSecret.md)|  | [optional] 

### Return type

[**JWTBundleTokenResponse**](JWTBundleTokenResponse.md)

### Authorization

No authorization required

### HTTP request headers

- **Content-Type**: application/x-www-form-urlencoded
- **Accept**: application/json


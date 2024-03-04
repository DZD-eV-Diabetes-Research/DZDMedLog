# MedLogRestApi.UserApi

All URIs are relative to *http://localhost*

Method | HTTP request | Description
------------- | ------------- | -------------
[**createLocalUserUserPost**](UserApi.md#createLocalUserUserPost) | **POST** /user | Create Local User
[**getMyselfUserMeGet**](UserApi.md#getMyselfUserMeGet) | **GET** /user/me | Get Myself
[**getUserUserUserIdGet**](UserApi.md#getUserUserUserIdGet) | **GET** /user/{user_id} | Get User
[**listUsersUserGet**](UserApi.md#listUsersUserGet) | **GET** /user | List Users
[**setMyPasswordUserMePasswordPut**](UserApi.md#setMyPasswordUserMePasswordPut) | **PUT** /user/me/password | Set My Password
[**setUserPasswordUserUserIdPasswordPut**](UserApi.md#setUserPasswordUserUserIdPasswordPut) | **PUT** /user/{user_id}/password | Set User Password
[**updateMyselfUserMePatch**](UserApi.md#updateMyselfUserMePatch) | **PATCH** /user/me | Update Myself
[**updateUserUserUserIdPatch**](UserApi.md#updateUserUserUserIdPatch) | **PATCH** /user/{user_id} | Update User



## createLocalUserUserPost

> User createLocalUserUserPost(userCreate, opts)

Create Local User

Creates a new user in the local user database. Needs admin or user-manager role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let userCreate = new MedLogRestApi.UserCreate(); // UserCreate | 
let opts = {
  'userPassword': "userPassword_example" // String | The password for the created user. If non is defined the user will be created but not able to login until an admin user defines a password.
};
apiInstance.createLocalUserUserPost(userCreate, opts, (error, data, response) => {
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
 **userCreate** | [**UserCreate**](UserCreate.md)|  | 
 **userPassword** | **String**| The password for the created user. If non is defined the user will be created but not able to login until an admin user defines a password. | [optional] 

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## getMyselfUserMeGet

> User getMyselfUserMeGet()

Get Myself

Get account data from the current user

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
apiInstance.getMyselfUserMeGet((error, data, response) => {
  if (error) {
    console.error(error);
  } else {
    console.log('API called successfully. Returned data: ' + data);
  }
});
```

### Parameters

This endpoint does not need any parameter.

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## getUserUserUserIdGet

> User getUserUserUserIdGet(userId)

Get User

Get account data from a user by its id. Needs admin or user-manager role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let userId = "userId_example"; // String | 
apiInstance.getUserUserUserIdGet(userId, (error, data, response) => {
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
 **userId** | **String**|  | 

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## listUsersUserGet

> PaginatedResponseUser listUsersUserGet(opts)

List Users

Get account data from a user by its id.  Needs admin or user-manager role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let opts = {
  'inclDeactivated': false, // Boolean | Also list deactivated users.
  'offset': 0, // Number | 
  'limit': 100, // Number | 
  'orderBy': "orderBy_example", // String | 
  'orderDesc': false // Boolean | 
};
apiInstance.listUsersUserGet(opts, (error, data, response) => {
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
 **inclDeactivated** | **Boolean**| Also list deactivated users. | [optional] [default to false]
 **offset** | **Number**|  | [optional] [default to 0]
 **limit** | **Number**|  | [optional] [default to 100]
 **orderBy** | **String**|  | [optional] 
 **orderDesc** | **Boolean**|  | [optional] [default to false]

### Return type

[**PaginatedResponseUser**](PaginatedResponseUser.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: Not defined
- **Accept**: application/json


## setMyPasswordUserMePasswordPut

> User setMyPasswordUserMePasswordPut(opts)

Set My Password

Set my password if i am a &#39;local&#39; user. If my account was provisioned via an external OpenID Connect provider this does nothing except the return value will be &#x60;false&#x60;.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let opts = {
  'oldPassword': "oldPassword_example", // String | 
  'newPassword': "newPassword_example", // String | 
  'newPasswordRepeated': "newPasswordRepeated_example" // String | For good measure we require the password twice to mitiage typos.
};
apiInstance.setMyPasswordUserMePasswordPut(opts, (error, data, response) => {
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
 **oldPassword** | **String**|  | [optional] 
 **newPassword** | **String**|  | [optional] 
 **newPasswordRepeated** | **String**| For good measure we require the password twice to mitiage typos. | [optional] 

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/x-www-form-urlencoded
- **Accept**: application/json


## setUserPasswordUserUserIdPasswordPut

> User setUserPasswordUserUserIdPasswordPut(userId, opts)

Set User Password

Set a local users password. If the user is provisioned via an external OpenID Connect provider this does nothing except the return value will be &#x60;false&#x60;.  Needs admin or user-manager role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let userId = "userId_example"; // String | 
let opts = {
  'newPassword': "newPassword_example", // String | 
  'newPasswordRepeated': "newPasswordRepeated_example" // String | For good measure we require the password twice to mitiage typos.
};
apiInstance.setUserPasswordUserUserIdPasswordPut(userId, opts, (error, data, response) => {
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
 **userId** | **String**|  | 
 **newPassword** | **String**|  | [optional] 
 **newPasswordRepeated** | **String**| For good measure we require the password twice to mitiage typos. | [optional] 

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/x-www-form-urlencoded
- **Accept**: application/json


## updateMyselfUserMePatch

> User updateMyselfUserMePatch(userUpdateByUser)

Update Myself

Update my user account data.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let userUpdateByUser = new MedLogRestApi.UserUpdateByUser(); // UserUpdateByUser | 
apiInstance.updateMyselfUserMePatch(userUpdateByUser, (error, data, response) => {
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
 **userUpdateByUser** | [**UserUpdateByUser**](UserUpdateByUser.md)|  | 

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


## updateUserUserUserIdPatch

> User updateUserUserUserIdPatch(userId, userUpdateByAdmin)

Update User

Get account data from a user by its id. Needs admin or user-manager role.

### Example

```javascript
import MedLogRestApi from 'med_log_rest_api';
let defaultClient = MedLogRestApi.ApiClient.instance;
// Configure OAuth2 access token for authorization: OAuth2PasswordBearer
let OAuth2PasswordBearer = defaultClient.authentications['OAuth2PasswordBearer'];
OAuth2PasswordBearer.accessToken = 'YOUR ACCESS TOKEN';

let apiInstance = new MedLogRestApi.UserApi();
let userId = "userId_example"; // String | 
let userUpdateByAdmin = new MedLogRestApi.UserUpdateByAdmin(); // UserUpdateByAdmin | 
apiInstance.updateUserUserUserIdPatch(userId, userUpdateByAdmin, (error, data, response) => {
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
 **userId** | **String**|  | 
 **userUpdateByAdmin** | [**UserUpdateByAdmin**](UserUpdateByAdmin.md)|  | 

### Return type

[**User**](User.md)

### Authorization

[OAuth2PasswordBearer](../README.md#OAuth2PasswordBearer)

### HTTP request headers

- **Content-Type**: application/json
- **Accept**: application/json


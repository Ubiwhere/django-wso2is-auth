# django_wso2is
A Django application that enables authentication against a remote WSO2 Identity Server.

## Installation
`pip install django-wso2is-auth`

## Getting started
1. In your Django project's settings file, change the Django `AUTHENTICATION_BACKENDS` to:

```python
AUTHENTICATION_BACKENDS = ['django_wso2is.backends.WSO2isAuthenticationBackend',]
```

2. If you are using Rest framework and want to authenticate API requests against WSO2 Identity server:
```python
REST_FRAMEWORK = {
    # ... other rest framework settings.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'django_wso2_is.authentication.BearerAuthentication'
    ],
}
```

3. Lastly, you need to provide some settings:
```python
WSO2IS_CONFIG = {
    # The URL of your WSO2 identity server
    "SERVER_URL": "<str>",
    # The "OAuth Client Key" of your service provider
    "OAUTH_CLIENT_ID": "<str>",
    # The "OAuth Client Secret" of your service provider
    "OAUTH_SECRET_KEY": "<str>",
    # The username of the service provider admin
    "ADMIN_USER_USERNAME": "<str>",
    # The password of the service provider admin
    "ADMIN_USER_SECRET_KEY": "<str>",
    # The name of the admin role for the client (e.g. `Application/Administration`)
    "CLIENT_ADMIN_ROLE": "<str>",
    # The group's admin role name
    "GROUP_ADMIN_ROLE": "<str>",
    # Whether the validity of the server's SSL certificate should be validated.
    # default=`False`. WARNING: This should be `True` in production environments.
    "VERIFY_SSL": False,
    # When a user is successfully authenticated with the WSO2 server this user
    # will be created or updated in the local database. This search is based on `DJANGO_USER_LOOKUP_FIELD`. 
    # This field is optional (default=None), and in such cases the lookup is performed based on the `USERNAME` field
    # of the auth user model, which by default corresponds to the `username` field. 
    # For instance, if you want this lookup to be based on email 
    # you can specify `"DJANGO_USER_LOOKUP_FIELD": "email"`
    DJANGO_USER_LOOKUP_FIELD: None,
    # This dictionary makes the mapping between attributes of the local user with attributes of the remote user.
    # This field is optional (default=None), but it is HIGHLY recommended you customize it. By default only `username` get's mapped
    # to WSO2's attribute "userName". A more detailed example of how to customize this field will be presented below.
    ATTRIBUTE_MAPPING: {"username": "userName"} # dict in format 'local_attribute' : 'remote_attribute'
}
```

You are all set!

## Advanced usage

### 1. Customizing attribute mapping
As previously mentioned, only the mapping between the username field is done. Let's say you have the following django User model:
```python
class MyUser(AbstractBaseUser):
  # first_name and last_name exist by default in django.contrib.auth user model
  # Now we specify new custom fields to save the user's organization and phone number from WSO2 identity server
  user_organization = models.CharField(max_length=255,null=True, blank=True)
  phone_number = models.CharField(max_length=255, null=True, blank=True)
  external_id = models.CharField(max_length=255, null=True, blank=True)
  
```
First we can inspect the JSON response from WSO2 to see the user information that is being returned to django. (This assumes you already configured everything else)
```python
# Inside django's shell (python manage.py shell)
from django_wso2is import Token
from pprint import pprint

token = Token.from_credentials("sample-username", "sample-password")
pprint(token.user_info)
```
You should get something like this:
```
{'emails': ['sample-email@gmail.com'],
 'id': '6b15e727-6b52-4d15-a9c9-b166a0439aa1',
 'meta': {'created': '2023-01-19T10:44:51.563609Z',
          'lastModified': '2023-01-19T15:52:48.282703Z',
          'location': 'https://sample-wso2is-server:9443/scim2/Users/6b15e727-6b52-4d15-a9c9-b166a0439aa1',
          'resourceType': 'User'},
 'name': {'familyName': 'John', 'givenName': 'Doe'},
 'phoneNumbers': [{'type': 'mobile', 'value': '914420876'}],
 'roles': [{'type': 'default',
            'value': 'Internal/everyone,Application/Administração'},
           {'$ref': 'https://wso2-dev.ubiwhere.com:9443/scim2/Roles/f0da2c12-f4c5-49dd-81f6-5077dfdd98d1',
            'display': 'Application/Administração',
            'value': 'f0da2c12-f4c5-49dd-81f6-5077dfdd98d1'},
           {'$ref': 'https://sample-wso2is-server:9443/scim2/Roles/75ace894-dc8b-495f-8438-60a066d84966',
            'display': 'everyone',
            'value': '75ace894-dc8b-495f-8438-60a066d84966'}],
 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User',
             'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User'],
 'urn:ietf:params:scim:schemas:extension:enterprise:2.0:User': {'country': 'Portugal',
                                                                'organization': 'My organization'},
 'userName': 'sample-username'}
```
To accommodate these additional fields the attribute mapping will be: 
```python
"ATTRIBUTE_MAPPING": {
    "username": "userName",
    "email": "emails[0]", # [0] because WSO2 returns the key "emails" as a list
    "phone_number": "phoneNumbers[0].value", # [0].value because WSO2 returns the key "phoneNumbers" as a list of objects with key "value"
    "first_name": "name.givenName", # .givenName because WSO2 returns nested "name" object
    "last_name": "name.familyName", # .familyName for the same reason as before
    "external_id": "id", # Simple attribute mapping
},
```



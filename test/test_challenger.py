"""
Test the challenger by sending requests to it via a TiddlyWeb instance.
The LDAP interface is mocked as setting up a real one in a test
environment is too much effort.

Still to  test and implement:
* Setting LDAP host and port in config
* Act on a redirect value
* Use redirect values other than /
* Setting a cookie
* Handle no connection to the LDAP server
* Accept a friendly user ID and map it to a DN.
* Pass error messages back to the form.
"""


import httplib2
import ldap
from _ldap import LDAPError

from mock import Mock

from test.fixtures import initialize_app


def setup_module():
    initialize_app()


def test_challenger_get_responds_with_401():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/challenge/tiddlywebplugins.ldapauth', method='GET')

    assert response['status'] == '401'


def test_challenger_get_responds_with_login_form():
    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/challenge/tiddlywebplugins.ldapauth', method='GET')

    assert content == """
        <form action="" method="POST">
User: <input name="user" size="40">
Password <input type="password" name="password" size="40">
<input type="hidden" name="tiddlyweb_redirect" value="/">

<input type="hidden" id="csrf_token" name="csrf_token">
<input type="submit" value="submit">
</form>
        """


def test_post_valid_user_credentials_responds_with_303():
    mock_ldap = ldap
    mock_initialize = ldap.initialize
    mock_ldap.initialize = Mock(return_value=mock_initialize)
    mock_initialize.simple_bind_s = Mock()

    try:
        http = httplib2.Http()
        http.request('http://our_test_domain:8001/challenge/tiddlywebplugins.ldapauth',
                     method='POST',
                     headers={'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                     body='user=pads&password=letmein',
                     redirections=0)

        mock_ldap.initialize.assert_called_once_with('ldap://127.0.0.1:389')
        mock_initialize.simple_bind_s.assert_called_once_with('pads', 'letmein')
    except httplib2.RedirectLimit, e:
        raised = 1

    assert raised
    assert e.response['status'] == '303'


def test_post_invalid_user_credentials_responds_with_401():
    mock_ldap = ldap
    mock_initialize = ldap.initialize
    mock_ldap.initialize = Mock(return_value=mock_initialize)
    # The Python LDAP interface does not distinguish between an invalid DN (the user) and a bad password
    mock_initialize.simple_bind_s = Mock(side_effect=LDAPError({'desc': 'Invalid Credentials'}))

    http = httplib2.Http()
    response, content = http.request('http://our_test_domain:8001/challenge/tiddlywebplugins.ldapauth',
                                     method='POST',
                                     headers={'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                                     body='user=imposter&password=letmein',
                                     redirections=0)

    mock_ldap.initialize.assert_called_once_with('ldap://127.0.0.1:389')
    mock_initialize.simple_bind_s.assert_called_once_with('imposter', 'letmein')

    assert response['status'] == '401'

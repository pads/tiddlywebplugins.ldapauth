"""
Test the challenger by sending requests to it via a TiddlyWeb instance.
The LDAP interface is mocked as setting up a real one in a test
environment is too much effort.

Still to  test and implement:
* Act on a redirect value
* Use redirect values other than /
* Accept a friendly user ID and map it to a DN.
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

    assert response['content-type'] == 'text/html; charset=UTF-8'
    _assert_form(content)


def test_post_valid_user_credentials_responds_with_303():
    mock_ldap, mock_initialize = _mock_good_ldap_bind()

    try:
        _send_good_login()

    except httplib2.RedirectLimit, e:
        raised = 1

    mock_ldap.initialize.assert_called_once_with('ldap://127.0.0.1:389')
    mock_initialize.simple_bind_s.assert_called_once_with('pads', 'letmein')

    assert raised
    assert e.response['status'] == '303'


def test_post_valid_user_credentials_sets_cookie():
    _mock_good_ldap_bind()

    try:
        _send_good_login()

    except httplib2.RedirectLimit, e:
        raised = 1

    assert raised
    assert 'tiddlyweb_user="pads:0af5c9b' in e.response['set-cookie']


def test_post_invalid_user_credentials_responds_with_401():
    mock_ldap, mock_initialize = _mock_bad_ldap_bind()

    response, content = _send_bad_login()

    mock_ldap.initialize.assert_called_once_with('ldap://127.0.0.1:389')
    mock_initialize.simple_bind_s.assert_called_once_with('imposter', 'letmein')

    assert response['status'] == '401'


def test_post_invalid_user_credentials_responds_with_login_form():
    mock_ldap, mock_initialize = _mock_bad_ldap_bind()

    response, content = _send_bad_login()

    mock_ldap.initialize.assert_called_once_with('ldap://127.0.0.1:389')
    mock_initialize.simple_bind_s.assert_called_once_with('imposter', 'letmein')

    _assert_form(content, 'Invalid user credentials, please try again')


def test_post_can_use_custom_ldap_config():
    from tiddlyweb.config import config

    config['ldap_host'] = '1.2.3.4'
    config['ldap_port'] = '56789'

    mock_ldap, mock_initialize = _mock_bad_ldap_bind()

    _send_bad_login()

    mock_ldap.initialize.assert_called_once_with('ldap://1.2.3.4:56789')


def test_no_ldap_connection_responds_with_504():
    mock_ldap, mock_initialize = _mock_bad_ldap_bind(exception=ldap.SERVER_DOWN({'desc': "Can't contact LDAP server"}))

    response, content = _send_good_login()

    mock_ldap.initialize.assert_called_once()
    mock_initialize.simple_bind_s.assert_called_once_with('pads', 'letmein')

    assert response['status'] == '504'


def test_no_ldap_connection_responds_with_login_form():
    mock_ldap, mock_initialize = _mock_bad_ldap_bind(exception=ldap.SERVER_DOWN({'desc': "Can't contact LDAP server"}))

    response, content = _send_good_login()

    mock_ldap.initialize.assert_called_once()
    mock_initialize.simple_bind_s.assert_called_once_with('pads', 'letmein')

    _assert_form(content, 'Unable to reach authorization provider, please contact your administrator')


def _assert_form(content, error_message=''):
    assert content == """
        <p>%s</p>
        <form action="" method="POST">
User: <input name="user" size="40">
Password <input type="password" name="password" size="40">
<input type="hidden" name="tiddlyweb_redirect" value="/">

<input type="hidden" id="csrf_token" name="csrf_token">
<input type="submit" value="submit">
</form>
        """ % error_message


def _mock_good_ldap_bind():
    mock_ldap = ldap
    mock_initialize = ldap.initialize
    mock_ldap.initialize = Mock(name='ldap_init', return_value=mock_initialize)
    mock_initialize.simple_bind_s = Mock(name='ldap_bind')
    return mock_ldap, mock_initialize


def _mock_bad_ldap_bind(exception=ldap.INVALID_CREDENTIALS({'desc': 'Invalid Credentials'})):
    mock_ldap = ldap
    mock_initialize = ldap.initialize
    mock_ldap.initialize = Mock(name='ldap_init', return_value=mock_initialize)
    # The Python LDAP interface does not distinguish between an invalid DN (the user) and a bad password
    mock_initialize.simple_bind_s = Mock(name='ldap_bind',
                                         side_effect=exception)
    return mock_ldap, mock_initialize


def _send_good_login():
    http = httplib2.Http()
    return http.request('http://our_test_domain:8001/challenge/tiddlywebplugins.ldapauth',
                        method='POST',
                        headers={'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                        body='user=pads&password=letmein',
                        redirections=0)


def _send_bad_login():
    http = httplib2.Http()
    return http.request('http://our_test_domain:8001/challenge/tiddlywebplugins.ldapauth',
                        method='POST',
                        headers={'content-type': 'application/x-www-form-urlencoded; charset=UTF-8'},
                        body='user=imposter&password=letmein',
                        redirections=0)

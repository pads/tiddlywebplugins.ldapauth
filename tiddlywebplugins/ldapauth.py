import logging
import ldap

from tiddlyweb.web.challengers import ChallengerInterface
from tiddlyweb.web.util import make_cookie

LOGGER = logging.getLogger(__name__)


class Challenger(ChallengerInterface):
    """
    A simple challenger that asks the user, by form, for their
    username and password and validates it against an LDAP
    server.
    """

    def challenge_get(self, environ, start_response):
        """
        Respond to a GET request by sending a form.
        """
        redirect = (environ['tiddlyweb.query'].get('tiddlyweb_redirect', ['/'])[0])
        return self._send_login_form(start_response, redirect=redirect)

    def challenge_post(self, environ, start_response):
        """
        Respond to a POST by processing data sent from a form.
        """
        ldap_config = environ['tiddlyweb.config'].get('ldapauth', {})
        ldap_host = ldap_config.get('ldap_host', '127.0.0.1')
        ldap_port = ldap_config.get('ldap_port', '389')
        ldap_instance = ldap.initialize('ldap://%s:%s' % (ldap_host, ldap_port))

        query = environ['tiddlyweb.query']
        user = query['user'][0]
        password = query['password'][0]
        redirect = query.get('tiddlyweb_redirect', ['/'])[0]

        try:
            ldap_instance.simple_bind_s(user, password)
            LOGGER.info("user %s successfully authenticated" % user)
            status = '303 See Other'

            secret = environ['tiddlyweb.config']['secret']
            cookie_age = environ['tiddlyweb.config'].get('cookie_age', None)
            cookie = make_cookie('tiddlyweb_user', user, mac_key=secret, path=self._cookie_path(environ),
                                 expires=cookie_age)
            start_response(status, [('Content-Type', 'text/plain'), ('Set-Cookie', cookie)])
            return [status]
        except ldap.INVALID_CREDENTIALS:
            LOGGER.warn("user %s failed authentication" % user)
            return self._send_login_form(start_response, error_message='Invalid user credentials, please try again',
                                         redirect=redirect)
        except ldap.SERVER_DOWN:
            LOGGER.error("could not establish connection with LDAP server")
            return self._send_login_form(start_response, '504 Gateway Timeout',
                                         error_message=
                                         'Unable to reach authorization provider, please contact your administrator',
                                         redirect=redirect)

    def _send_login_form(self, start_response, status='401 Unauthorized', error_message='', redirect='/'):
        start_response(status, [('Content-Type', 'text/html; charset=UTF-8')])
        return ["""
<p>%s</p>
<form action="" method="POST">
    <label>
        User:
        <input name="user" />
    </label>
    <label>
        Password:
        <input type="password" name="password" />
    </label>
    <input type="hidden" name="tiddlyweb_redirect" value="%s" />
    <input type="submit" value="submit" />
</form>
        """ % (error_message, redirect)]

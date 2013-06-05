import logging
import ldap

from tiddlyweb.web.challengers import ChallengerInterface
from tiddlyweb.web.util import make_cookie, server_host_url

LOGGER = logging.getLogger(__name__)

FORM = """
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
    <input type="hidden" name="tiddlyweb_redirect" value="%s" />%s
"""

TW_FORM_END = """
    <input type="submit" value="submit" />
</form>"""

TS_FORM_END = """
    <input type="hidden" id="csrf_token" name="csrf_token" />
    <input type="submit" value="submit" />
</form>
<script type="text/javascript" src="/bags/tiddlyspace/tiddlers/TiddlySpaceCSRF"></script>
<script type="text/javascript">
    var csrfToken = window.getCSRFToken(),
        el = null;

    if (csrfToken) {
        el = document.getElementById('csrf_token');
        el.value = csrfToken;
    }
</script>"""


class Challenger(ChallengerInterface):
    """
    A simple challenger that asks the user, by form, for their
    username and password and validates it against an LDAP
    server.
    """

    def challenge_get(self, environ, start_response):
        """
        Respond to a GET request by sending a form for the user to supply a username and password.
        """
        tiddlyspace_mode = environ['tiddlyweb.config'].get('ldapauth', {}).get('ldap_tiddlyspace_mode', False)

        redirect = (environ['tiddlyweb.query'].get('tiddlyweb_redirect', ['/'])[0])
        return self._send_login_form(start_response, redirect=redirect, tiddlyspace_mode=tiddlyspace_mode)

    def challenge_post(self, environ, start_response):
        """
        Respond to a POST by processing data sent from a form.
        Attempts to bind to the LDAP interface with the user credentials extracted from the form.
        If this succeeds then the user is redirected to the target URI (default '/').
        If the authentication fails then the form is re-sent with the appropriate error message.
        """
        ldap_config = environ['tiddlyweb.config'].get('ldapauth', {})
        ldap_host = ldap_config.get('ldap_host', '127.0.0.1')
        ldap_port = ldap_config.get('ldap_port', '389')
        ldap_base_dn = ldap_config.get('ldap_base_dn', 'dc=localhost')
        ldap_instance = ldap.initialize('ldap://%s:%s' % (ldap_host, ldap_port))
        tiddlyspace_mode = ldap_config.get('ldap_tiddlyspace_mode', False)

        # Get the required data from the posted form
        query = environ['tiddlyweb.query']
        user = query['user'][0]
        password = query['password'][0]
        redirect = query.get('tiddlyweb_redirect', ['/'])[0]

        try:
            # Attempt to authenticate the user.I
            # If no exception is raised then the user is authenticated.
            ldap_instance.simple_bind_s('cn=%s,%s' % (user, ldap_base_dn), password)
            LOGGER.info("user %s successfully authenticated" % user)

            status = '303 See Other'
            uri = '%s%s' % (server_host_url(environ), redirect)
            cookie = self._make_cookie(environ, user)

            # Redirect the user to the target URI now that they are authenticated.
            start_response(status, [('Content-Type', 'text/plain'), ('Set-Cookie', cookie),
                                    ('Location', uri.encode('utf-8'))])
            return [uri]
        except ldap.INVALID_CREDENTIALS:
            LOGGER.warn("user %s failed authentication" % user)
            return self._send_login_form(start_response, error_message='Invalid user credentials, please try again',
                                         redirect=redirect, tiddlyspace_mode=tiddlyspace_mode)
        except ldap.SERVER_DOWN:
            LOGGER.error("could not establish connection with LDAP server")
            return self._send_login_form(start_response, '504 Gateway Timeout',
                                         error_message=
                                         'Unable to reach authorization provider, please contact your administrator',
                                         redirect=redirect, tiddlyspace_mode=tiddlyspace_mode)

    def _make_cookie(self, environ, user):
        secret = environ['tiddlyweb.config']['secret']
        cookie_age = environ['tiddlyweb.config'].get('cookie_age', None)
        return make_cookie('tiddlyweb_user', user, mac_key=secret, path=self._cookie_path(environ),
                           expires=cookie_age)

    def _send_login_form(self, start_response, status='401 Unauthorized', error_message='', redirect='/',
                         tiddlyspace_mode=False):
        start_response(status, [('Content-Type', 'text/html; charset=UTF-8')])
        if tiddlyspace_mode:
            return [FORM % (error_message, redirect, TS_FORM_END)]
        else:
            return [FORM % (error_message, redirect, TW_FORM_END)]

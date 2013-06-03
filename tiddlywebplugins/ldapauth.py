import logging
import ldap

from tiddlyweb.web.challengers import ChallengerInterface

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
        start_response('401 Unauthorized', [('Content-Type', 'text/html; charset=UTF-8')])
        return ["""
        <form action="" method="POST">
User: <input name="user" size="40">
Password <input type="password" name="password" size="40">
<input type="hidden" name="tiddlyweb_redirect" value="/">

<input type="hidden" id="csrf_token" name="csrf_token">
<input type="submit" value="submit">
</form>
        """]

    def challenge_post(self, environ, start_response):
        """
        Respond to a POST by processing data sent from a form.
        """
        ldap_host = environ['tiddlyweb.config'].get('ldap_host', '127.0.0.1')
        ldap_port = environ['tiddlyweb.config'].get('ldap_port', '389')
        ldap_instance = ldap.initialize('ldap://%s:%s' % (ldap_host, ldap_port))

        query = environ['tiddlyweb.query']
        user = query['user'][0]
        password = query['password'][0]

        status = '401 Unauthorized'
        try:
            ldap_instance.simple_bind_s(user, password)
            status = '303 See Other'
        except ldap.LDAPError:
            pass

        start_response(status, [('Content-Type', 'text/plain')])
        return [status]

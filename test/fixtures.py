import wsgi_intercept
from wsgi_intercept import httplib2_intercept

from tiddlyweb.web.serve import load_app
from tiddlywebconfig import config

config['server_host'] = {
    'scheme': 'http',
    'host': 'our_test_domain',
    'port': '8001',
}

config['auth_systems'] = ['tiddlywebplugins.ldapauth']


def initialize_app():
    app = load_app()

    def app_fn():
        return app

    httplib2_intercept.install()
    wsgi_intercept.add_wsgi_intercept('our_test_domain', 8001, app_fn)

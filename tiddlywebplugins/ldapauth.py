import logging

from tiddlyweb.web.challengers import ChallengerInterface

LOGGER = logging.getLogger(__name__)


class Challenger(ChallengerInterface):
    """

    """

    def challenge_get(self, environ, start_response):

        start_response('200 OK',
                       [('Content-Type', 'text/html; charset=UTF-8')])
        return ['<html><body><h1>Not yet Implemented</h1></body></html>']

    def challenge_post(self, environ, start_response):

        start_response('200 OK',
                       [('Content-Type', 'text/html; charset=UTF-8')])
        return ['<html><body><h1>Not yet Implemented</h1></body></html>']

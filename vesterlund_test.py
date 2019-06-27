import falcon

from mode import *
from login import *
from submit import *

api = falcon.API()
api.add_route('/', Login())
api.add_route('/mode', SelectMode())
api.add_route('/submit', Submit())


if __name__ == '__main__':
    from wsgiref import simple_server
    simple_server.make_server('0.0.0.0', 8080, api).serve_forever()

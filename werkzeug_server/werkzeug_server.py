import json
import time

from werkzeug.routing import Rule, Map
from werkzeug.serving import run_simple
from werkzeug.wrappers import Response
from werkzeug.exceptions import NotFound, InternalServerError


class SampleServer(object):

    def __init__(self, server_name):
        self.server_name = server_name or __name__
        self.route_func = dict()
        self.route_map = Map()

    def run(self, host='127.0.0.1', port=8000, **options):
        run_simple(host, port, self, **options)

    def __call__(self, environ, start_response):
        url_adapter = self.route_map.bind_to_environ(environ)
        rv = Response(content_type='application/json')
        try:
            rule = url_adapter.match(environ['PATH_INFO'])
            func = self.route_func.get(rule[0])
            rv.status_code = 200
            rv.data = json.dumps(func())
        except (NotFound, InternalServerError) as e:
            rv.data = e.description
            rv.status_code = e.code
        finally:
            return rv(environ, start_response)

    def route(self, path):
        def inner(f):
            rule = Rule(path, endpoint=f.__name__)
            self.route_map.add(rule)
            if f.__name__ in self.route_func:
                print("error, func name [{}] duplicated".format(f.__name__))
                exit(1)
            else:
                self.route_func[f.__name__] = f
            return f

        return inner


app = SampleServer('zhuozimu')


@app.route("/")
def index():
    return dict(msg="welcome", date=time.ctime())


@app.route("/test")
def test():
    return dict(msg="test json")


if __name__ == '__main__':
    """gunicorn -w 2 werkzeug_server:app"""
    app.run()

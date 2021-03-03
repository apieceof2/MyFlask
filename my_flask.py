from werkzeug import Response
from werkzeug.exceptions import HTTPException
from werkzeug.local import LocalStack
from werkzeug.routing import Rule, Map
from functools import wraps


class _RequestContext(object):
    def __init__(self, app, environ):
        self.app = app

        # 将当前请求的url_adapter注入
        self.url_adapter = self.app.url_map.bind_to_environ(environ)

    def __enter__(self):
        _request_ctx_stack.push(self)

    def __exit__(self, exc_type, exc_val, exc_tb):
        """如果没有出错, 直接pop"""
        if exc_tb is None:
            _request_ctx_stack.pop()


class FlaskAPP(object):
    def __init__(self, package_name, debug=True):
        # 是否开启debug
        self.debug = debug

        # 用来记录Rule的Map
        self.url_map = Map()

        # key为endpoint, 也就是某个视图函数的标识符, 这里使用函数名作为endpoint. value为函数
        self.view_funcs = {}

        # key为error code, value为函数
        self.error_handlers = {}

        # 设置包名
        self.package_name = package_name

    def __call__(self, environ, start_response):
        """程序的入口, 每次请求都会调用本函数, 实际的响应通过wsgi_app实现
        :param environ: 环境字典
        :param start_response:
        """
        return self.wsgi_app(environ, start_response)

    def route(self, url, **options):
        def wrapper(func):
            self.url_map.add(Rule(url, endpoint=func.__name__, **options))
            self.view_funcs[func.__name__] = func
            return func
        return wrapper

    def error_handler(self, error_code):
        def wrapper(func):
            self.error_handlers[error_code] = func
            return func
        return wrapper

    def wsgi_app(self, environ, start_response):
        # 使用上下文, 现在使用对资源的调用可以直接使用_request_ctx_stack
        with self.request_context(environ):
            # 原来这里是 rv = self.dispatch_request(environ)
            rv = self.dispatch_request()
            response = Response(rv)    # 构建Response
            return response(environ, start_response)    # 响应

    def dispatch_request(self):
        """通过environ找到视图函数 执行并返回其返回值
        """
        try:
            endpoint, args = self.match_request()
            return self.view_funcs[endpoint](**args)
        except HTTPException as e:
            handler = self.error_handlers[e.code]
            if handler:
                return handler()
            else:
                return e
        except Exception as e:
            handler = self.error_handlers[500]
            if self.debug or handler is None:
                raise
            else:
                return handler(e)

    @staticmethod
    def match_request():
        rv = _request_ctx_stack.top.url_adapter.match()
        return rv

    def request_context(self, environ):
        return _RequestContext(self, environ)


_request_ctx_stack = LocalStack()
from werkzeug import Request, Response
from werkzeug.local import LocalStack
from werkzeug.routing import Rule, Map


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
    def __init__(self, package_name):
        # 用来记录Rule的Map
        self.url_map = Map()

        # 用来匹配URL的Adapter
        self.url_adapter = None

        # key为endpoint, 也就是某个视图函数的标识符, 这里使用函数名作为endpoint. value为函数
        self.view_funcs = {}

        # 设置包名
        self.package_name = package_name

        # 临时的一个路由注册函数, 以后会删掉
        self.router_register()

    def __call__(self, environ, start_response):
        """程序的入口, 每次请求都会调用本函数, 实际的响应通过wsgi_app实现
        :param environ: 环境字典
        :param start_response:
        """
        return self.wsgi_app(environ, start_response)

    def router_register(self):
        def index1():
            return "index1"

        def index2():
            return "index2"
        self.url_map.add(Rule("/test/index1", endpoint=index1.__name__))
        self.view_funcs[index1.__name__] = index1
        self.url_map.add(Rule("/test/index2", endpoint=index2.__name__))
        self.view_funcs[index2.__name__] = index2

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
        endpoint, args = self.match_request()
        return self.view_funcs[endpoint](**args)

    @staticmethod
    def match_request():
        rv = _request_ctx_stack.top.url_adapter.match()
        return rv

    def request_context(self, environ):
        return _RequestContext(self, environ)


_request_ctx_stack = LocalStack()
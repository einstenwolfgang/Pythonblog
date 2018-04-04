import asyncio,os,json,time
from datetime import datetime
from aiohttp import web
import logging; logging.basicConfig(level=logging.INFO)
import jinja2


async def init(loop):
    app = web.Application(loop=loop,middlewares=[
    logger_factory, response_factory])
    app.router.add_route('GET','/',index)
    init_jinja2(app, filters=dict(datetime=datetime_filter))
    add_routes(app, 'handlers')
    add_static(app)
    srv = yield from loop.create_server(app.make_handler(),'127.0.0.1',9001)
    logging.info('server started at port 9001')
    return srv

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', headers={'content-type':'text/html'})

#自定义web框架中的get方法装饰器
def get(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
                return func(*args,**kw)
        wrapper.__method__ = 'GET'
        wrapper.__route__ = 'path'
        return wrapper
        return decorator

#自定义web框架中的post方法装饰器
def post(path):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
                return func(*args,**kw)
        wrapper.__method__ = 'POST'
        wrapper.__route__ = 'path'
        return wrapper
        return decorator

#定义关于不同request处理相应的生成器
class RequestHandler(object):
    def __init__(self, app, func):
        self._app = app
        self._func = func
        pass

    async def __call__(self,request):
        r = yield from self._func(**kw)
        return r

#各种方法添加入处理router序列
def add_route(app,fn):
    method = getattr(fn,'__method__',None)
    path = getattr(fn,'__path__',None)
    if method is None or path is None:
        raise ValueError('method not defined')
    if not asyncio.iscoroutine(fn) and not inspect.isgeneratorfunction(fn):
        fn = asyncio.coroutine(fn)
    app.router.add_route(method,path,RequestHandler(app,fn))

#批量化router序列加入
def add_routes(app,module_name):
    r = module_name.rind('.')
    if r == -1:
        mod = __import__(module_name,globals(),locals())
    else: 
        name = module_name[r+1:]
        mod = getattr(__import__(module_name[:r],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if  attr.startswith('_'):
            continue
        else: 
            fn = getattr(mod,attr)
            method = getattr(fn,'__method__',None)
            path = getattr(fn,'__path__',None)
            if method and path:
                add_route(app,fn)

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()


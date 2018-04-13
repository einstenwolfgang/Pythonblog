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

def init_jinja2(app,**kw):
    logging.info('init jinja2...')  
    # class Environment(**options)  
    # 配置options参数  
    options = dict(  
        # 自动转义xml/html的特殊字符  
        autoescape = kw.get('autoescape', True),  
        # 代码块的开始、结束标志  
        block_start_string = kw.get('block_start_string', '{%'),  
        block_end_string = kw.get('block_end_string', '%}'),  
        # 变量的开始、结束标志  
        variable_start_string = kw.get('variable_start_string', '{{'),  
        variable_end_string = kw.get('variable_end_string', '}}'),  
        # 自动加载修改后的模板文件  
        auto_reload = kw.get('auto_reload', True)  
    )  
    # 获取模板文件夹路径  
    path = kw.get('path', None)  
    if not path:  
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')  
    # Environment类是jinja2的核心类，用来保存配置、全局对象以及模板文件的路径  
    # FileSystemLoader类加载path路径中的模板文件  
    env = Environment(loader = FileSystemLoader(path), **options)  
    # 过滤器集合  
    filters = kw.get('filters', None)  
    if filters:  
        for name, f in filters.items():  
            # filters是Environment类的属性：过滤器字典  
            env.filters[name] = f  
    # 所有的一切是为了给app添加__templating__字段  
    # 前面将jinja2的环境配置都赋值给env了，这里再把env存入app的dict中，这样app就知道要到哪儿去找模板，怎么解析模板。  
    app['__template__'] = env # app是一个dict-like对象  

#编写一个过滤器
def datetime_filter(t):  
    delta = int(time.time() - t)  
    if delta < 60:  
        return u'1分钟前'  
    if delta < 3600:  
        return u'%s分钟前' % (delta//60)  
    if delta < 86400:  
        return u'%s小时前' % (delta//3600)  
    if delta < 604800:  
        return u'%s天前' % (delta//86400)  
    dt = datetime.fromtimestamp(t)  
    return u'%s年%s月%s日' % (dt.year, dt.month, dt.day) 

#提供静态文件夹的目录即可注册静态文件
def add_static(app):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    app.router.add_static('/static/',path)

#定义logger factory 用来记录URL信息
async def logger_factory(app,handler):
    async def logger(request):
        logging.info('Request has %s methond and %s path'% (request.method, request.path))
        return (yield from handler(request))
    return logger

def index(request):
    return web.Response(body=b'<h1>Awesome</h1>', headers={'content-type':'text/html'})

#定义middleware根据不同情况处理URL
async def response_factory(app, handler):
    async def response(request):
        # 结果:
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp = web.Response(body=r)
            resp.content_type = 'application/octet-stream'
            return resp
        if isinstance(r, str):
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r, dict):  
            # 在后续构造视图函数返回值时，会加入__template__值，用以选择渲染的模板  
            template = r.get('__template__', None)   
            if template is None: # 不带模板信息，返回json对象  
                resp = web.Response(body=json.dumps(r, ensure_ascii=False, default=lambda obj: obj.__dict__).encode('utf-8'))  
                # ensure_ascii：默认True，仅能输出ascii格式数据。故设置为False。  
                # default：r对象会先被传入default中的函数进行处理，然后才被序列化为json对象  
                # __dict__：以dict形式返回对象属性和值的映射  
                resp.content_type = 'application/json;charset=utf-8'  
                return resp  
            else: # 带模板信息，渲染模板  
                # app['__templating__']获取已初始化的Environment对象，调用get_template()方法返回Template对象  
                # 调用Template对象的render()方法，传入r渲染模板，返回unicode格式字符串，将其用utf-8编码  
                resp = web.Response(body=app['__template__'].get_template(template).render(**r))  
                resp.content_type = 'text/html;charset=utf-8' # utf-8编码的html格式  
                return resp
        if isinstance(r, int) and (600>r>=100):  
            resp = web.Response(status=r)  
            return resp  
        # 返回了一组响应代码和原因，如：(200, 'OK'), (404, 'Not Found')  
        if isinstance(r, tuple) and len(r) == 2:  
            status_code, message = r  
            if isinstance(status_code, int) and (600>status_code>=100):  
                resp = web.Response(status=r, text=str(message))  
        resp = web.Response(body=str(r).encode('utf-8')) # 均以上条件不满足，默认返回  
        resp.content_type = 'text/plain;charset=utf-8' # utf-8纯文本  
        return resp  
        
        # 返回了一组响应代码和原因，如：(200, 'OK'), (404, 'Not Found')  
        if isinstance(r, tuple) and len(r) == 2:  
            status_code, message = r  
            if isinstance(status_code, int) and (600>status_code>=100):  
                resp = web.Response(status=r, text=str(message))  
        resp = web.Response(body=str(r).encode('utf-8')) # 均以上条件不满足，默认返回  
        resp.content_type = 'text/plain;charset=utf-8' # utf-8纯文本  
        return resp  
    return response



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


def get_required_kw_args(fn):  # 获取无默认值的命名关键词参数  
    args = []  
    ''''' 
    def foo(a, b = 10, *c, d,**kw): pass 
    sig = inspect.signature(foo) ==> <Signature (a, b=10, *c, d, **kw)> 
    sig.parameters ==>  mappingproxy(OrderedDict([('a', <Parameter "a">), ...])) 
    sig.parameters.items() ==> odict_items([('a', <Parameter "a">), ...)]) 
    sig.parameters.values() ==>  odict_values([<Parameter "a">, ...]) 
    sig.parameters.keys() ==>  odict_keys(['a', 'b', 'c', 'd', 'kw']) 
    '''  
    params = inspect.signature(fn).parameters  
    for name, param in params.items():  
        # 如果视图函数存在命名关键字参数，且默认值为空，获取它的key（参数名）  
        if param.kind == inspect.Parameter.KEYWORD_ONLY and param.default == inspect.Parameter.empty:  
            args.append(name)  
    return tuple(args)  
  
def get_named_kw_args(fn):  # 获取命名关键词参数  
    args = []  
    params = inspect.signature(fn).parameters  
    for name, param in params.items():  
        if param.kind == inspect.Parameter.KEYWORD_ONLY:  
            args.append(name)  
    return tuple(args)  
  
def has_named_kw_arg(fn):  # 判断是否有命名关键词参数  
    params = inspect.signature(fn).parameters  
    for name, param in params.items():  
        if param.kind == inspect.Parameter.KEYWORD_ONLY:  
            return True  
  
def has_var_kw_arg(fn):  # 判断是否有关键词参数  
    params = inspect.signature(fn).parameters  
    for name, param in params.items():  
        if param.kind == inspect.Parameter.VAR_KEYWORD:  
            return True  
  
def has_request_arg(fn):   # 判断是否含有名叫'request'的参数，且位置在最后  
    params = inspect.signature(fn).parameters  
    found = False  
    for name, param in params.items():  
        if name == 'request':  
            found = True  
            continue  
        if found and (  
            param.kind != inspect.Parameter.VAR_POSITIONAL and   
            param.kind != inspect.Parameter.KEYWORD_ONLY and   
            param.kind != inspect.Parameter.VAR_KEYWORD):  
            # 若判断为True，表明param只能是位置参数。且该参数位于request之后，故不满足条件，报错。  
            raise ValueError('request parameter must be the last named parameter in function:%s%s' % (fn.__name__, str(sig)))  
    return found  


#定义关于不同request处理相应的生成器
class RequestHandler(object):  
    def __init__(self, app, fn):  
        self._app = app  
        self._func = fn  
        self._required_kw_args = get_required_kw_args(fn)  
        self._named_kw_args = get_named_kw_args(fn)  
        self._has_request_arg = has_request_arg(fn)  
        self._has_named_kw_arg = has_named_kw_arg(fn)  
        self._has_var_kw_arg = has_var_kw_arg(fn)  
  
    # 1.定义kw，用于保存参数  
    # 2.判断视图函数是否存在关键词参数，如果存在根据POST或者GET方法将request请求内容保存到kw  
    # 3.如果kw为空（说明request无请求内容），则将match_info列表里的资源映射给kw；若不为空，把命名关键词参数内容给kw  
    # 4.完善_has_request_arg和_required_kw_args属性  
    async def __call__(self, request):  
        kw = None # 定义kw，用于保存request中参数  
        if self._has_named_kw_arg or self._has_var_kw_arg: # 若视图函数有命名关键词或关键词参数  
            if request.method == 'POST':  
                # 根据request参数中的content_type使用不同解析方法：  
                if request.content_type == None: # 如果content_type不存在，返回400错误  
                    return web.HTTPBadRequest(text='Missing Content_Type.')  
                ct = request.content_type.lower() # 小写，便于检查  
                if ct.startwith('application/json'):  # json格式数据  
                    params = await request.json() # 仅解析body字段的json数据  
                    if not isinstance(params, dict): # request.json()返回dict对象  
                        return web.HTTPBadRequest(text='JSON body must be object.')  
                    kw = params  
                # form表单请求的编码形式  
                elif ct.startwith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):  
                    params = await request.post() # 返回post的内容中解析后的数据。dict-like对象。  
                    kw = dict(**params) # 组成dict，统一kw格式  
                else:  
                    return web.HTTPBadRequest(text='Unsupported Content-Type: %s' % request.content_type)  
            if request.method == 'GET':  
                qs = request.query_string # 返回URL查询语句，?后的键值。string形式。  
                if qs:  
                    kw = dict()  
                    ''''' 
                    解析url中?后面的键值对的内容 
                    qs = 'first=f,s&second=s' 
                    parse.parse_qs(qs, True).items() 
                    >>> dict([('first', ['f,s']), ('second', ['s'])]) 
                    '''  
                    for k, v in parse.parse_qs(qs, True).items(): # 返回查询变量和值的映射，dict对象。True表示不忽略空格。  
                        kw[k] = v[0]  
        if kw is None:  # 若request中无参数  
            # request.match_info返回dict对象。可变路由中的可变字段{variable}为参数名，传入request请求的path为值  
            # 若存在可变路由：/a/{name}/c，可匹配path为：/a/jack/c的request  
            # 则reqwuest.match_info返回{name = jack}  
            kw = dict(**request.match_info)  
        else: # request有参数  
            if self._has_named_kw_arg and (not self._has_var_kw_arg): # 若视图函数只有命名关键词参数没有关键词参数                 
                copy = dict()  
                # 只保留命名关键词参数  
                for name in self._named_kw_arg:  
                    if name in kw:  
                        copy[name] = kw[name]  
                kw = copy # kw中只存在命名关键词参数  
            # 将request.match_info中的参数传入kw  
            for k, v in request.match_info.items():  
                # 检查kw中的参数是否和match_info中的重复  
                if k in kw:  
                    logging.warn('Duplicate arg name in named arg and kw args: %s' % k)   
                kw[k] = v  
        if self._has_request_arg: # 视图函数存在request参数  
            kw['request'] = request  
        if self._required_kw_args: # 视图函数存在无默认值的命名关键词参数  
            for name in self._required_kw_args:  
                if not name in kw: # 若未传入必须参数值，报错。  
                    return web.HTTPBadRequest('Missing argument: %s' % name)  
        # 至此，kw为视图函数fn真正能调用的参数  
        # request请求中的参数，终于传递给了视图函数  
        logging.info('call with args: %s' % str(kw))  
        #try:  
        r = await self._func(**kw)  
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


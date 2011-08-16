""" view tests """
import sys, unittest
from martian.error import GrokImportError
from zope import interface, component
from zope.configuration.config import ConfigurationExecutionError

from webob.exc import HTTPForbidden, HTTPNotFound, HTTPFound
from webob.response import Response
from pyramid.interfaces import IView, IRequest
from pyramid.interfaces import IViewClassifier
from pyramid.interfaces import IAuthenticationPolicy

from memphis import config, view
from memphis.config import api
from memphis.view import meta
from memphis.view.base import View
from memphis.view.renderers import Renderer

from base import Base, Context


class BaseView(Base):

    def _setup_memphis(self):
        pass

    def _view(self, name, context, request):
        adapters = component.getSiteManager().adapters

        view_callable = adapters.lookup(
            (IViewClassifier, 
             interface.providedBy(request), 
             interface.providedBy(context)),
            IView, name=name, default=None)

        return view_callable(context, request)

       
class TestView(BaseView):

    def test_view_register_errs(self):
        self.assertRaises(
            ValueError, view.registerView, 'test.html', None)

        self.assertRaises(
            ValueError, view.registerView, 'test.html', {})

    def test_view_register_view(self):
        class MyView(view.View):
            def render(self):
                return '<html>view</html>'

        view.registerView('index.html', MyView)
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.status, '200 OK')
        self.assertEqual(v.content_type, 'text/html')
        self.assertEqual(v.body, '<html>view</html>')

    def test_view_register_declarative(self):
        class MyView(view.View):
            view.pyramidView('index.html')

            def render(self):
                return '<html>view</html>'

        view.registerView('index.html', MyView)
        self._init_memphis(
            {}, meta.PyramidViewGrokker().grok,  *('MyView', MyView))

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.status, '200 OK')
        self.assertEqual(v.content_type, 'text/html')
        self.assertEqual(v.body, '<html>view</html>')

    def test_view_register_view_err1(self):
        # default 'render' implementation
        class MyView(view.View):
            pass

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        context = Context()
        self.assertTrue(
            view.renderView('index.html', context, 
                            self.request).content_length ==0)

    def test_view_register_view_layout(self):
        class MyLayout(view.Layout):
            def render(self, rendered):
                return '<html>%s</html>'%rendered

        class MyView(view.View):
            def render(self):
                return 'test'

        view.registerView('index.html', MyView, Context)
        view.registerLayout('', Context, klass=MyLayout)
        self._init_memphis()

        context = Context()
        res = view.renderView('index.html', context, self.request)
        self.assertTrue('<html>test</html>' in res.body)

    def test_view_register_view_disable_layout1(self):
        class MyLayout(view.Layout):
            def render(self, rendered):
                return '<html>%s</html>'%rendered

        class MyView(view.View):
            def render(self):
                return 'test'

        view.registerView('index.html', MyView, Context, layout=None)
        view.registerLayout('', Context, klass=MyLayout)
        self._init_memphis()

        context = Context()
        res = view.renderView('index.html', context, self.request)
        self.assertEqual(res.body, 'test')

        v = MyView(None, self.request)
        self.assertEqual(MyLayout(v, None, self.request).render(
                v.render()), '<html>test</html>')

    def test_view_custom_response(self):
        class MyView(view.View):
            def render(self):
                response = self.request.response
                response.status = '202'
                return 'test'

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        res = view.renderView('index.html', Context(), self.request)
        self.assertEqual(res.status, '202 Accepted')
        self.assertEqual(res.body, 'test')

    def test_view_httpresp_from_update(self):
        class MyView(view.View):
            def update(self):
                raise HTTPForbidden()

        view.registerView('index.html', MyView, Context,
                          template = view.template('templates/test.pt'))
        self._init_memphis()

        self.assertRaises(
            HTTPForbidden,
            view.renderView, 'index.html', Context(), self.request)

    def test_view_httpresp_from_render(self):
        class MyView(view.View):
            def render(self):
                raise HTTPFound()

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        self.assertRaises(
            HTTPFound,
            view.renderView, 'index.html', Context(), self.request)

    def test_view_with_template(self):
        view.registerView(
            'index.html', view.View, Context,
            template=view.template('memphis.view.tests:templates/test.pt'))

        self._init_memphis()

        res = view.renderView('index.html', Context(), self.request)
        self.assertEqual(res.body, '<div>My pagelet</div>\n')

    def test_view_with_decorator(self):
        def deco(func):
            def func(context, request):
                return 'decorator'
            return func

        view.registerView(
            'index.html', view.View, Context, decorator = deco)

        self._init_memphis()

        res = view.renderView('index.html', Context(), self.request)
        self.assertEqual(res, 'decorator')

    def test_view_register_view_class_requestonly(self):
        class MyView(object):
            def __init__(self, request):
                self.request = request

            def render(self):
                return '<html>view: %s</html>'%(self.request is not None)

        view.registerView('index.html', MyView)
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>view: True</html>')

    def test_view_register_view_function(self):
        def render(context, request):
            return '<html>context: %s</html>'%(context is not None)

        view.registerView('index.html', render)
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>context: True</html>')

    def test_view_register_view_function_requestonly(self):
        def render(request):
            return '<html>request: %s</html>'%(request is not None)

        view.registerView('index.html', render)
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>request: True</html>')

    def test_view_register_view_function_with_template(self):
        def render(context, request):
            return {}

        view.registerView('index.html', render,
                          template = view.template('templates/test.pt'))
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<div>My pagelet</div>\n')

    def test_view_register_view_function_requestonly_template(self):
        def render(request):
            return {}

        view.registerView('index.html', render,
                          template = view.template('templates/test.pt'))
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<div>My pagelet</div>\n')

    def test_view_register_secured_view(self):
        def render(request):
            return '<html>Secured view</html>'

        view.registerView('index.html', render,
                          permission = 'Protected')

        class SimpleAuth(object):
            interface.implements(IAuthenticationPolicy)
       
            allowed = False
       
            def effective_principals(self, request):
                return (1,2)
       
            def permits(self, context, princials, permission):
                return self.allowed

        component.getSiteManager().registerUtility(
            SimpleAuth(), IAuthenticationPolicy)

        self._init_memphis()

        context = Context()
        self.assertRaises(
            HTTPForbidden,
            self._view, 'index.html', context, self.request)

        SimpleAuth.allowed = True
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>Secured view</html>')

    def test_view_register_default_view(self):
        def render(request):
            return '<html>content</html>'

        view.registerView('index.html', render, default = True)
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>content</html>')

        v = self._view('', context, self.request)
        self.assertEqual(v.body, '<html>content</html>')

    def test_view_register_default_view_seperate_reg(self):
        def render(request):
            return '<html>content</html>'

        view.registerView('index.html', render)
        view.registerDefaultView('index.html')
        self._init_memphis()

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>content</html>')

        v = self._view('', context, self.request)
        self.assertEqual(v.body, '<html>content</html>')

    def test_view_function(self):
        self._init_memphis()

        config.action.immediately = True

        class f(object):
            def __init__(self):
                d = {}
                self.f_locals = d
                self.f_globals = d

        @view.pyramidView('index.html', frame=f())
        def render(request):
            return '<html>content</html>'

        context = Context()
        v = self._view('index.html', context, self.request)
        self.assertEqual(v.body, '<html>content</html>')

        config.action.immediately = False

    def test_view_function_err(self):
        self.assertRaises(
            GrokImportError,
            view.pyramidView, 'index.html')


class TestSubpathView(BaseView):

    def test_view_subpath(self):
        class MyView(view.View):
            @view.subpath
            def validate(self):
                return 'Validate method'

            def render(self):
                return 'Render method'

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        v = self._view('index.html', Context(), self.request)
        self.assertEqual(v.body, 'Render method')

        self.request.subpath = ('validate',)
        v = self._view('index.html', Context(), self.request)
        self.assertTrue(isinstance(v, str))       
        self.assertEqual(v, 'Validate method')

    def test_view_subpath_call(self):
        class MyView(view.View):
            @view.subpath()
            def validate(self):
                return 'Validate method'

            def render(self):
                return 'Render method'

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        v = self._view('index.html', Context(), self.request)
        self.assertEqual(v.body, 'Render method')

        self.request.subpath = ('validate',)
        v = self._view('index.html', Context(), self.request)
        self.assertTrue(isinstance(v, str))       
        self.assertEqual(v, 'Validate method')

    def test_view_subpath_json_renderer(self):
        class MyView(view.View):
            @view.subpath(renderer=view.json)
            def validate(self):
                return {'text': 'Validate method'}

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        self.request.subpath = ('validate',)
        v = self._view('index.html', Context(), self.request)
        self.assertTrue(isinstance(v, Response))
        self.assertEqual(v.body, '{"text": "Validate method"}')

    def test_view_subpath_custom_name(self):
        class MyView(view.View):
            @view.subpath(name='test')
            def validate(self):
                return 'Validate method'

            def render(self):
                return 'Render method'

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        self.request.subpath = ('validate',)
        v = self._view('index.html', Context(), self.request)
        self.assertTrue(isinstance(v, Response))       
        self.assertEqual(v.body, 'Render method')

        self.request.subpath = ('test',)
        v = self._view('index.html', Context(), self.request)
        self.assertTrue(isinstance(v, str))       
        self.assertEqual(v, 'Validate method')

    def test_view_subpath_class_requestonly(self):
        class MyView(object):
            def __init__(self, request):
                self.request = request

            @view.subpath()
            def validate(self):
                return 'Validate method: %s'%(self.request is not None)

            def render(self):
                return 'Render method'

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        v = self._view('index.html', Context(), self.request)
        self.assertEqual(v.body, 'Render method')

        self.request.subpath = ('validate',)
        v = self._view('index.html', Context(), self.request)
        self.assertTrue(isinstance(v, str))       
        self.assertEqual(v, 'Validate method: True')

    def test_view_subpath_with_template(self):
        class MyView(view.View):
            @view.subpath(renderer=Renderer(view.template('templates/test.pt')))
            def validate(self):
                return {}

        view.registerView('index.html', MyView, Context)
        self._init_memphis()

        self.request.subpath = ('validate',)
        v = self._view('index.html', Context(), self.request)
        self.assertEqual(v.body, '<div>My pagelet</div>\n')

    def test_view_subpath_err(self):
        sp = view.subpath()
        self.assertRaises(
            ValueError,
            sp, self.test_view_subpath_err, sys._getframe(1))

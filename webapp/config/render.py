# -*- coding: utf-8 -*-

"""A Jinja Handler and tool.  This code is in the public domain.

Adapted from martinrusev https://github.com/martinrusev

Usage:
@cherrypy.expose
@cherrypy.tools.jinja(filename='index.html')
def controller(**kwargs):
    return {

    } # This dict is the template context     

"""
import cherrypy
import jinja2
import os
from jinja2 import evalcontextfilter, escape
from webapp.config import DATADIR
#import re

#from settings import TEMPLATES_DIR
TEMPLATES_DIR = os.path.join(DATADIR, 'templates')

#_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@evalcontextfilter
def nl2br(eval_ctx, value):
#TODO: Not "road legal"
#    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br/>\n')
#                          for p in _paragraph_re.split(escape(value)))
    return value.replace('\n', '<br/>\n')
    
@evalcontextfilter
def convert_type(eval_ctx, type = 0):
    types = ['Prepend', 'Content', 'Append']
    return types[type]
    
class JinjaHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body."""

    def __init__(self, env, template_name, next_handler):
        self.env = env
        self.template_name = template_name
        self.next_handler = next_handler

    def __call__(self):
        context = {}
        try:
            r = self.next_handler()
            context.update(r)
        except ValueError, e:
            cherrypy.log('%s (handler for "%s" returned "%s")\n' % (
                e, self.template_name, repr(r)), traceback=True)

        context.update({
            'request': cherrypy.request,
            'app_url': cherrypy.request.app.script_name,
        })

        cherrypy.request.template = tmpl = self.env.get_template(self.template_name)
        output = tmpl.render(**context)

        return output

class JinjaLoader(object):
    """A CherryPy 3 Tool for loading Jinja templates."""

    def __init__(self, templates=''):

        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(TEMPLATES_DIR))
        self.env.filters['nl2br'] = nl2br
        self.env.filters['convert_type'] = convert_type
        

    def __call__(self, template):
        cherrypy.request.handler = JinjaHandler(self.env, template, cherrypy.request.handler)

    def add_filter(self, func):
        """Decorator which adds the given function to jinja's filters."""
        self.env.filters[func.__name__] = func

        return func

    def add_global(self, func):
        """Decorator which adds the given function to jinja's globals."""
        self.env.globals[func.__name__] = func

        return func

loader = JinjaLoader()
cherrypy.tools.jinja = cherrypy.Tool('on_start_resource', loader)
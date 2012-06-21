# -*- coding: utf-8 -*-

import cherrypy
import routes
from jobs import ServiceLock, SystemLockedException
from cgi import escape as escape # Used to escape HTML content

def base():
    host = 'http://' + cherrypy.request.headers.get('host')
    base = cherrypy.config.get('config').get('global', 'urlbase')
    base = host + '/' + base if base else host

    return base

def url(*args, **kwargs):
    return cherrypy.url(routes.url_for(*args, **kwargs), base = base())

def redirect(url):
    url = url if url else base()
    raise cherrypy.HTTPRedirect(url)

def escape_string(text):
    """ Escapes html string to avoid XSS errors """
    return escape(text)
    

class BaseController:
    """ Base controller for Snortmanager. Provides necassary functionality for all objects."""
    globals = {
        'url': url,	
    }

    def __init__(self):
        """ Does nothing. """
        pass
       # self.cron = cherrypy.config.get('cron')
       # self.searchers = cherrypy.config.get('searchers')
       # self.flash = self.globals['flash'] = cherrypy.config.get('flash')
       # self.globals['debug'] = cherrypy.config.get('debug')
       # self.globals['updater'] = cherrypy.config.get('updater')
       # self.globals['searchers'] = self.searchers
       # self.globals['cherrypy'] = cherrypy
       
    def check_status(self):
        """ Check that service is not locked """
        
        if ServiceLock.is_locked():
            raise SystemLockedException('System is locked by background job')

    def render(self, list):
        """ Global rendrer, check specific items before returning data. """

        if ServiceLock.is_locked():
            list['service_lock'] = True
        return list

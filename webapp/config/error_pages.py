# -*- coding: utf-8 -*-

""" Creates the ability to add custom error pages to Snortmanager."""

try:
    import cherrypy
    from webapp.controller import BaseController, url, redirect
    import os
except ImportError as e:
	print 'Error while importing error in', __file__
	print e
	exit(1)

TEMPLATES = 'templates/errors'

#@cherrypy.tools.jinja(template='errors/404.html')    
#def error_page_404(status, message, traceback, version):


def init_errors():

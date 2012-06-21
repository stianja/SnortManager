# -*- coding: utf-8 -*-

try:
    from webapp.controller import BaseController, url, redirect
    from webapp.config.dbconfig import Session, EventLog
    from sqlalchemy.orm import query
    import cherrypy
except ImportError as e: #If there's an error
    print 'There was a importerror in', __file__
    print e


class MainController(BaseController):
    """ Provides the functionality for the main parts of Snortmanager. """

    
    @cherrypy.expose
    @cherrypy.tools.jinja(template='main/index.html')
    def index(self):
        """ Returns a list of the 10 last log events. """
        event_content = Session.query(EventLog).limit(10)
        
        return (self.render({ 'page_title': 'Main page', 'event_content': event_content}))

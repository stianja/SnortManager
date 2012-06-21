# -*- coding: utf-8 -*-

""" Provides the funcionality to edit information about rules and sources. """

try:
	from webapp.controller import BaseController, url, redirect
	from webapp.config.dbconfig import Session, UpdateSource, UpdateFilter
	import cherrypy
except ImportError as e: #If there's an error
	print 'There was a importerror in', __file__
	print e


class RuleController(BaseController):

    @cherrypy.expose
    @cherrypy.tools.jinja(template='rules/index.html')
    def index(self):
        """ Returns a list of sources.
        
        Landing page for Snort rule sources, returns a list of all the sources registered in the system.
        """
        sources = Session.query(UpdateSource)
        
        return (self.render({ 'page_title': 'Rules', 'sources': sources }))
        
    @cherrypy.expose
    @cherrypy.tools.jinja(template='rules/register_source.html')
    def source(self, id = 0):
        """ Returns interface to add Snort sources. """
    	source_url = None
        
    	if id is not 0:
    	    source_url = Session.query(UpdateSource).get(id)
    	    
    	    
    	return { 'page_title': 'Rules', 'source_url': source_url}
    
    @cherrypy.expose
    def register_source(self, **kwargs):
        """ Register source data, and adds to database. 
        
        If source exsists, it will be updated. If the source does not excist it will be added.
        """


        try: # Check if source is active, deactivate if necessary.
            if 'active' not in kwargs or kwargs['active'] == 'off':
                active = 0
            else:
                active = 1
                
            url = kwargs['source-url']
        except KeyError:
            raise

        if 'source-id' in kwargs:
            id = kwargs['source-id']
        else:
            id = None
         

    	if id:
    	    sourceUrl = Session.query(UpdateSource).get(id)
    	    sourceUrl.url = url
    	    sourceUrl.active = active
    	else:
            sourceUrl = UpdateSource(active, url)
    	Session.merge(sourceUrl)
    	
    	raise cherrypy.HTTPRedirect('/rules/')
		
	

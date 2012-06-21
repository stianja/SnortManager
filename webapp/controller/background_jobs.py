# -*- coding: utf-8 -*-

try:
    import cherrypy
    from webapp.controller import BaseController, url, redirect
#    from webapp.config.dbconfig import Session, Sensor
#    from sqlalchemy import *
    from jobs.rules.updater import update_snort_rules
    from jobs.policy.policyproducer import produce_configuration_files
    from webapp.config.scheduler import snort_scheduler
    import threading
    from time import sleep
except ImportError as e: #If there's an error
	print 'There was a importerror in', __file__
	print e
	exit(2)
################################################

class JobsController(BaseController):
    """ Provides the interface to start jobs and change scheduled tasks. """
    def __init__(self):

        self.available_tasks = {'update_rules': update_snort_rules,
        'create_configuration_files': produce_configuration_files}

##################################################    
    @cherrypy.expose
    @cherrypy.tools.jinja(template='background_jobs/index.html')
    def index(self):
        """ Returns the interface for starting background jobs. """ 
   
        return (self.render({ 'page_title': 'Background jobs'}))

    @cherrypy.expose
    def start_job(self, **kwargs):
        """ Starts a background job 
        
        Starts a background task based on user input. Checks if task is allowed.
        """
        for key in kwargs.iterkeys():
            if key in self.available_tasks:
                target_task = self.available_tasks[key]
                threading.Thread(target=target_task, name=target_task).start()
                break
    
    @cherrypy.expose
    @cherrypy.tools.jinja()
    def schedule(self):
        """ Retuns a list of Schedued tasks """
        jobs = []
        for job in snort_scheduler.get_jobs():
            jobs.append({'name' : job.name,
            'trigger' : job.trigger
            })
            
        return {'page_title' : 'Schedule', 'jobs' : jobs}
    
    
        
    
    
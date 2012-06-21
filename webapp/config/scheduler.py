# -*- coding: utf-8 -*-

""" Provides the functionality to schedule tasks. """

try:
    from apscheduler.scheduler import Scheduler
    from cherrypy.process.plugins import SimplePlugin
    from cherrypy import engine
    from jobs.rules.updater import update_snort_rules
    from jobs.policy.policyproducer import produce_configuration_files
    from webapp.config.dbconfig import ScheduleStore
except ImportError as e:
    print 'Error while importing dependencies for file %s' % __file__
    print 'Error message: %s\n\nExiting program!' % e
    exit(1)

class SnortScheduler(SimplePlugin):
    """ Enables Schduling for Snortmanager """
    
    scheduler = None # The APS instance
    
    def __init__(self, bus):
        """ Initiates scheduler. """
        SimplePlugin.__init__(self, bus)
        self.scheduler = Scheduler()
        
    def __initiate_jobs(self):
        """ Adds schedueled tasks if database is empty. """
        sched = self.scheduler
        sched.add_cron_job(update_snort_rules, hour = 7, jobstore='sql')
        sched.add_cron_job(produce_configuration_files, hour = 9, jobstore='sql')
        
    def start(self):
        """ Intitates scheduler when Snortmanager starts """
        sched = self.scheduler
        sched.add_jobstore(ScheduleStore(), 'sql')
        if len(sched.get_jobs()) is 0:
            self.__initiate_jobs()
        sched.start()
    
    def stop(self):
        """ Stops Scheduler service when thread dies. """
        self.scheduler.shutdown(wait=False)
        
    def restart(self):
        """ Restarts the service if necassary. """
        self.stop()
        self.start()
    
    def get_jobs(self):
        return self.scheduler.get_jobs()

snort_scheduler = SnortScheduler(engine)
    
def initiate_scheduler(bus):
#    snort_scheduler = SnortScheduler(bus)
    snort_scheduler.subscribe()
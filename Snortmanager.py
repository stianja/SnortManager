# -*- coding: utf-8 -*-

"""

Main administrations script for the Snortmanager utility. Gives the ability to start server, make a daemon and run tasks

Created by Christer Vaskinn and Kristian Wikestad

"""



import os
import sys


TEMPLATES = 'templates/'

rundir = os.path.dirname(os.path.abspath(__file__))

try:
    frozen = sys.frozen
except AttributeError:
    frozen = False

# Define path based on frozen state
if frozen:
    path_base = os.environ['_MEIPASS2']
    rundir = os.path.dirname(sys.executable)
else:
    path_base = rundir

# Include paths
sys.path.insert(0, path_base)
sys.path.insert(0, os.path.join(path_base, 'library'))

try:
    """ Initiliazes paths and SQL credentials. """
    import webapp.config
    import cherrypy
    webapp.config.DATADIR = rundir
    webapp.config.VARDIR = os.path.join(rundir, 'var')
    
    pid_file = os.path.join(webapp.config.VARDIR, 'snort_daemon.pid')
    cherrypy.config.update(os.path.join(rundir, 'configuration.conf')) # Database and global config
    
    _db_credentials = {'driver': cherrypy.config.get('db_driver'),
        'host': cherrypy.config.get('db_host'),
        'name': cherrypy.config.get('db_name'),
        'username': cherrypy.config.get('db_username'),
        'password': cherrypy.config.get('db_password')}
        
    sql_server = '%s://%s:%s@%s/%s' % (_db_credentials['driver'],
                                           _db_credentials['password'],
                                           _db_credentials['username'],
                                           _db_credentials['host'],
                                           _db_credentials['name'])
    webapp.config.SQLSTRING = sql_server
           
                                           
        
        
except KeyError as e:
    print 'There was an error while configuring database %s' % e
    print 'Can\'t connect to database'
    exit(1)
except ImportError:
    print 'Error while setting variables'

try:
    from argparse import ArgumentParser
    from jobs import ServiceLock, SystemLockedException
    import webapp.config.render
    from webapp.config.routes import initialize_routes as Disp # Get the custom dispatcher
    import webapp.config
    from webapp.config.scheduler import initiate_scheduler
    from jobs.rules.updater import update_snort_rules
    from jobs.policy.policyproducer import produce_configuration_files
    from cherrypy.process import plugins
    import signal
except ImportError as e:    # Exits if there's an error
    print 'There was an error while importing modules in', __file__
    print e
    exit(1)

def snortmanager_status():
    """ Check if PID file exsists, return contents if true. """
    try:
        f = open(pid_file).read()
        return int(f)
    except IOError:
        return 0

def main():

    parser = ArgumentParser(description='Administration script for the Snortmanager uility')    
    parser.add_argument('-d',action='store_true',dest='daemonize',help='Run server as a daemon')
    parser.add_argument('-u',action='store_true',dest='update',help='Update rules from sources')
    parser.add_argument('-p',action='store_true',dest='policychain',help='Produce and push policy chain')
    parser.add_argument('-s',action='store_true',dest='silent',help='Silent operation, log nothing to screen')
    parser.add_argument('--status',action='store_true',dest='status',help='Check the running status of Snortmanager')
    parser.add_argument('--stop',action='store_true',dest='stop',help='Stop Snortmanager if running as daemon')
    args = parser.parse_args()

    from webapp.config.dbconfig import init_database
    init_database()

    
    if args.update:
        
        print 'Starting download of Rules'
        update_snort_rules()
        exit(0)
    
    if args.policychain:
        if ServiceLock.is_locked():
            print 'This system is locked for changes'

        print 'Producing policychains'
#        produce_configuration_files()
        exit(0)
    
    running_state = snortmanager_status()
        
    if args.status:
        if running_state:
            print 'Snortmanager is running. PID: %i' % running_state
        else:
            print 'Snortmanger is not running'

        exit(0)
    
    if args.stop:
        if running_state: # Potentiel sikkerhetsfeil
            print 'Shutting down snortmanager'
            os.kill(running_state, signal.SIGTERM)
            running_state = 0

            try:
                os.remove(pid_file)
            except OSError as e:
                print 'Error while removing PID file: %s' % e
                
            exit(0)
        else:
            print 'Snortmanager is not running'
            exit(1)

    configuration = os.path.join(rundir, 'webapp.conf')
    configuration = {
        '/': {
            'request.dispatch': Disp(),
            'tools.staticfile.root': rundir,
            'tools.sessions.on':  True,
            'tools.sessions.timeout': 240,
            'tools.gzip.on': True,
            'tools.gzip.mime_types': ['text/html', 'text/plain', 'text/css', 'text/javascript', 'application/javascript'],
            'tools.trailing_slash.on': True,
            'tools.trailing_slash.missing': False,
            'tools.trailing_slash.extra': True
            },
        '/favicon.ico': {
            'tools.staticfile.on': True,
            'tools.staticfile.filename' : 'resources/favicon.ico'
            },
        '/stylesheet.css' : {
            'tools.staticfile.on': True,
            'tools.staticfile.filename': 'resources/stylesheet/stylesheet.css'
        },
        '/resources': {
        	'tools.staticdir.on': True,
        	'tools.staticdir.root': rundir,
        	'tools.staticdir.dir': 'resources'
        	}
    }

    if args.daemonize:
        if running_state:
            print 'Snortmanager is already running as daemon! PID: %i' % running_state
            exit(1)
        print 'Starting Snortmanager as Daemon'
        plugins.Daemonizer(cherrypy.engine).subscribe()
        
        plugins.PIDFile(cherrypy.engine, pid_file).subscribe()

    # Neceassary to create a PID file   
    """
    if args.pid_file:
        plugins.PIDFile(cherrypy.engine, options.pid_file).subscribe()
    """    
    
    if args.silent or args.daemonize:
        cherrypy.config.update({'log.screen': False})
    else:
        cherrypy.config.update({'log.screen': True})
        
    try:
        cherrypy.config.update({
        'global': {
        'basePath': path_base,
        'runPath': rundir,
        'error_page.404':  os.path.join(TEMPLATES, "errors/404.html")
        

        }
    })
    
        initiate_scheduler(cherrypy.engine)
        cherrypy.tree.mount(None, config=configuration)
        cherrypy.engine.start()
        cherrypy.engine.block()
    except Exception as e:
        print e
        sys.exit(1)


if __name__ == '__main__':
    main()

# -*- coding: utf-8 -*-

""" The functionality necassary for the Sensor module """

try:
    import cherrypy
    from webapp.controller import BaseController, url, redirect, escape_string
    from webapp.config.dbconfig import Session, Sensor, SensorLocation
    from webapp.config.log import debug, info, warning, error, critical
    from sqlalchemy import *
    from sqlalchemy.orm import subqueryload
    from sqlalchemy.orm.exc import NoResultFound 
    from sqlalchemy.orm.exc import MultipleResultsFound 
    from webapp.config.log import debug, info, warning, error, critical    
    import simplejson
except ImportError as e: #If there's an error
	print 'There was a importerror in', __file__
	print e

################################################

class SensorController():
    """ Presents the neceassry content and functionality for manipulation of Sensors """
    def _create_sidemenu(self):
        sidecontent = [
        {'href' : '#', 'text' : 'List Sensors'},
        {'href' : 'addsensor', 'text' : 'Add Sensor'},
        {'href' : '#', 'text' : 'Edit Sensor'},
        {'href' : '#', 'text' : 'Delete Sensor'}, 
		]
        sidemenu = {'title' : 'Sensor',
        'content' : sidecontent}
		
        return sidemenu
##################################################    
    @cherrypy.expose
    @cherrypy.tools.jinja(template='sensor/index.html')
    def index(self):
        """ The main page shown for sensor, lists all activated sensors, grouped by location. """
        
        location_list = Session.query(SensorLocation)\
                 .join(Sensor)\
                 .filter(Sensor.active == 1)\
                 .all()
        
        locations = Session.query(SensorLocation).all()
        
        return ({ 'page_title': 'Sensor', 'secondmenu': self._create_sidemenu(),
         'location_list' : location_list, 'locations' : locations})
#################################################
    @cherrypy.expose
    def delete_sensor(self, **kwargs):
        """ Deactivates a sensor in the system. """
        try:
            id = kwargs['sensor_id']
            sensor = Session.query(Sensor).filter(Sensor.id == id).one()
            sensor.active = 0
            Session.merge(sensor)
            Session.flush()
        except NoResultFound:
            print 'No result found'
        except KeyError as e:
            print 'Key error occured %s' % e

#################################################
    @cherrypy.expose
    @cherrypy.tools.jinja(template='sensor/addsensor.html')
    def addsensorindex(self):
        """ Add a new sensor to the database"""
        
        locations = Session.query(SensorLocation).all()
   
        return ({ 'page_title': 'Add Sensor', 'secondmenu': self._create_sidemenu(), 'locations' : locations})
###################################################

    @cherrypy.expose
    def get_sensor_data(self, id):
        """ Returns a JSON string containing a sensors data.
        
        This function takes a sensors ID as paramater, and providing it exists will return all its data as JSON string.
        
        The function is used by AJAX to populate forms. """
        try:
            if not id.isdigit():
                raise TypeError
            
            sensor = Session.query(Sensor).filter(Sensor.id == id).one()
        except TypeError:
            print 'Type error occured'
        except NoResultFound:
            print 'No result found'
                    
        return simplejson.dumps(sensor.make_json())

###################################################

    @cherrypy.expose
    def save_sensor_data(self, **kwargs):
        """ Get a sensors data provided bu a form, and either change it or add new. """
     
        try:
            """ Retrieves information from web request. """
            addName = escape_string(kwargs['sensor_name'])
            addIp = escape_string(kwargs['sensor_ip'])
            addLocation = kwargs['sensor_location']
            addDescription = escape_string(kwargs['sensor_description'])
            sensor_id = kwargs['sensor_id']
        except KeyError as e:
            print 'There was a key error %s' % (e)

        
        try: 
            """ In case sensor does not excist. """
            if sensor_id == 0:    
                raise NoResultFound
                
            sensor = Session.query(Sensor).filter(Sensor.id == sensor_id).one()
            sensor.name = addName
            sensor.ip = addIp
            sensor.description = addDescription
            
            Session.merge(sensor)
            
        except NoResultFound: # Sensor does not exsist, add new.
            new_sensor = Sensor(addName, addIp, addLocation, addDescription)
            Session.add(new_sensor)
        finally:
            Session.flush()
        
        Session.flush()

    @cherrypy.expose
    def add_location(self, **kwargs):
        """ Adds a new location to the database """
        try:
            name = escape_string(kwargs['location_name'])
            
            if len(name) == 0:
               raise TypeError('The location name is empty!')            
            
            new_location = SensorLocation(name)
            
            Session.add(new_location)
            Session.flush()
            
            print new_location
            return simplejson.dumps(new_location.id)
            
        except KeyError as e:
            print 'KEYERROR; this key does not excist: %s' % s
        except TypeError as e:
            print e

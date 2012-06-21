# -*- coding: utf-8 -*-

""" Contains the classes to define database tables and the infrastructure to open connections to the database. """

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import mapper, relation, scoped_session, relationship
    from sqlalchemy.orm.session import sessionmaker
    from sqlalchemy.orm.exc import NoResultFound
    from sqlalchemy.exc import OperationalError
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.schema import MetaData, Table, Column, ForeignKey
    from sqlalchemy.sql.expression import and_, desc
    from sqlalchemy.types import Integer, DateTime, String, Boolean, Text, DateTime
    from sqlalchemy.dialects.mysql import INTEGER
    from jobs.rules.Parser.RuleParser import Rule as SnortRule
    from datetime import datetime # To create datetimestamp
    from apscheduler.jobstores.sqlalchemy_store import SQLAlchemyJobStore
    from webapp.config.log import debug, info, warning, error, critical
    from webapp.config import SQLSTRING, DATADIR
    import cherrypy

except ImportError as e:
    print 'Error while importing modules in:', __file__
    print e
    exit(1)

class RootObjectException(Exception):
    """ The exception thrown if there's an error with the root object."""
    def __init__(self, message):
        self.message = message
        
    def __str__(self):
        return repr(self.message)

        
try:
    engine = create_engine(SQLSTRING, echo=False, pool_recycle=3600)
    metadata = MetaData(engine)
    Session = scoped_session(sessionmaker(bind = engine, autocommit = True))
except OperationalError as e:
	print 'Error while connection to database, shutting down!'
	print e
	exit(1)
	
# Start creating those tables

Base = declarative_base()

## Rules table
class UpdateLog(Base):
    """ The declarative class for the database table to create logs.

    The class contains the attributes and structure of the UpdateLog
    """
    __tablename__ = 'Updates'
    
    id = Column('id', Integer, primary_key = True, autoincrement = True)
    urlid = Column('urlid', Integer, ForeignKey('UpdateSource.id'), nullable = False)
    timestamp = Column('timestamp', DateTime, nullable = False)

    def __init__(self, urlid, timestamp):
        """ Contructor for the """
        self.urlid = urlid
        self.timestamp = timestamp
    
    def __repr__(self):
        return "<UpdateLog('%i', '%i', %s')>" % (self.id, self.urlid, self.timestamp)	
	
class UpdateSource(Base):
    """ The declarative class for the database table UpdateSources.

    The class contains the attributes and structure of the UpdateSources
    """
    __tablename__ = 'UpdateSource'
    id = Column('id', Integer, primary_key = True, autoincrement = True)
    active = Column('active', Integer, nullable = False, default = 1)
    url = Column('url', String(256), nullable=False)
     
    def __init__(self, active, url):
        self.active = active
        self.url = url

    def is_active(self):
        if self.active > 0:
            return 'Active'
        else:
            return 'Inactive'

    def __repr__(self):
        return "<UpdateSource(%i, %i, '%s')>" % (self.id, self.active, self.url)
         
         
class UpdateFilter(Base):
    """ The declarative class for the database table UpdateFilter.

    The class contains the attributes and structure of the UpdateFilter
    """
    __tablename__ = 'UpdateFileFilter'
    
    updateurl = Column('updateurl', Integer, ForeignKey('UpdateSource.id'),
                                primary_key = True, autoincrement = False)
    path = Column('path', String(64), primary_key = True, autoincrement = False)
    
    def __init__(self, updateurl, path):
        self.updateurl = updateurl
        self.path = path

	def __repr__(self):
	    return "<UpdateFilter(%i, '%s')>" % (self.updateurl, self.path)


class UpdateFile(Base):
    """ The declarative class for the database table UpdateFile.

    The class contains the attributes and structure of the UpdateFile
    """
    __tablename__ = 'UpdateFile'
    
    id = Column('id', Integer, primary_key = True)
    name = Column('name', String(128), nullable = False)
    path = Column('path', String(128))
    updatesource = Column('updatesource', Integer, ForeignKey('UpdateSource.id'))

    def __init__(self, name, updatesource, path = None):
        self.name = name
        self.path = path
        self.updatesource = updatesource
        
    
    
    def __repr_(self):
        return "<UpdateFile(%i, '%s', '%s', %i)>" % (self.id, self.name, self.path, self.updatesource)
       
       
class Rule(Base):
    """ The declarative class for the database table Rule.

    The class contains the attributes and structure of the Rule.
    """
    __tablename__ = 'Rules'
    
    id = Column('id', Integer, primary_key = True, autoincrement = True)
    active = Column('active', Integer, default=1)
    file = Column('file', Integer, ForeignKey('UpdateFile.id'))
    sid = Column('sid', Integer, nullable = False)
    rev = Column('rev', Integer, nullable = False)
    rule = Column('rule', Text, nullable = False)
    
    def __init__(self, active, file, sid, rev, rule):
        self.active = active
        self.file = file
        self.sid = sid
        self.rev = rev
        self.rule = rule

    def __init__(self, SnortRule, fileid):
        self.active = SnortRule.active
        self.file = fileid
        self.sid = SnortRule.sid
        self.rev = SnortRule.rev
        self.rule = SnortRule.raw

    def is_active(self):
        if self.active > 0:
            return 'Active'
        else:
            return 'Inactive'
     
    def __str__(self):
    	print 'SID: %s\n REV: %s \n Active: %s' % (self.sid, self.rev, self.is_active())
    	print 'File ID: %i' % (self.file)
    	print self.rule

    def __repr__(self):
        return "<Rule(%i, %i, %i, %i,'%s')>" % (self.sid, self.rev, self.active, self.file, self.rule)


class Group(Base):
    """ The declarative class for the database table Group.

    The class contains the attributes and structure of the Group.
    """
    __tablename__ = 'Group'
    
    id = Column('id', Integer, primary_key = True, autoincrement = True)
    name = Column('name', String(64), nullable=False)
    description = Column('description', String(256))
    
    def __init__(self, name, description):
        self.name = name
        self.description = description
        
    def __repr__(self):
        return "<Group(%i, '%s', '%s')>" % (self.id, self.name, self.description)


class User(Base):
    """ The declarative class for the database table User.

    The class contains the attributes and structure of the User.
    """
    __tablename__ = 'User'
    id = Column('id', Integer, primary_key = True, autoincrement = True)
    group = Column('group', Integer, ForeignKey(Group.id))
    username = Column('username', String(64), nullable = False)
    email = Column('email', String(128), nullable = False)
    password = Column('password', String(512), nullable = False)
   

    def __init__(self, group, username, email, password):
        self.group = group
        self.username = username
        self.email = email
        self.password = password
        
    def __repr__(self):
        return "<User(%i, '%s', '%s', '%s')>" % (self.group, self.username, self.email, self.password)


class PolicyChainMeta(Base):
    """ The declarative class for the database table PolicyChainMeta.

    The class contains the attributes and structure of the PolicyChainMeta.
    """
    __tablename__ = 'PolicyChainMeta'
    
    id = Column('id', INTEGER(unsigned = True), primary_key=True) # Has capitol integer because of unsigned
    name = Column('name', String(128), nullable=False)
    active = Column('active', Integer, nullable=False, default = 1)
    description = Column('description', Text)
    
    def __init__(self, name, description=None):
        self.name = name
        self.description = description
        
    
    def __repr__(self):
        return "<PolicyChainMeta(%i, '%s', '%s')>" % (self.id, self.name, self.description)
      
      
class PolicyObject(Base):
    """ The declarative class for the database table PolicyObject.

    The class contains the attributes and structure of the PolicyObject
    """
    __tablename__ = 'PolicyObject'
    
    id = Column('id', INTEGER(unsigned = True), primary_key=True)
    active = Column('active', INTEGER(unsigned = True), default=0, nullable=False)
    type = Column('type', Integer(), default = 1, nullable = False)
    contents = Column('contents', Text, nullable = False)
    
    def __init__(self, type, contents):
        active = 1
        self.contents = contents
        self.type = type
    
    def __repr__(self):
        return "<PolicyObject(%i, %i, %i, %s)>" % (self.id, self.active, self.type, self.contents)
    
    def make_json(self):
        return {'id' : self.id, 'active' : self.active, 'type' : self.type, 'contents' : self.contents }


class PolicyChain(Base):
    """ The declarative class for the database table PolicyChain.

    The class contains the attributes and structure of the PolicyChain.
    """
    __tablename__ = 'PolicyChain'
    
    id = Column('id', INTEGER(unsigned = True), primary_key = True, autoincrement = True)
    chain_id = Column('chain_id', INTEGER(unsigned = True), ForeignKey('PolicyChainMeta.id'))
    policyobject_id = Column('policyobject_id', INTEGER(unsigned = True), ForeignKey("PolicyObject.id"), nullable=False)
    parent = Column('parent', INTEGER(unsigned = True), ForeignKey(id), default = 1, nullable = False)
    child = Column('child', INTEGER(unsigned = True), default = int(0), nullable = False)
    
    policyobject = relationship("PolicyObject", uselist=False)
    
    def __init__(self, chain_id, object = 0, parent = 0, child = 0):
        self.chain_id = chain_id
        self.parent = parent
        self.child = child
        self.policyobject_id = object

        
    def __repr__(self):
        try:
            return "<PolicyChain(%i, %i, %i, %i, %i)>" % (self.id, self.chain_id, self.policyobject_id, self.parent, self.child)
        except TypeError:
            print 'Type error occured'
            print self
        
    def __str__(self):
        string = ''
        string += 'ID: %s\n' % self.id
        string += 'Chain: %s\n' % self.chain_id
        string += 'Object: %s\n' % self.policyobject_id
        string += 'Parent: %s\n' % self.parent
        string += 'Child: %s\n' % self.child
        
        return string
        
    def make_json(self):
        return {'id' : self.id, 'chain_id' : self.chain_id, 
        'policyobject_id' : self.policyobject_id,
        'parent' : self.parent,
        'child' :self.child,
        'object' : self.policyobject.make_json() }
        
class SensorLocation(Base):
    """ The declarative class for the database table SensorLocation.

    The class contains the attributes and structure of the SensorLocation.
    """
    __tablename__ = 'SensorLocation'
    id = Column('id', INTEGER(unsigned = True), primary_key = True)
    name = Column('name', String(128), nullable=False)
    
    sensors = relationship('Sensor', uselist=True)
    
    def __init__(self, name):
        self.name = name
    
    def __repr__(self):
        return "<SensorLocation(%i, %s)>" % (self.id, self.name)
    

class Sensor(Base):
    """ The declarative class for the database table Sensor.

    The class contains the attributes and structure of the Sensor
    """
    __tablename__ = 'Sensor'
    id = Column('id', Integer, primary_key = True, autoincrement = True)
    active = Column('active', Integer, nullable = False, default = 1);
    name = Column('name', String(50), nullable = False)
    ip = Column('ip', String(20), nullable = False)
    location = Column('location', INTEGER(unsigned = True),ForeignKey(SensorLocation.id), nullable = False)
    description = Column('description', String(140), nullable = False)
    policychain = Column('policychain', Integer, nullable = False)


  
    def __init__(self, name, ip, location, description, policychain = 0):
        self.name = name
        self.ip = ip
        self.location = location
        self.description = description
        self.policychain = policychain
        self.active = 1

    def __repr__(self):

        return "<Sensor('%i','%s', '%s', '%s', '%s')>" % (self.id, self.name, self.ip, self.location, self.description)
    
    def make_json(self):
        return {'id' : self.id,
        'name' : self.name,
        'ip' : self.ip,
        'description' : self.description,
        'location' : self.location,
        'policychain' : self.policychain}

        
       
       
class EventLog(Base):
    """ The declarative class for the database table EventLogs.

    The class contains the attributes and structure of the EventLogs
    """
    
    __tablename__ = 'EventLog'
    
    id = Column('id', Integer, primary_key=True, autoincrement=True)
    severity = Column('severity', String(50), nullable = False)
    timestamp = Column('timestamp', DateTime, nullable = False)
    module = Column('module', String(50), nullable = False)
    text = Column('text', Text, nullable = False)
    
    severityDict={0:'debug',1:'info', 2:'warning', 3:'error', 4:'fatal'}
    
    def __init__(self, severity, module, text):
        try: 
            if type(severity) is not int:
                raise TypeError('Severity is not a int')
            
            if severity < 0 or severity > len(self.severityDict): # Checks if the provided interval is correct
                raise ValueError('The severity has to be between 0 and', str(len(self.severityDict)))
            self.severity = severity
            self.module = module
            self.text = text
            self.timestamp = datetime.now()
        except TypeError as e:
            print e
        except ValueError as e:
            print e
    

    
    def __repr__(self):
        severity = self.severityDict[self.severity] # Translates the severity integer to text
        return "<EventLog(%i, '%s', '%s', '%s')>" % (self.id, severity, self.module, self.text)
    
    
class ScheduleStore(SQLAlchemyJobStore):
    """ Custom class used to provide job store with SQLAlchemy.
    
    This class is subclassed to provide correct functionality with Snortmanagers setup of SQLAlchemy.
    """

    def __init__(self):
        SQLAlchemyJobStore.__init__(self, engine=engine, metadata=metadata, tablename='Schedule')
	

# Initialize database
def init_database():
    """ Inititaes database and creates the tables.

    Creates all the databases, check if the integrity is correct on the root object.
    """
    try: 
        Base.metadata.create_all(engine)
        
        root_object = Session.query(PolicyChainMeta).filter(PolicyChainMeta.id == 1).one()
        
        if root_object.name != 'Root':
            raise RootObjectException('The root object is has changed name, please rename to root')
    
    except NoResultFound:
        root_object = PolicyChainMeta('Root', 'Root policy for entire policy chain')
    except OperationalError:
        print 'Error while connection to database'
    except RootObjectException as e:
        print 'There was an error while initilizing database: %s' % e
        print 'Halting execution!'
        exit(1)
     
def log_to_eventlog(severity, module, text):
    """ Log events to database. """
    
    Session.add(EventLog(severity, module, text))
    Session.flush()

    id = Column('id', Integer, primary_key = True, autoincrement = True)
    urlid = Column('urlid', Integer, ForeignKey('UpdateSource.id'), nullable = False)
    timestamp = Column('timestamp', DateTime, nullable = False)

    def __init__(self, urlid, timestamp):
        self.urlid = urlid
        self.timestamp = timestamp

# -*- coding: utf-8 -*-

""" The functionality to create and manipulate Policies in the system. """

try:
    import cherrypy
    from webapp.controller import BaseController, url, redirect, escape_string
    from webapp.config.dbconfig import Session, PolicyChainMeta, PolicyObject, PolicyChain
    from jobs import SystemLockedException
    from sqlalchemy.orm.exc import NoResultFound
    from sqlalchemy.sql.expression import and_
    import simplejson


except ImportError as e: #If there's an error
    print 'There was a importerror in', __file__
    print e
################################################

""" Constants, defines the types of policy objects. """

PREPEND = 0 
CONTENTS = 1
APPEND = 2 

class PolicyController(BaseController):
    """ The controller for the /policy/ part of the system. """

##################################################    
    @cherrypy.expose
    @cherrypy.tools.jinja(template='policy/index.html')
    def index(self):
        """ Returns a list of the active policies in the system.
        
        Provides a list of active policies and the ability to create more.
        """
        policy_chain = Session.query(PolicyChainMeta).filter(PolicyChainMeta.active == 1).all()
        
        for item in policy_chain:
            if item.name is None:
                item.name = 'N/A'
        
        return self.render({ 'page_title': 'Policy chains', 'policy_chain': policy_chain})

#################################################
    @cherrypy.expose
    def add_policy(self, name='', description=''):
        """ Creates a new policy based on user input.
        
        Known bug: Doesn't check exsitence of policy.
        """
        try:
            self.check_status()
            if len(name) > 0 and len(description) > 0:
                new_policy = PolicyChainMeta(escape_string(name.capitalize()), escape_string(description))
                Session.add(new_policy)
                Session.flush()
        except SystemLockedException:
            pass
        finally:
            raise cherrypy.HTTPRedirect("/policy/") # Return to index
            
    
    @cherrypy.expose
    @cherrypy.tools.jinja(template='policy/edit_policy.html')
    def edit_policy(self, id = 0):
        """ Returns a interface to edit entire policies.
        
        Returns a list of the contents of the policy, correctly ordered. """
        if id == 0:
            raise cherrypy.HTTPRedirect("/policy/") # Return to index
            
        # Get information about policy
        
        chain_contents = [] # List of policy chain objects
        
        policy_info = Session.query(PolicyChainMeta).filter(PolicyChainMeta.id == id).one()
        
        policyContents = Session.query(PolicyChain).join(PolicyObject).filter(
        and_(PolicyChain.chain_id == id, PolicyChain.parent == 0)).first()
        
        if policyContents is None:
            next = 0
            policyContents = Session.query(PolicyChain).filter(
            and_(PolicyChain.chain_id == id, PolicyChain.parent == 0)).first()
            if policyContents is not None:
                chain_contents.append({'id': policyContents.id, 'object': None})
        
        else:
            chain_contents.append({'id': policyContents.id, 'object': policyContents.policyobject})   
            next = int(policyContents.child)
        
        while next is not 0:
            cp = Session.query(PolicyChain).join(PolicyObject).filter(PolicyChain.id == next).first()
           
            if cp is not None:
                chain_contents.append({'id': cp.id, 'object': cp.policyobject})
                next = int(cp.child)
            else:
                cp = Session.query(PolicyChain).filter(PolicyChain.id == next).first()
                chain_contents.append({'id': cp.id, 'object': None})
                next = 0
    
        all_objects = Session.query(PolicyObject).all()
        
        return self.render({'page_title' : 'Edit policy',
        'all_objects' : all_objects,
         'policy' : {'contents' : chain_contents, 'info' : policy_info}})
    
    @cherrypy.expose
    def remove_object(self, **kwargs):
        """ Remove the object from the list """
        
        if 'Referer' in cherrypy.request.headers:
            return_url = cherrypy.request.headers['Referer']
        else:
            return_url = '/policy/'
        try:
            if kwargs['object-id'] is None or not kwargs['object-id'].isdigit():
                raise TypeError('Policy ID is either None or ID is not int')
            if kwargs['policy-id'] is None:
                raise TypeError('Policy content None')

            object_id = int(kwargs['object-id'])
            policy_id = int(kwargs['policy-id'])
            
            delete_object = Session.query(PolicyChain).filter(and_(
            PolicyChain.chain_id == policy_id, PolicyChain.id == object_id)).one()
            parent = delete_object.parent
            child = delete_object.child
            Session.delete(delete_object)
            
            if parent != 0:
                parent_object = Session.query(PolicyChain).filter(and_(
                PolicyChain.id == parent, PolicyChain.chain_id == policy_id)).one()
                parent_object.child = child
                Session.merge(parent_object)
            
            if child != 0:
                child_object = Session.query(PolicyChain).filter(and_(
                PolicyChain.id == child, PolicyChain.chain_id == policy_id)).one()
                
                child_object.parent = parent
                Session.merge(child_object)
            
            Session.flush()
            
            raise cherrypy.HTTPRedirect(return_url)
        except NoResultFound:
            raise cherrypy.HTTPRedirect(return_url)
        except KeyError as e:
            raise
        
    @cherrypy.expose
    def edit_order(self, **kwargs):
       """ Edit the order of the policy. Not implemented. """
       pass
    
    @cherrypy.expose
    def choose_object(self, **kwargs):
        """ Choose a excisting policy object. """
        try:
            if 'object-id' not in kwargs and 'policy-id' not in kwargs:
                raise KeyError
            
            object_id = kwargs['object-id']
            policy_id = kwargs['policy-id']
            
            policy_object = Session.query(PolicyChain).filter(
            PolicyChain.id == policy_id).one()
            
            policy_object.policyobject_id = object_id
            
            Session.merge(policy_object)
            Session.flush()
        
        except KeyError:
            print 'KeyError'
     
    @cherrypy.expose
    def get_policy_item(self, id=0):
        """ Return a policy item as a JSON string. """
        cherrypy.response.headers['Content-Type'] = 'application/json'
        try:
                policy_item = Session.query(PolicyChain).join(PolicyObject).filter(
                PolicyChain.id == id).one()
                policy_object = policy_item.policyobject
        except NoResultFound:
            return simplejson.dumps({'id' : 0, 'active' : 0, 'type' : 0, 'contents' : '' })

        return simplejson.dumps(policy_object.make_json())                
        
    @cherrypy.expose
    def get_object(self, id=0):
        """ Return policy object as a JSON string.
        
        Produces slightly different output than get_policy_item().
        """
        if id == 0:
            policy_object = Session.query(PolicyObject).first()
        else:
            policy_object = Session.query(PolicyObject).filter(
            PolicyObject.id == id).one()
        
        return simplejson.dumps(policy_object.make_json())                
        
    @cherrypy.expose
    def save_object(self, **kwargs):
        """ Add the contents of a policy object to the database. """
        
        print '\n\n Save object \n\n'
        try:
            content = escape_string(kwargs['object-content'])
            object_id = int(kwargs['object-id'])
            type = kwargs['object-type']
            item_id = kwargs['policy-id']
            if object_id == 0:
                policy_item = Session.query(PolicyChain).filter(
                PolicyChain.id == item_id).one()
                
                policy_object = PolicyObject(type, content)
                Session.add(policy_object)
                Session.flush()
                
                policy_item.policyobject_id = policy_object.id
            else:
                policy_object= Session.query(PolicyObject).filter(PolicyObject.id == object_id).one()
            
                policy_object.contents = content
                policy_object.type = type
            
            Session.merge(policy_object)
            Session.flush()
            
        except KeyError as e:
            print e
        except NoResultFound as e:
            #policy_object = PolicyObject(type, content)
            #Session.add(policy_object)
            #Session.flush()
            print 'no result found'
            pass
             
    @cherrypy.expose
    def delete_policy(self, id = 0):
        """ Sets a policy to deactive in the database. """
        try:
            self.check_status()
        except SystemLockedException:
            raise cherrypy.HTTPRedirect('/policy/')

        if id == 0:
            raise NoResultFound
        
        try:
            policy = Session.query(PolicyChainMeta).filter(PolicyChainMeta.id == id).one()
            policy.active = 0
            Session.merge(policy)
            Session.flush()
        except NoResultFound:
            pass
        finally:
            raise cherrypy.HTTPRedirect('/policy/')
            
    @cherrypy.expose
    def new_object(self, id = 0):
        """ Adds a new object to the end of the policy """
        if 'Referer' in cherrypy.request.headers:
            return_url = cherrypy.request.headers['Referer']
        else:
            return_url = '/policy/'
        
        try:
            last_object = Session.query(PolicyChain).filter(and_(
            PolicyChain.chain_id == id, PolicyChain.child == 0)).one();
            parent = last_object.id
        
            new_object = PolicyChain(id, 0, parent, 0)   
            Session.add(new_object)
            Session.flush()
        
            last_object.child = new_object.id
            Session.merge(last_object)
            Session.flush()
        except NoResultFound:
            new_object = PolicyChain(id, 0, 0, 0)   
            Session.add(new_object)
            Session.flush()
        
        raise cherrypy.HTTPRedirect(return_url)

    @cherrypy.expose
    def add_object(self, **kwargs):
        """ Creates a new policy object. """
        try:

            if kwargs['object_id'] is None or not kwargs['object_id'].isdigit():
                raise TypeError('Policy ID is either None or ID is not int')
            if kwargs ['object_content'] is None:
                raise TypeError('Policy content None')
        except KeyError as e:
            return 'Key %s does not exist' % e
        except TypeError as e:
            return '<p>An error occured</p><p><b>Errorinfo:</b><br/>%s' % e
        
        policy_id = kwargs['object_id'] 
        try:
        
            policy_object = Session.query(PolicyObject).filter(PolicyObject.id == policy_id).one()
            policy_object.contents = escape_string(kwargs['object_content'])
            Session.merge(policy_object)
            Session.flush()
        except NoResultFound:
            policy_object = PolicyObject(contents = escape_string(kwargs['object_content']))
            Session.add(policy_object)
            Session.flush()
        
        finally:
            raise cherrypy.HTTPRedirect("/policy/")
###################################################


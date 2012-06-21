# -*- coding: utf-8 -*-

try: 
    from webapp.config.dbconfig import Session, log_to_eventlog, Sensor, PolicyChain, PolicyChainMeta, PolicyObject, UpdateFile, Rule
    from sqlalchemy.sql.expression import and_
    from sqlalchemy.orm.exc import NoResultFound
    from jobs import ServiceLock, SystemLockedException
    from tempfile import mkdtemp
    import os
    import re # regex library

except ImportError as e:
    print 'Error while importing modules in %s' % (__file__)
    print e
    exit(1)

PREPEND = 0
CONTENTS = 1
APPEND = 2 
    
class PolicyChainProducer():

    temp_sensor_folder = '' # Path of the temporary folder used by the system.
    all_the_rules = None # In case we need to cache all the rules
    def __init__(self):
        """ Create temporary folder and get all the rule files """
        self.temp_sensor_folder = mkdtemp()
        self.rule_files = Session.query(UpdateFile)#.join(PolicyObject).filter(and_(PolicyChain.chain_id == chainId, PolicyChain.parent == 0))
        
    def producePolicyChain(self):
        """ Produces configuration file based on contents in policy chain

The job is done in the following way
 #. Compile a list of all the sensor grouped by the policy chain they use
 #. Create a list of policy contents."""

        chainList = {}                       # The list of sensors grouped by policy chain
        
        try:
            """ Compiles the list of sensors and policy chains. """
        
            for sensor in Session.query(Sensor).all():
                if str(sensor.policychain) not in chainList: # If it isn't already in the list
                    chainList[str(sensor.policychain)] = []
                
                chainList[str(sensor.policychain)].append(sensor.ip)
        except KeyError as e:
            print 'Error with key\n', e
        
        
        
        for ipList in chainList.items():
            chainId = ipList[0]
            chain_contents = []	
            
            PolicyFile = {PREPEND : [],
            CONTENTS : [],
            APPEND : []}
            
            policy_contents = Session.query(PolicyChain).join(PolicyObject).filter(and_(PolicyChain.chain_id == chainId, PolicyChain.parent == 0)).first()
            if policy_contents is not None:
                chain_contents.append({'id': policy_contents.id,'object': policy_contents.policyobject})
                next = int(policy_contents.child)
            else:
                next = 0
                
            while next is not 0:
                cp = Session.query(PolicyChain).join(PolicyObject).filter(PolicyChain.id == next).first()

                if cp is not None: # If the chain element doesn't have a Object connected to it
                    chain_contents.append({'id': cp.id, 'object': cp.policyobject})
                else:
                    cp = Session.query(PolicyChain).filter(PolicyChain.id == next).first()
            
                next = int(cp.child)
            	
            for element in chain_contents:
                policy_type = element['object'].type
                
                strings = element['object'].contents.splitlines()
                
                for string in strings:
                    if not string.startswith('#'): # Check if a line is really a comment
                        PolicyFile[policy_type].append(string) # Add to the proper list

            
            #Build policychain

            configString = ''
            
            inclusion = {'file': [], 'sid':[], 'regex': []}
            exclusion = {'file': [], 'sid':[]}
            rewrite = {}
            
            action_package = {'enable' : inclusion, 'disable' : exclusion, 'rewrite' : rewrite}
            
            pfinder = re.compile(r'^(?P<action>(disable|enable|set|rewrite))\s+(?P<target>(file|sid|regex)?)\s+(?P<content>(.+)?)$')
            for policy_string in PolicyFile[CONTENTS]:
                p_string_contents = pfinder.search(policy_string) # Builds object from content
                if p_string_contents is not None:

                    policy_action = p_string_contents.group('action')
                    policy_target = p_string_contents.group('target')
                    policy_content = p_string_contents.group('content')                 
                        
                    if policy_action == 'rewrite':
                        find_sid_pattern = re.compile(r'^\d+')
                        rewrite_sid = find_sid_pattern.search(policy_content)
                        action_package[policy_action][rewrite_sid.group(0)] = policy_content
                    else:
                            
                        if policy_action == 'enable' and policy_target != 'regex':
                            try:
                                action_package['disable'][policy_target].remove(policy_content)
                            except ValueError:
                                pass
                        elif policy_action == 'disable':
                            try:
                               action_package['enable'][policy_target].remove(policy_content)
                            except ValueError:
                                pass
                         
                        action_package[policy_action][policy_target].append(policy_content)
            
            # Add content to file
            
            for line in PolicyFile[PREPEND]: # Write all prepend content to file
                configString += line + '\n'
            
            for file in self.rule_files:
                if len(exclusion['file']) is not 0:
                    if file.name not in exclusion['file']:
                        rules = Session.query(Rule).filter(Rule.file == file.id)
                        for rule in rules:
                            if str(rule.sid) not in exclusion['sid'] and rule.active is not 0:
                                if rule.sid in rewrite:
                                    configstring += self.prepare_rule(rule.rule,rewrite[rule.sid])
                                else:
                                    configString += rule.rule

                if len(inclusion['file']) is not 0:

                    if file.name in inclusion['file']:
                        rules = Session.query(Rule).filter(Rule.file == file.id)
                        for rule in rules:
                            if str(rule.sid) not in exclusion['sid'] and rule.active is not 0:
                                if str(rule.sid) == rewrite:
                                    configstring += self.prepare_rule(rule.rule, rewrite[rule.sid])
                                else:
                                    configString += rule.rule
                    
             
            if len(inclusion['sid']) is not 0: 
                for inc_sid in inclusion['sid']:
                    try: 
                        rule = Session.query(Rule).filter(Rule.sid == inc_sid).order_by(Rule.rev.desc()).first()	   
                    
                        if rule is None:
                            raise NoResultFound
                        if str(rule.sid) in rewrite:
                            configString += self.prepare_rule(rule.rule, rewrite[str(rule.sid)])
                        else:
                            configString += rule.rule
                    except NoResultFound:
                        pass
            
                        # Enable from regex

            if len(inclusion['regex']) > 0: # Activates rules based on regex pattern
                """ Will only fetch all the rules __IF__ there's regex item """
                self.all_the_rules = Session.query(Rule).filter(Rule.active == 1).all() # Get ALL the rules
                for sid_expression in inclusion['regex']: # Go through each pattern to search
                    reg_pattern = re.compile(r'%s' % sid_expression)
                    for rule in self.all_the_rules: # Go through rules
                        if reg_pattern.search(rule.rule):

                            if (str(rule.sid) not in inclusion['sid'] and 
                            self.rule_files[rule.file].name not in inclusion['file']):
                                configString += rule.rule
                    
            for line in PolicyFile[APPEND]:			# Write all the append content to file
                configString += line + '\n'

            for sensor in ipList[1]:
                #roll out policychain
                try:
                    f = open(os.path.join(self.temp_sensor_folder, sensor + '.txt'),'w')
                    f.write(configString)
                    f.close()
                except IOError:
                    print 'IOError'
                

    
    def prepare_rule(self, rule = '', rewrite = None):
        """ Prepeares the rule for usage """ 
        if rewrite is not None:
            find_values = re.compile(r'(?P<sid>\d+)\s+(?P<search>"(\$|\w|\-|\-)+")\s+(?P<replace>"(\$|\w|\-|\-)+")')
            values = find_values.search(rewrite)
            search = values.group('search').strip('"')
            replace = values.group('replace').strip('"')
            return rule.replace(search, replace)
        else:
            return rule
            
def produce_configuration_files():
    if not ServiceLock.is_locked():
        ServiceLock.lock_system('Update System')
        producer = PolicyChainProducer()
        producer.producePolicyChain()
        ServiceLock.unlock_system()
    else:
        print 'System is locked'

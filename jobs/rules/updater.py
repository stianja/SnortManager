# -*- coding: utf-8 -*-
"""
Downloads rules from list of providers


"""

try: 

	import re, os, sys, tempfile, urllib2, mimetypes
	import tarfile, zipfile # Libraries for archives
	from Parser.RuleParser import Rule
	from shutil import rmtree
	from datetime import datetime
	from sqlalchemy.exc import DatabaseError, OperationalError
	from sqlalchemy.orm.exc import NoResultFound
	from webapp.config.dbconfig import Session, UpdateSource, UpdateFilter, Rule as Rules, UpdateFile, UpdateLog
	from sqlalchemy.sql.expression import and_, desc
	from jobs import ServiceLock
except ImportError:
	print('Error while importing modules!') # TODO: Oversettes til andre språk
	raise
	sys.exit()


class GetRules():


	def __init__(self):
		""" Constructor that does nothing """
		self.tempDownloadFolder = tempfile.mkdtemp() # Creates temporary folder securly
		
	def get_ignore_list(self, urlID):
		""" Gets the list of files to ignore """
		filesToIgnore = []						# List of files and folders to ignore

		try:
			IgnoreList = Session.query(UpdateFilter).filter(UpdateFilter.updateurl == urlID)
    			for item in IgnoreList:
	    			filesToIgnore.append(item.path)
		except Exception as e:
			print('Exception; problem with generation of ignore list')		
			print e
			exit(1)
			
		return filesToIgnore
		
	def download_rules(self):
		""" Downloads all the rules from a provided array of lists and reads from file """
		# PROPER VALUES
		tempDownloadFolder = self.tempDownloadFolder
		try:
			listOfUrl = Session.query(UpdateSource).filter(UpdateSource.active == 1) #sql.execute("SELECT id, url FROM UpdateUrl WHERE active = 1") 

			for listUrl in listOfUrl:
				try:
					# Get ignores
					self.register_update_in_database(listUrl.id) # Register 
					IgnoreList = self.get_ignore_list(listUrl.id)
					FileUrl = listUrl.url # TODO: DELETE
					urlHandler = urllib2.urlopen(FileUrl)
					localFileName = re.search(r'(?<=/{1})[\w\-\.]+\.(rules|tar\.gz|zip|conf)', FileUrl)
					localFilePath = os.path.join(tempDownloadFolder, os.path.basename(localFileName.group(0)))
					localFile = open(localFilePath, 'w') 
					localFile.write(urlHandler.read())
					localFile.close()
					isArchive = self.check_if_file_is_archive(localFilePath)
					if(isArchive == None):
						self.read_rule_file(localFilePath, listUrl.id, IgnoreList) #Traverse dir
					else:
						for file in isArchive:
							full_path = os.path.join(tempDownloadFolder, file)
#							print 'Reading file name %s' % full_path
							self.read_rule_file(full_path, listUrl.id, IgnoreList)
							#self.get_rule_contents(os.path.join(tempDownloadFolder, file), listUrl.id, IgnoreList)
				except urllib2.HTTPError, e:
					errorCodes = {404: 'Not Found',
						403: 'Forbidden'}
					print r"""
===================
Error while downloading updates
Url: %s
Error code: %i
Error message: %s
===================
""" % (FileUrl, e.code, errorCodes[e.code])

				except urllib2.URLError, e:
					print 'Error with URL', e.reason  #TODO: OVERSETT

		except DatabaseError:
			print('Error connecting to database')
			raise
			exit()
		finally:
			self.rm_temp()

	def register_file_in_database(self, file, urlid):
		""" Register a Snort rule in the database
		
		This method will register a Snort rule file with its full path and file name.
		
		:param file: the full path with filename.
		:param urlid: the update source. Used to connect registered file to correct source in the database.
		""" 
		try:
			base_path = str(self.tempDownloadFolder)
			search_pattern = re.compile(r'(?P<path>[A-z]+)/(?P<name>(\w|\.|-)+)$') # Search for file ending
			file_attributes = search_pattern.search(file) #
			file_name = file_attributes.group('name')
			file_path = file_attributes.group('path')
				
			try:

				file_from_db = Session.query(UpdateFile).filter(and_(UpdateFile.name == file_name, UpdateFile.updatesource == urlid)).one()
			
			
			
				if file_from_db is None:
					raise NoResulFound
				else:
					return file_from_db.id
			except NoResultFound:
				new_file = UpdateFile(file_name, urlid, file_path)
				Session.add(new_file)
				Session.flush()
				return new_file.id
		except ImportError:
			#print('') #TODO: TRANSLATe
			#raise
			#exit(1)
			print e
			exit()
		return 0

	def register_update_in_database(self, urlid=0):
        	""" Register download in database """ 
		if(urlid != 0):
			try:
				UpdateItem = UpdateLog(urlid,datetime.now())
				Session.add(UpdateItem)
				return UpdateItem.id
			except:
				print('Error while registering update with database')
				raise

			return 0
				
	def check_if_file_is_archive(self, path):
		""" Checks if file is archive. Returns false if it isn't. """
		fileMembers = None
		mimetypes.init()
		if os.path.isfile(path):
			pathMime, pathEncoding = mimetypes.guess_type(path)
			if(pathMime is not None):
				if(pathMime.endswith('x-tar')):
					fileMembers = self.extract_tar(path)
				elif(pathMime.endswith('zip')):
					fileMembers = self.extract_zip(path)
		return fileMembers
	
	def extract_tar(self, path):
		""" Extract contents of tar file to temporary folder """ 
		fileMembers = None
		try:
			if(tarfile.is_tarfile(path)):
				tarArchive = tarfile.open(path)
				fileMembers = tarArchive.getnames()
				tarArchive.extractall(self.tempDownloadFolder)
				tarArchive.close()
		except tarfile.TarError:
			print('There was an error reading the TAR Archive') #TODO: OVERSETT
			raise

		return fileMembers

	def extract_zip(self, path):
		""" Extract contents of zip file """
		fileMembers = None
		try:
			if(zipfile.is_zipfile(path)):
				zipArchive = zipfile.open(path)
				fileMembers = zipFile.getnames()
				zipArchive.extractall(self.tempDownloadFolder)
				zipArchive.close()
		except zipfile.ZipFile:
			print('Error while reading zip archive') # TODO: OVERSETT

		return fileMembers
		
	def rm_temp(self):
		""" Deletes temporary folder from computer """
		rmtree(self.tempDownloadFolder)

	def isRule(self, rule):
		""" Check if the string is a rule or if it's plain text. """ 
		try:
			reg = re.compile(r'^#?\s*(alert|log|pass|activate|dynamic|drop|sdrop|reject)\s*(tcp|udp|icmp|ip)\s*')
			if(reg.search(rule)):
				return True
			else:
				return False
		except Exception as e:
			print "Exception in isRule" #TODO: Translate
			print e
			
	def read_rule_file(self, path, source, ignore_list = []):
		""" Reads the contens of a rule file """
		ruleFileID = 0
		listOfRules = []
		try:
			if(path.endswith('.rules')):
				ruleFileID = self.register_file_in_database(path, source) # Registers this file in the database
				ruleFile = open(path)
				for line in ruleFile.readlines():	
					if (self.isRule(line)):
						listOfRules.append(Rule(line))

				ruleFile.close()
		except Exception as e:
			print('EXCEPTION: Error during rule creation (read_rule_file)\n--Errorinfo--')
			print'Path:', path
			print e
	
		if(len(listOfRules) is not 0):			# Continue to add rules to db
			self.add_rules_to_database(ruleFileID,listOfRules)

	def _find_local_rule(self, rule_list = [], search = 0):
		""" Find a rule in a local list of rules from the database. """
		found_rules = []

		if len(rule_list) != 0 or int(search) != 0:
			for rule in rule_list:
				if int(rule.sid) == int(search):
					found_rules.append(rule)
			
		if len(found_rules) > 1:
			return sorted(found_rules, key=lambda rule: rule.rev)
		
		return found_rules
	
	def add_rules_to_database(self, file_id, ruleList):
		""" Add rules to database based on file """
		stored_rules = Session.query(Rules).filter(Rules.file == file_id).all() # Returns entire set of rules
		stored_list = {}	# Cache of already accessed rules
		rules_to_add = []   # List of rule to add to database
		for new_rule in ruleList:
			try:

				try:
					if int(new_rule.sid) not in stored_list or stored_list[new_rule.sid] is None:
						stored_list[int(new_rule.sid)] = self._find_local_rule(stored_rules, int(new_rule.sid))
					
					stored_local_rules = stored_list[int(new_rule.sid)]
					
					if stored_local_rules is None or len(stored_local_rules) == 0:
#					    print 'print %s is not in DB. Type %s' % (int(new_rule.sid), type(new_rule.sid))
#					    for rules in stored_rules:
#					        print 'Sid: %s Rev: %s\nRule: %s' % (rules.sid, rules.rev, rules.rule)
					    
					    raise NoResultFound
					    
					old_rule = stored_local_rules[0]
					#print '--#--\n SID: %s' % (new_rule.sid)
					#print '---\n ID: %s \n Rule: %s --#--' % (old_rule.sid, old_rule.rule)
					
					#print '-#- \n %s \n -#- \n %s-#-'  % (old_rule, new_rule)
					
					
					if int(old_rule.rev) < int(new_rule.rev) or str(old_rule.rule) != str(new_rule.raw):
						old_rule = self.deactivate_rule(old_rule)
						print 'Different revision or content %s' % old_rule.sid
						raise NoResultFound
					
					if new_rule.active != old_rule.active:
						print 'Rule is deactiviated: %s' % old_rule.sid
						old_rule = deactiviate_rule(old_rule)
						
					stored_local_rules[0] = old_rule 
					stored_list[int(new_rule.sid)] = stored_local_rules
				except NoResultFound:			# No result found, add rule
					new_rule_add = Rules(new_rule, file_id)
					rules_to_add.append(new_rule_add)
				except IndexError as e:
					print 'List index: %s' % (e)
					print stored_local_rules
					exit(1)
				except TypeError as e:
					print 'Type error: %s' % (e)
#					print type(new_rule.sid)
#					print stored_local_rules
					exit(1)

			except OperationalError as e:
				print 'EXCEPTION in add_rules_to_database\nError information: %s' % (e) #TODO: Needs to fuck off
		
		Session.add_all(rules_to_add)
		Session.flush()	
	
	def deactivate_rule(self, rule):
		""" Deactivates and merges rules. Also returns the old rule to """
		rule.active = 0
		Session.merge(rule)
		
		return rule
		
	def get_rule_contents(self, path, updateurl, ignoreList=[]):
		""" Opens a text file containing rules, reads and registers data to database """
		try:
			if(os.path.basename(path.rstrip('/')) not in ignoreList):
#				if os.path.isfile(path):
					self.read_rule_file(path, updateurl)
#				else:
#					for file in os.listdir(path):
#						fullPath = os.path.join(path, file)
#						if(os.path.isdir(fullPath)):
#							self.get_rule_contents(fullPath, updateurl, ignoreList)
#						else:
#							self.read_rule_file(fullPath, updateurl)	
		except NoResultFound as e:
			print 'EXCEPTION during get_rule_contents\nError Information:' #TODO: TRANSLATE
			print 'Path:', path
			print e

def update_snort_rules():
    if not ServiceLock.is_locked():
        ServiceLock.lock_system('Update System')
        ruleFile = GetRules()
        ruleFile.download_rules()
        ServiceLock.unlock_system()
    else:
        print 'System is locked'

def main():
	print 'Starting execution and download', datetime.now()
	ruleFile = GetRules()
	ruleFile.download_rules()
	print 'Starting execution and download', datetime.now()

if __name__ == '__main__':
	main()

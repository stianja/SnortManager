# -*- coding: utf-8 -*-

from webapp.config import VARDIR
import os

class SystemLockedException(Exception):
    """ Exception to throw if system is locked for usage """
    process_id = 0
    process_name = ''
    message = ''

    def __init__(self, message = ''):
        self.message = message
    
    def __init__(self, message = '', proc_id = 0, process_name = ''):
        self.process_id = proc_id
        self.process_name = process_name
        self.message = message
        
    def __str__(self):
        return repr('%s' , self.proc_id) % (self.message)


class SystemLock:
    """ Locks the system so users can't start new jobs or write to database """
    system_locked = False
    process_name = ''
    process_id = 0
    pid_file = os.path.join(VARDIR, 'DB_LOCK.pid')
    
    def __init__(self):
        pass
	    
    def is_locked(self):
        """ Return the status of the lock. True if system is locked."""
        try:
            f = open(self.pid_file, 'r')
            f.close()
            return True
        except IOError as e:
            return False

    def lock_system(self, name):
        if self.is_locked():
            raise SystemLockedException(self.process_id, self.process_name)
        
        try:
            self.process_id = os.getppid()
            lock_file = file(self.pid_file, 'w')
            lock_file.write(str(self.process_id))
            lock_file.close()
        except IOError:
            print 'Error while creting PID'
	    
    def unlock_system(self):
        if self.is_locked():
            self.process_name = ''
            self.process_id = 0
            os.remove(self.pid_file)
            
ServiceLock = SystemLock()
	    
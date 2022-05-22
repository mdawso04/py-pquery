from pp.constants import *
import pp.config as config
from pp.log import logger
from pp.util import *
#from pp.ml_f import *

#python standard libraries
import functools, inspect

#non-standard libraries
import pandas as pd

class App(object):
    def __init__(self, todos=None):
        # TODO - CHANGE TO 'TODO_NAME': 'TODO' FORMAT
        if todos is None or not isinstance(todos, list): 
            #self.todos = {k: [] for k in ('read', 'data', 'viz', 'write')} 
            self.todos = []
        else:
            self.todos = todos
            if not self._hasRead():
                self.todos = []
                logger.warning('Assigned Todos missing Read so reset to None')
            else:
                logger.debug('Initiated App: {} Todos'.format(len(todos)))
    
    def services(self, group=None, as_list=False):
        if as_list:
            d = self._service_helper(return_type='group_service_names', group=group)
            return [i for l in d.values() for i in l]
        return self._service_helper(return_type='group_service_names', group=group)
    
    def _getService(self, service):
        service_dict = self._service_helper(return_type='service_callable')
        if service in service_dict.keys():
            return service_dict[service]
        else:
            return None
    
    def _service_helper(self, group=None, return_type='group_service_callable', filter_read=True):
        if return_type=='group_service_callable':
            if self._hasRead():
                if filter_read:
                    return service_helper(groups=['data', 'viz', 'write'], return_type='group_service_callable')
                else:
                    return service_helper(groups=['read', 'data', 'viz', 'write'], return_type='group_service_callable')
            else:
                if group in ('read', None):
                    return service_helper(groups='read', return_type='group_service_callable')
                else:    
                    return None
                
        elif return_type=='group_service_names':
            if self._hasRead():
                if filter_read:
                    return service_helper(groups=['data', 'viz', 'write'], return_type='group_service_names')
                else:
                    return service_helper(groups=['read', 'data', 'viz', 'write'], return_type='group_service_names')
            else:    
                if group in ('read', None):
                    return service_helper(groups='read', return_type='group_service_names')
                else:
                    return None
                
        elif return_type=='service_callable':
            if self._hasRead():
                if filter_read:
                    return service_helper(groups=['data', 'viz', 'write'], return_type='service_callable')
                else:
                    return service_helper(groups=['read', 'data', 'viz', 'write'], return_type='service_callable')
            else:
                if group in ('read', None):
                    return service_helper(groups='read', return_type='service_callable')
                else:
                    return None
        return "SERVICE NOT FOUND"
    
    def options(self, service, df=None, index=None):
        s = self._getService(service)
        if s is None:
            raise Exception('Service: {} not found'.format(service))
        if df is not None:
            o = s.options(df)
        else:
            if len(self.todos) == 0:
                o = None
            else:
                o = s.options(self.call(last_index=index))
        logger.debug('Generated options for {} field/s'.format(len(o) if o is not None else None))
        return o
    
    def add(self, service, options=None, index=None, todoName=None):
        if not self._validateAdd(service):
            raise Exception('Service: {} not found'.format(service))
        group = extractGroup(service)
        def toUniqueName(name):
            n = 1
            name = str(name)
            currentNames = [s['name'] for s in self.todos]
            while name in currentNames:
                name = name + '_' + str(n)
            return name
        if todoName is not None:
            todoName = toUniqueName(todoName)
        else:
            todoName = toUniqueName(group)
        todo = {'name': todoName, 'type': group, 'settings': {'service': service, 'options': options}}
        if index is not None:
            self.todos.insert(index, todo)
        else:
            self.todos.append(todo)
        logger.debug('Added Todo: {} ({})'.format(service, todoName))
        
    def _validateAdd(self, service):
        group = extractGroup(service)
        if group is None:
            return False
        if group == 'read':
            if self._hasRead():
                logger.debug('Already has read!')
                return False
            else:
                return True
        else:
            if not self._hasRead():
                logger.debug('No read set so cant start!')
                return False
            else:
                return True
    
    def _hasRead(self):
        # need 1 and only 1 read in todos
        td = self._todo_helper('read')
        if len(td) == 1:
            return True
        return False
    
    def _todo_helper(self, group=None):
        if group == None:
            return self.todos
        else:
            return [i for i in self.todos if i['type']==group]
    
    # TODO - CHANGE TO 'TODO_NAME': 'TODO' FORMAT
    def call(self, df=None, last_index=None, return_df=True):
        if not self._isvalid():
            #exception
            return "ERROR"
        service_list = self._service_helper(return_type='service_callable', filter_read=False)  
        result, results = None, []
        logger.debug('Calling Todos: {}'.format(len(self.todos)))
        for item in self.todos[:last_index]:
            fn = service_list[item['settings']['service']].fn
            s = inspect.signature(fn)
            if 'df' in s.parameters:
                if 'options' in item['settings'].keys() and item['settings']['options'] is not None:
                    result = fn(df=df, **item['settings']['options'])
                else:
                    result = fn(df=df)
            else:
                print(item)
                if 'options' in item['settings'].keys() and item['settings']['options'] is not None:
                    result = fn(**item['settings']['options'])
                else:
                    result = fn()
            if isinstance(result, pd.DataFrame):
                df = result
            else:
                results.append(result)
            logger.debug('Called Todo: {} ({})'.format(item['settings']['service'], item['name']))
        results.append(df)
        logger.debug('Called Todos: {}'.format(len(self.todos)))
        logger.debug('Generated results: {}'.format(len(results)))
        if return_df:
            return results[-1]
        return results

    def _isvalid(self):
        #TODO
        # MUST/WANT param check
        # param type check
        return True
    
    def tostring():
        pass

    
'''
class Base(object):
    
    def __init__(self, source):
        super(Base, self).__init__()
        
        #Build base data structure
        self._data = {
            DATATYPE_DATAFRAME:{
                'active':None,
                'stack':[]
            },
        }
        logger.debug('Data structure built')
        
        #read user supplied source
        self._read(source)
        logger.debug('Source read: {}'.format(source))
        
        #call default preview
        self._preview()
               
    def _pop(self, key):
        #Return current data item and replace with next from stack
        #TODO if empty
        s = self._data[key]['stack']
        old = s.pop()
        self._data[key]['active'] = s[-1] if len(s) > 0 else None
        return old
    
    def _append(self, key, data):
        #Add data item to stack and make active
        #TODO if empty
        self._data[key]['stack'].append(data); self._data[key]['active'] = data
        return self
    
    def _active(self, key, data):
        #Replace active data
        self._pop(key); self._append(key, data)
        return self
    
    def REPORT_SAVE_DATA_AS_CSV_EXCEL(self, tar):
        self._write(tar)
        return self
        
    @property
    def df(self):
        return self._data[DATATYPE_DATAFRAME]['active']
    
    @df.setter
    def df(self, df1):
        #Replace active df without pushing current to stack
        self._active(DATATYPE_DATAFRAME, df1)
    
    def _repr_pretty_(self, p, cycle): 
        #Selects content for IPython display
        selected = self._previewMode
        d = self._data
        return PREVIEWERS[selected].preview(data=self._data)
        
    def __repr__(self): 
        return self._df.__repr__()
    
    def __str__(self): 
        return self._df.__str__()
'''                          
                             
'''
if x < 0:
  raise Exception("Sorry, no numbers below zero")

try:
  print("Hello")
except:
  print("Something went wrong")
else:
  print("Nothing went wrong")
  '''


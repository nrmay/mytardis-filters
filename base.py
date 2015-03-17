'''
Created on 13 Mar 2015

@author: nmay
'''

import logging
from tardis.tardis_portal.models import Schema
from tardis.tardis_portal.models import ParameterName, DatafileParameter
from pprint import pformat
from dateutil import parser


class FilterBase(object):
    '''
    classdocs
    '''

    def __init__(self, name, namespace, version, schemas, suffixes):
        '''
        Constructor
        '''
        self.name = name
        self.namespace = namespace
        self.version = version
        self.schemas = schemas
        self.suffixes = suffixes
        self.logger = logging.getLogger(__name__)
        
        return

    # --------------------------
    #     main process template
    #--------------------------
    def __call__(self, sender, **kwargs):
        """post save callback entry point.

        :param sender: The model class.
        :param instance: The actual instance being saved.
        :param created: A boolean; True if a new record was created.
        :type created: bool
        """
        
        try:
            # get the file in the database
            instance = kwargs.get('instance')

            # get the real location of the file
            filepath = instance.get_absolute_filepath()
            
            # check filepath suffixes
            if not(filepath.lower().endswith(self.suffixes)):
                return None
            
            self.logger.debug("\n%s: filepath = %s" % (self.name, 
                                                       str(filepath)))

            # check its a new file
            psets = instance.getParameterSets()
            if not psets:
                metadata = self.extractMetadata(filepath)                        
                self.logger.debug("\n%s: meta-data = %s" % (self.name, 
                                                            str(metadata)))
                if metadata:
                    self.saveMetadata(instance, metadata)
            
            self.printDatafileMetadata(instance)
            
        except Exception, e:
            # if anything goes wrong, log it in tardis.log and exit
            self.logger.info(e)
            
        return
    
    
    def extractMetadata(self, target):
        """
        Extract meta-data from file.

        :param target: the file path
        :type target: string
        :return 
        :type 
        """
        
        result = None
        self.logger.debug(
            '%s: extracting meta-data for %s' % (self.name, target))
 
        # return 
        return result          


    def saveMetadata(self, instance, metadata):
        """
        Save the metadata to Dataset_Files parameter sets.
        
        :param instance: file.
        :param metadata: file header as a multi-level dictionary.
        """
        self.logger.debug('%s: starting!' % (self.name))
        
        # save each line as a parameter set
        for key, line in metadata.items():
            # get the schema for this line

    
        # finished with saveMetadata
        return

    # --------------------------------
    # get the schema for a header line
    # --------------------------------
    def getSchema(self, schema):
        """
        Return the schema object that the paramater set will use.
        """
        
        result = None
        
        # format full schema name
        fullname = str(self.namespace)
        if not fullname.endswith('/'):
            fullname += '/'
        fullname += self.version 
        if not fullname.endswith('/'):
            fullname += '/'
        fullname += schema
        self.logger.debug("%s: get schema(%s) as %s" % (    
                                                self.name, schema, fullname))
            
        try:
            # get existing schema
            result = Schema.objects.get(namespace__exact=fullname)
        except Schema.DoesNotExist:
            # create missing schema
            result = Schema(namespace=fullname, 
                            name=("%s - %s" % (self.name, schema)), 
                            type=Schema.DATAFILE)
            result.save()
          
        # finished      
        return result

    # ----------------------------------------
    # get a list of parameters for this schema 
    # ----------------------------------------
    def getParameterSets(self, schema, datafile):
        """
        Return a list of the parameter sets for a given schema and datafile.
        """
        self.logger.debug('%s: get parameter sets for schema[id=%s] and datafile[id=%s]' % (
                           self.name, str(schema.id), str(datafile.id)))
        
        result = []
        psets = datafile.getParameterSets()
        for pset in psets:
            if pset.schema == schema:
                result.append(pset)
          
        # finished    
        self.logger.debug('%s: get parameter sets  found %d items' % (
                            self.name, len(result)))  
        return result

    # ----------------------------------------
    # get a list of parameters for this schema 
    # ----------------------------------------
    def getParameterNames(self, schema, params):
        """
        Return a list of the parameters that will be saved.
        """
        self.logger.debug('%s: get parameter names for schema[%s]' % (
                            self.name, str(schema)))
        
        parameter_names = list(ParameterName.objects.filter(schema=schema))
        self.logger.debug('%s: list parameter name for schema[%s] found %d ' % (
                            self.name, str(schema), len(parameter_names)))
            
        # create objects if empty
        if not parameter_names:
            for param in params.itervalues():
                self.logger.debug('%s: create parameter name for param = %s' % (
                            self.name, str(param)))
                
                if param.has_key('data_type'):
                    if param['data_type'] == 'DATETIME':
                        param_type = ParameterName.DATETIME
                    if param['data_type'] == 'NUMERIC':
                        param_type = ParameterName.NUMERIC
                else:
                    param_type = ParameterName.STRING
                    
                name = ParameterName(schema=schema,
                                     name=param['name'], 
                                     full_name=param['full_name'],
                                     data_type=param_type)
                name.save()  
                parameter_names.append(name)

        # finished
        self.logger.debug('%s: get parameter names for schema[%s] returned %d names' % (
                            self.name, str(schema), len(parameter_names)))
        return parameter_names

    # --------------------------------
    # create new a list of parameter names 
    # --------------------------------
    def createDatafileParameters(self, tags, paramset, paramnames, metadata):
        """Create the Parameter values for the parameter set
        
        :param tags: SAMFORMAT parameter details.
        :param paramset: ParameterSet for this schema/datafile.
        :param paramnames: ParameterNames for this schema.
        :param metadata: File metadata line for this schema.
        """
        
        self.logger.debug('%s: tags = %s'       % (self.name, str(tags)))  
        self.logger.debug('%s: metadata = %s'   % (self.name, str(metadata)))    
        self.logger.debug('%s: paramnames = %s' % (self.name, str(paramnames)))    
       
        for key, values in tags.items():
            self.logger.debug('%s: tags key[%s] values[%s]' % (
                                            self.name, str(key), str(values)))
            
            # get the parametername
            for item in paramnames:
                if item.name == values.get('name'):
                    pname = item
                    self.logger.debug('%s: param.name = %s' % (
                                            self.name, str(pname)))
            
            # create the datafile parameter
            if metadata.has_key(key):
                # set value from metadata
                param = DatafileParameter(parameterset=paramset,name=pname)
                param = self.setParameterValue(param,pname,metadata.get(key))
                self.logger.debug('%s: parameter = %s' % (
                                            self.name, pformat(param)))

            elif values.has_key('default'):
                # check default provided
                param = DatafileParameter(parameterset=paramset,name=pname)
                param = self.setParameterValue(param,pname,values.get('default'))
                self.logger.debug('%s: parameter = %s (default)' % (
                                            self.name, str(param)))

            elif values.get('required'):
                # check if required
                raise

        # finished
        return   

    # ----------------------------------
    # sets the parameter value and saves
    # ----------------------------------
    def setParameterValue(self, parameter, pname, value):   
        
        if pname.isNumeric():
            parameter.numerical_value = value
        elif pname.isDateTime():
            self.logger.debug('%s: isDateTime = %s' % (self.name, value))
            dvalue = parser.parse(value)
            self.logger.debug("%s: date = %s" % (self.name, str(dvalue)))
            parameter.datetime_value = dvalue
        else:
            parameter.string_value = value

        parameter.save()
        
        return parameter

    # --------------------------------------------
    # print schema and parametersets for datafile
    # --------------------------------------------
    def printDatafileMetadata(self, target):
        '''Print the Metadata for a Datafile
            Including: Schemas, ParameterNames, ParameterSets, and Parameters.
            
        :param target: the datafile.
        '''

        tab = '   '
        tab2 = tab + tab
        tab3 = tab + tab2
        self.logger.debug('--------------------------------------------------')
        self.logger.debug('datafile id = ' + str(target.id))
        self.logger.debug('%sfilename = %s' % (tab, str(target.filename)))
        
        
        # parameter sets
        psets = target.getParameterSets()
        self.logger.debug('parameter sets: count = %s' % (str(len(psets))))
        for item in psets:
            schema = item.schema
            pnames = list(ParameterName.objects.filter(schema=schema))
            params = DatafileParameter.objects.filter(parameterset=item)
            
            self.logger.debug('%sparameter set id = %s' % (tab, str(item.id)))
            self.logger.debug('%sschema id = %s' % (tab2, str(schema.id)))
            self.logger.debug('%stype = %s'      % (tab2, str(schema.type)))
            self.logger.debug('%snamespace = %s' % (tab2, str(schema.namespace)))
            self.logger.debug('%sparameter names count = %s' % (tab2, str(len(pnames))))
            for pn in pnames:
                self.logger.debug('%sname = %s' % (tab3, str(pn))) 
                
            self.logger.debug('%sparameters count = %s' % (tab2, str(len(params))))
            for ps in params:
                self.logger.debug('%sparam id = %s'  % (tab3, str(ps.id)))
                self.logger.debug('%sname  = %s'     % (tab3, str(ps.name.name)))
                if ps.datetime_value:
                    self.logger.debug('%svalue = %s' % (tab3, str(ps.datetime_value)))
                elif ps.numerical_value:
                    self.logger.debug('%svalue = %s' % (tab3, str(ps.numerical_value)))
                else:
                    self.logger.debug('%svalue = %s' % (tab3, ps.string_value))
                     
        # finished
        self.logger.debug('--------------------------------------------------')
        return

        
'''
Created on 17/03/2015

@author: Nick
'''
from base import FilterBase
from tardis.tardis_portal.models import DatafileParameterSet

class FilterTemplate(FilterBase):
    '''
    classdocs
    '''
    
    def __init__(self, name, namespace):
        """
        This filter extracts meta-data from files.

        :param name: the short name of the schema.
        :type name: string
        :param namespace: the namespace of the schema to load the data into.
        :type namespace: string
        """
        
        # define schema version and file extensions      
        self.version = "1.0"
        self.suffixes = ('.txt', )
        
        # define schema formats
        # schema: dictionary of parameters;
        #     key: source data label --- if applicable
        #    data: dictionary of parameter fields; 
        #            name: (string)  name of the parameter.
        #       full_name: (string)  description of the parameter.
        #        required: (boolean) is this field mandatory
        #                            defaults to FALSE if none provided.
        #         default: (string)  value to use if none provided.
        #       data_type: (string)  'NUMERIC', 'DATETIME', 'STRING'
        #                            defaults to 'STRING' if none provided.
               
        self.params_header = {
            'KB': {'name': 'size', 'full_name': 'File Size (KBs)',
                   'data_type': 'NUMERIC', 'required': True, '},
        }
        
        
        # define list of schemas
        # schemas: dictionary of schemas;
        #      key: source data label -- if applicable.
        #     data: dictionary of schema parameters;
        #             name: (string)     name of the schema.
        #           params: (dictionary) schema parameters variable.
        #             list: (boolean)    are multiple schemas of this type allowed.
        
        self.schemas = {
            'HD': {'name':'header','params': self.params_header, 'list': False},
        }
        
        # initialise filterbase
        FilterBase.__init__(self, name, namespace,
                            self.version, self.schemas, self.suffixes)
   
        return
    
    
    def extractMetadata(self, target):
        """
        Extract meta-data from file.

        :param target: the file path
        :type target: string
        :return: file metadata 
        """
        
        result = None
        self.logger.debug('%s: override to extract meta-data for %s' % (
                                                    self.name, target))
        return result          


    def saveMetadata(self, instance, metadata):
        """
        Save the metadata to Dataset_Files parameter sets.
        
        :param instance: file.
        :type instance: Dataset_file
        :param metadata: file metadata
        """
        self.logger.debug('%s: override to save metadata for %s' % (
                                                    self.name, str(instance)))
        return

    
make_filter.__doc__ = Filter.__doc__


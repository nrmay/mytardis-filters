'''
Created on 17/03/2015

@author: Nick
'''

from base import FilterBase
from tardis.tardis_portal.models import DatafileParameterSet
from pprint import pformat
import pysam

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
        self.version = "6f8dfe4"
        self.suffixes = ('.sam', '.bam', '.tam')
        
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
            'VN': {'name': 'format', 'full_name': 'Format Version',
                   'required': True, 'default': 'unknown'},
            'SO': {'name': 'sorting', 'full_name': 'Sorting Order'},
        }
        
        self.params_sequence = {
            'SN': {'name': 'name', 'full_name': 'Reference Sequence Name',
                   'required': True},
            'LN': {'name': 'length', 'full_name': 'Sequence Length', 
                   'required': True, 'data_type': 'NUMERIC'},
            'AS': {'name': 'genome', 
                   'full_name': 'Genome Assembly Identifier'},
            'M5': {'name': 'md5', 'full_name': 'MD5 Checksum'},
            'SP': {'name': 'species', 'full_name': 'Species'},
            'UR': {'name': 'uri', 'full_name': 'Sequence URI'},
        }
        
        self.params_group = {
            'ID': {'name': 'id', 'full_name': 'Read Group Identifier', 
                   'required': True},
            'CN': {'name': 'center', 
                   'full_name': 'Name of the Sequencing Center'},
            'DS': {'name': 'description', 'full_name': 'Description'},
            'DT': {'name': 'rundate', 'full_name': 'Run Date', 
                   'data_type': 'DATETIME'},
            'FO': {'name': 'flow', 'full_name': 'Flow Order'},
            'KS': {'name': 'key', 'full_name': 'Key Sequence'},
            'LB': {'name': 'library', 'full_name': 'Library'},
            'PG': {'name': 'program', 'full_name': 'Processing Program'},
            'PI': {'name': 'median', 'full_name': 'Predicted Median'},
            'PL': {'name': 'platform', 'full_name': 'Processing Platform'},
            'PU': {'name': 'unit', 'full_name': 'Platform Unit'},
            'SM': {'name': 'sample', 'full_name': 'Sample/Pool Name'},
        }
        
        self.params_program = {
            'ID': {'name': 'id', 'full_name': 'Program Identifier', 
                   'required': True},
            'PN': {'name': 'name', 'full_name': 'Program Name'},
            'CL': {'name': 'command', 'full_name': 'Command Line'},
            'PP': {'name': 'previous', 
                   'full_name': 'Previous Program Identifier'},
            'VN': {'name': 'version', 'full_name': 'Program Version'},
        }
        
        self.params_comment = {
            'CO': {'name': 'comment', 'full_name': 'Comment'},
        }
        
        
        # define list of schemas
        # schemas: dictionary of schemas;
        #      key: source data label -- if applicable.
        #     data: dictionary of schema parameters;
        #             name: (string)     name of the schema.
        #           params: (dictionary) schema parameters variable.
        #             list: (boolean)    are multiple schemas of this type allowed.
        
        self.schemas = {
                            'HD': {'name':'header',
                                   'params': self.params_header,
                                   'list': False},
                            'SQ': {'name':'sequence',
                                   'params': self.params_sequence,
                                   'list': True},
                            'RG': {'name':'group',
                                   'params': self.params_group,
                                   'list': True},
                            'PG': {'name':'program',
                                   'params': self.params_program,
                                   'list': True},
                            'CO': {'name':'comment',
                                   'params': self.params_comment,
                                   'list': True},
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
        self.logger.debug(
            '%s: extracting meta-data for %s' % (self.name, target))
        
        # open file       
        if (target.lower().endswith(self.suffixes[0])):    
            samfile = pysam.Samfile( target, "r" )
        else:
            samfile = pysam.Samfile( target, "rb" )
            
        if (samfile):
            result = samfile.header
        
        self.logger.debug(
            '%s: header = %s' % (self.name, pformat(result)))
       
        # return 
        return result          


    def saveMetadata(self, instance, metadata):
        """
        Save the metadata to Dataset_Files parameter sets.
        
        :param instance: file.
        :type instance: Dataset_file
        :param metadata: file metadata
        """
        self.logger.debug('%s: starting!' % (self.name))
        
        # save each line as a parameter set
        for key, line in metadata.items():
            # get the schema for this line
            schema_mapping = self.schemas[key]
            self.logger.debug('%s: schema mapping for key[%s] = %s' % (
                                    self.name, key, str(schema_mapping)))
            schema = self.getSchema(schema_mapping['name'])
            self.logger.debug('%s: schema for key[%s] = %s' % (
                                    self.name, key, str(schema)))
            
            # get the parameter set for this line
            parameter_names = self.getParameterNames(schema, 
                                                     schema_mapping['params'])
            self.logger.debug('%s: parameter names for key[%s] count = %d' % (
                                    self.name, key, len(parameter_names)))
            
            # create datafile parameter set
            self.logger.debug('%s: schema_mapping[\'list\'] = %s' % (
                                    self.name, str(schema_mapping['list'])))


            if not schema_mapping['list']:
                self.logger.debug('%s: create parameterset for line = %s' % (
                                    self.name, str(line)))
                parameter_set = DatafileParameterSet(schema=schema, 
                                                     dataset_file=instance)
                parameter_set.save()
                self.createDatafileParameters(schema_mapping['params'], 
                                              parameter_set, 
                                              parameter_names,  
                                              line)
            else:
                self.logger.debug('%s: line = %s' % (self.name, str(line)))
                for item in line:
                    if key == 'CO':
                        self.logger.debug('%s: create parameterset for item = %s' % (
                                    self.name, str(item)))
                        psets = self.getParameterSets(schema, instance)
                        if not psets:
                            parameter_set = DatafileParameterSet(
                                                    schema=schema,
                                                    dataset_file=instance)
                            parameter_set.save()
                        else:
                            parameter_set = psets[0]
                        self.createDatafileParameters(schema_mapping['params'], 
                                                      parameter_set, 
                                                      parameter_names,  
                                                      {'CO': item,})
                    else:
                        self.logger.debug('%s: create parameterset for item = %s' % (
                                    self.name, str(item)))
                        parameter_set = DatafileParameterSet(
                                                    schema=schema,
                                                    dataset_file=instance)
                        parameter_set.save()
                        self.createDatafileParameters(schema_mapping['params'], 
                                                      parameter_set, 
                                                      parameter_names,  
                                                      item)
    
        # finished with saveMetadata
        return
    
make_filter.__doc__ = FilterTemplate.__doc__


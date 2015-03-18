'''
Created on 17/03/2015

@author: Nick
'''
from base import FilterBase
from tardis.tardis_portal.models import DatafileParameterSet
from FlowCytometryTools import FCMeasurement

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
        self.version = "3.1"
        self.suffixes = ('.fcs', )
        
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
            'START_DATETIME':   {'name': 'sdt', 'full_name': 'Start Date/Time',
                                 'data_type': 'DATETIME', },
            'END_DATETIME':     {'name': 'edt', 'full_name': 'End Date/Time',
                                 'data_type': 'DATETIME', },
            'EXP':              {'name': 'exp', 'full_name': 'Experimenter', },
            'INST':             {'name': 'inst', 'full_name': 'Institution', },
            'LAST_MODIFIED':    {'name': 'mdt', 
                                 'full_name': 'Last Modified Date/Time', 
                                 'data_type': 'DATETIME', },
            'LAST_MODIFIER':    {'name': 'mdr', 'full_name': 'Last Modifier', },
            'LOST':             {'name': 'lost', 
                                 'full_name': 'Number of Events Lost', 
                                 'data_type': 'NUMERIC', },
            'MODE':             {'name': 'mode', 
                                 'full_name': 'Data Acquisition Mode', },
            'ORIGINALITY':      {'name': 'origin', 
                                 'full_name': 'Originality of Data', },
            'PLATEID':          {'name': 'pid', 
                                 'full_name': 'Plate Identifier', },
            'PLATENAME':        {'name': 'pname', 'full_name': 'Plate Name', },
            'PROJ':             {'name': 'proj', 'full_name': 'Project', },
            'TIMESTEP':         {'name': 'timestep', 'full_name': 'Time Step', 
                                 'data_type': 'NUMERIC',  },
            'TOT':              {'name': 'tot', 
                                 'full_name': 'Total Number of Events', 
                                 'data_type': 'NUMERIC',  },
            'VOL':              {'name': 'vol', 
                                 'full_name': 'Sample Volume Consumed', 
                                 'data_type': 'NUMERIC',  },
            'WELLID':           {'name': 'wellid', 
                                 'full_name': 'Well Identifier', },
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
        self.logger.debug('%s: starting to extract meta-data for %s' % (
                                                    self.name, target))
        
        sample = FCMeasurement(ID='target', datafile=target)
        logger.debug("sample keys = %s" % sample.meta.keys() )
        
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


def make_filter(name='', namespace=''):
    if not name:
        raise ValueError("fcsfilter requires a name to be defined.")
    if not namespace:
        raise ValueError("fcsfilter requires a namespace to be defined.")
    return FilterTemplate(name, namespace)
    
make_filter.__doc__ = Filter.__doc__


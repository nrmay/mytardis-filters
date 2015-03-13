# -*- coding: utf-8 -*-
#
# Copyright (c) 2010-2011, Monash e-Research Centre
#   (Monash University, Australia)
# Copyright (c) 2010-2011, VeRSI Consortium
#   (Victorian eResearch Strategic Initiative, Australia)
# All rights reserved.
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#    *  Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#    *  Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#    *  Neither the name of the VeRSI, the VeRSI Consortium members, nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE REGENTS AND CONTRIBUTORS ``AS IS'' AND ANY
# EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE REGENTS AND CONTRIBUTORS BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#

"""
samfiles.py

.. moduleauthor:: Nick May <nicholasmay2@gmail.com>

"""
import logging
import pysam

from tardis.tardis_portal.models import Schema, DatafileParameterSet
from tardis.tardis_portal.models import ParameterName, DatafileParameter

from pprint import pformat
from dateutil import parser

logger = logging.getLogger(__name__)

class Samfilter(object):
    """This filter extracts meta-data from SAM and BAM files.

    :param name: the short name of the schema.
    :type name: string
    :param schema: the name of the schema to load the EXIF data into.
    :type schema: string
    """
    def __init__(self, name, schema):
        self.name = name
        self.schema = schema
        
        # a list of parameters we want to save      
        self.version = "6f8dfe4"
        
        self.params_header = {
            'VN': {'name': 'format', 'full_name': 'Format Version', 'required': True, 'default': 'unknown'},
            'SO': {'name': 'sorting', 'full_name': 'Sorting Order'},
        }
        
        self.params_sequence = {
            'SN': {'name': 'name', 'full_name': 'Reference Sequence Name', 'required': True},
            'LN': {'name': 'length', 'full_name': 'Sequence Length', 'required': True, 'data_type': 'NUMERIC'},
            'AS': {'name': 'genome', 'full_name': 'Genome Assembly Identifier'},
            'M5': {'name': 'md5', 'full_name': 'MD5 Checksum'},
            'SP': {'name': 'species', 'full_name': 'Species'},
            'UR': {'name': 'uri', 'full_name': 'Sequence URI'},
        }
        
        self.params_group = {
            'ID': {'name': 'id', 'full_name': 'Read Group Identifier', 'required': True},
            'CN': {'name': 'center', 'full_name': 'Name of the Sequencing Center'},
            'DS': {'name': 'description', 'full_name': 'Description'},
            'DT': {'name': 'rundate', 'full_name': 'Run Date', 'data_type': 'DATETIME'},
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
            'ID': {'name': 'id', 'full_name': 'Program Identifier', 'required': True},
            'PN': {'name': 'name', 'full_name': 'Program Name'},
            'CL': {'name': 'command', 'full_name': 'Command Line'},
            'PP': {'name': 'previous', 'full_name': 'Previous Program Identifier'},
            'VN': {'name': 'version', 'full_name': 'Program Version'},
        }
        
        self.params_comment = {
            'CO': {'name': 'comment',  'full_name': 'Comment'},
        }
        
        self.schema_names = {
                            'HD': {'name':'header',   'params': self.params_header,   'list': False},
                            'SQ': {'name':'sequence', 'params': self.params_sequence, 'list': True},
                            'RG': {'name':'group',    'params': self.params_group,    'list': True},
                            'PG': {'name':'program',  'params': self.params_program,  'list': True},
                            'CO': {'name':'comment',  'params': self.params_comment,  'list': True},
        }

        self.suffixes = ('.sam','.bam', '.tam')
        
        return

    # ---------------------
    #     main process
    #----------------------
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
            logger.debug("\n\n\n")
            logger.info("samfile: filepath = " + filepath)

            # check filepath suffixes
            if not(filepath.lower().endswith(self.suffixes[0]) 
                   or filepath.lower().endswith(self.suffixes[1])
                   or filepath.lower().endswith(self.suffixes[2])):
                return None

            # check its a new file
            psets = instance.getParameterSets()
            if not psets:
                # set the metadata (a dictionary of dictionaries)
                metadata = self.extractMetadata(filepath)            
                logger.debug('samfile: meta-data = ' + str(metadata))

                # save this metadata to a file
                if metadata:
                    self.saveMetadata(instance, metadata)
            
            self.printDatafileMetadata(instance)
            
        except Exception, e:
            # if anything goes wrong, log it in tardis.log and exit
            logger.info(e)
            
        return

    # ---------------------------
    # extract the samfile header
    # as a multi-level dictionary
    # ---------------------------
    def extractMetadata(self, target):
        """extract header row from sam/bam file.
        
        :param target: the file path
        """
        
        logger.debug('samfiles: extracting meta-data for %s' % target)
        result = None
        
        # open file       
        if (target.lower().endswith(self.suffixes[0])):    
            samfile = pysam.Samfile( target, "r" )
        else:
            samfile = pysam.Samfile( target, "rb" )
            
        if (samfile):
            result = samfile.header
        
        logger.debug('samfiles: header = %s' % pformat(result))
       
        # return 
        return result          

    # ----------------------------------
    # save, or overwrite, the datafile's f
    # meta-data on the database
    # ----------------------------------
    def saveMetadata(self, instance, metadata):
        """Save the metadata to Dataset_Files parameter sets.
        
        :param instance: sam file.
        :param metadata: sam file header as a multi-level dictionary.
        """
        logger.debug('starting!')
        
        # save each line as a parameter set
        for key, line in metadata.items():
            # get the schema for this line
            schema_mapping = self.schema_names[key]
            logger.debug("schema mapping for key[" + key + "] = " + str(schema_mapping))
            schema = self.getSchema(schema_mapping['name'])
            logger.debug("schema for key[" + key + "] = " + str(schema))
            
            # get the parameter set for this line
            parameter_names = self.getParameterNames(schema, schema_mapping['params'])
            logger.debug("parameter names for key[" + key + "] count = %d " % len(parameter_names))
            
            # create datafile parameter set
            logger.debug('schema_mapping[\'list\'] = ' + str(schema_mapping['list']))


            if not schema_mapping['list']:
                logger.debug('create parameterset for line = '  + str(line))
                parameter_set = DatafileParameterSet(schema=schema,dataset_file=instance)
                parameter_set.save()
                self.createDatafileParameters(schema_mapping['params'], parameter_set, 
                                              parameter_names,  
                                              line)
            else:
                logger.debug('line = ' + str(line))
                for item in line:
                    if key == 'CO':
                        logger.debug('create parameterset for item = '  + str(item))
                        psets = self.getParameterSets(schema, instance)
                        if not psets:
                            parameter_set = DatafileParameterSet(schema=schema,dataset_file=instance)
                            parameter_set.save()
                        else:
                            parameter_set = psets[0]
                        self.createDatafileParameters(schema_mapping['params'], parameter_set, 
                                                      parameter_names,  
                                                      {'CO': item,})
                    else:
                        logger.debug('create parameterset for item = '  + str(item))
                        parameter_set = DatafileParameterSet(schema=schema,dataset_file=instance)
                        parameter_set.save()
                        self.createDatafileParameters(schema_mapping['params'], parameter_set, 
                                                      parameter_names,  
                                                      item)
    
        # finished with saveMetadata
        return

    # --------------------------------
    # get the schema for a header line
    # --------------------------------
    def getSchema(self, key):
        """Return the schema object that the paramater set will use.
        """
        schema = None
        fullname = str(self.schema)
        
        if not fullname.endswith('/'):
            fullname += '/'
        
        fullname += self.version + '/' + key
        
        logger.debug("getSchema(" + key + ") as " + fullname)
            
        try:
            # get existing schema
            schema = Schema.objects.get(namespace__exact=fullname)
        except Schema.DoesNotExist:
            # create missing schema
            schema = Schema(namespace=fullname, name=("SAM Format - " + key), type=Schema.DATAFILE)
            schema.save()
          
        # finished      
        return schema

    # ----------------------------------------
    # get a list of parameters for this schema 
    # ----------------------------------------
    def getParameterSets(self, schema, datafile):
        """Return a list of the parameter sets for a given schema and datafile.
        """
        logger.debug('getParameterSets for schema[id=' + str(schema.id) + '] and datafile[id=' + str(datafile.id) + ']')
        
        result = []
        psets = datafile.getParameterSets()
        for pset in psets:
            if pset.schema == schema:
                result.append(pset)
          
        # finished    
        logger.debug('getParameterSets() found %d items' % len(result))  
        return result

    # ----------------------------------------
    # get a list of parameters for this schema 
    # ----------------------------------------
    def getParameterNames(self, schema, params):
        """Return a list of the parameters that will be saved.
        """
        logger.debug('getParameterNames for schema[' + str(schema) + ']')
        
        parameter_names = list(ParameterName.objects.filter(schema=schema))
        logger.debug('list ParameterName for schema[' + str(schema) + '] found %d ' % len(parameter_names))
            
        # create objects if empty
        if not parameter_names:
            for param in params.itervalues():
                logger.debug('create ParameterName for param = ' + str(param))
                
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
        logger.debug('getParameterNames() returned %d names' % len(parameter_names))
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
        
        logger.debug('tags = ' + str(tags))    
        logger.debug('metadata = ' + str(metadata))    
        logger.debug('paramnames = ' + str(paramnames))    
       
        for key, values in tags.items():
            logger.debug('tags key[' + str(key) + '] values[' + str(values) + ']')
            
            # get the parametername
            for item in paramnames:
                if item.name == values.get('name'):
                    pname = item
                    logger.debug('param.name = ' + str(pname))
            
            # create the datafile parameter
            if metadata.has_key(key):
                # set value from metadata
                param = DatafileParameter(parameterset=paramset,name=pname)
                param = self.setParameterValue(param,pname,metadata.get(key))
                logger.debug('parameter = %s' % pformat(param))

            elif values.has_key('default'):
                # check default provided
                param = DatafileParameter(parameterset=paramset,name=pname)
                param = self.setParameterValue(param,pname,values.get('default'))
                logger.debug('parameter = ' + str(param) + ' (default)')

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
            logger.debug('isDateTime = %s ' % value)
            dvalue = parser.parse(value)
            logger.debug("date = " + str(dvalue))
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

        logger.debug('------------------------------------------------------------------')
        logger.debug('datafile id = ' + str(target.id))
        logger.debug('   filename = ' + str(target.filename))
        
        # parameter sets
        psets = target.getParameterSets()
        logger.debug('parameter sets:')
        logger.debug('   count = ' + str(len(psets)))
        for item in psets:
            logger.debug('   parameter set id = ' + str(item.id))
            schema = item.schema
            logger.debug('      schema id = ' + str(schema.id))
            logger.debug('         type = ' + str(schema.type))
            logger.debug('         namespace = ' + str(schema.namespace))
            pnames = list(ParameterName.objects.filter(schema=schema))
            logger.debug('         parameter names count = ' + str(len(pnames)))
            for pn in pnames:
                logger.debug('            name = ' + str(pn)) 
            params = DatafileParameter.objects.filter(parameterset=item)
            logger.debug('      parameters count = ' + str(len(params)))
            for ps in params:
                logger.debug('         param id = ' + str(ps.id))
                logger.debug('            name  = ' + str(ps.name.name))
                if ps.datetime_value:
                    logger.debug('            value = ' + str(ps.datetime_value))
                elif ps.numerical_value:
                    logger.debug('            value = ' + str(ps.numerical_value))
                else:
                    logger.debug('            value = ' + ps.string_value)
                     
        # finished
        logger.debug('------------------------------------------------------------------')
        return

make_filter.__doc__ = Samfilter.__doc__

'''
Created on 17/03/2015

@author: Nick
'''
import unittest
from os import path
from compare import expect
from django.test import TestCase
from tardis.tardis_portal.filters.samformat.samfiles import Samfilter 
from tardis.tardis_portal.tests.test_download import get_size_and_sha512sum 
from tardis.tardis_portal.models import User, UserProfile, Location, \
    Experiment, Dataset, ObjectACL, Dataset_File, Replica, Schema, \
    ParameterName, DatafileParameter
    
class FilterTest(unittest.TestCase):

    def setUp(self):
        '''
        Create test owner without enough details
        '''
        
        username, email, password = ('testuser',
                                     'testuser@example.test',
                                     'password')
        user = User.objects.create_user(username, email, password)
        profile = UserProfile(user=user, isDjangoAccount=True)
        profile.save()

        Location.force_initialize()

        # Create test experiment and make user the owner of it
        experiment = Experiment(title='Text Experiment',
                                institution_name='Test Uni',
                                created_by=user)
        experiment.save()
        acl = ObjectACL(
            pluginId='django_user',
            entityId=str(user.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        dataset = Dataset(description='dataset description...')
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        
        def create_datafile(index):
            testfile = path.join(path.dirname(__file__), 'fixtures',
                                 'samfile_test%d.sam' % index)

            size, sha512sum = get_size_and_sha512sum(testfile)

            datafile = Dataset_File(dataset=dataset,
                                    filename=path.basename(testfile),
                                    size=size,
                                    sha512sum=sha512sum)
            datafile.save()
            base_url = 'file://' + path.abspath(path.dirname(testfile))
            location = Location.load_location({
                'name': 'test-sam', 'url': base_url, 'type': 'external',
                'priority': 10, 'transfer_provider': 'local'})
            replica = Replica(datafile=datafile,
                              url='file://'+path.abspath(testfile),
                              protocol='file',
                              location=location)
            replica.verify()
            replica.save()
            return Dataset_File.objects.get(pk=datafile.pk)

        self.dataset = dataset
        self.datafiles = [create_datafile(i) for i in (1,2)]


    def tearDown(self):
        # finished
        return


    def testSchemaNamespace(self):
        '''
        verify the schema namespace
        '''
        
        samformat = 'SAMFORMAT'
        version="6f8dfe4"
        schema = 'http://mytardis.org/samformat/noend'
        fullname = schema + "/" + version + "/"
         
        # run base
        Samfilter(samformat,schema)(None, instance=self.datafiles[0])
         
        # get datafile
        datafile = Dataset_File.objects.get(id=self.datafiles[0].id)
        self.assertEqual(datafile.id,self.datafiles[0].id,"datafile id not matched!")
                 
        # Check that two schemas were created
        print "schema count = %d " % Schema.objects.all().count()
         
        # check schemas
        schemas = Schema.objects.filter(namespace__startswith=fullname)
        self.assertEqual(schemas.count(),2,"schema count not matched!")
        schemas = Schema.objects.filter(namespace__exact=fullname + 'header')
        self.assertEqual(schemas.count(),1,"schema for header count not matched!")
        schemas = Schema.objects.filter(namespace__exact=fullname + 'sequence')
        self.assertEqual(schemas.count(),1,"schema for sequence count not matched!")   
        schemas = Schema.objects.filter(namespace__exact=fullname + 'group')
        self.assertEqual(schemas.count(),0,"schema for group count not matched!")
    
        # finished
        return     

    
    def testSmallHeader(self):
        '''
        test small sam file: with one HD and SQ lines
        '''
        
        samformat = 'SAMFORMAT'
        version="6f8dfe4"
        namespace = 'http://mytardis.org/samformat/small/'
        fullname = namespace + version + "/"
         
        # run base
        Samfilter(samformat,namespace)(None, instance=self.datafiles[0])
         
        # get datafile
        datafile = Dataset_File.objects.get(id=self.datafiles[0].id)
        self.assertEqual(datafile.id,self.datafiles[0].id,"datafile id not matched!")
         
        # Check that two schemas were created
        print "schema count = %d " % Schema.objects.all().count()
         
        # check schemas
        schemas = Schema.objects.filter(namespace__startswith=fullname)
        self.assertEqual(schemas.count(),2,"schema count not matched!")
        
        # check header line
        try:
            # check schema
            schemaname = fullname + 'header'
            schema = Schema.objects.get(namespace__exact=schemaname)
            print 'schema[' + schemaname + '] exists'
             
            # check header parameter names
            param_names = ParameterName.objects.filter(schema=schema)
            self.assertEqual(param_names.count(),2,"parameter names not matched for " + schemaname)
            param = param_names.get(name__exact='format')
            expect(param.full_name).to_equal('Format Version')
            expect(param.data_type).to_equal(ParameterName.STRING)
            param = param_names.get(name__exact='sorting')
            expect(param.full_name).to_equal('Sorting Order')
            expect(param.data_type).to_equal(ParameterName.STRING)
            print 'schema[' + schemaname + '] parameter names matched'
             
            # check parameter sets
            pset = datafile.getParameterSets().filter(schema__exact=schema)
            self.assertEqual(pset.count(),1,"count of header parametersets not matched!")
             
            # Check all the expected parameters are there
            psm = pset[0]
            pname = 'format'
            expect(psm.get_param(pname).string_value).to_equal('1.0')
         
                        
        except DatafileParameter.DoesNotExist:
            self.fail('DatafileParameter[name=\'' + pname + '\'] not found')    
     
        except Schema.DoesNotExist:
            self.fail('Schema[\'' + schemaname + '\'] not found')    
             
        # check sequence line
        try:
            # check schema 
            schemaname = fullname + 'sequence'
            schema = Schema.objects.get(namespace__exact=schemaname)
            print 'schema[' + schemaname + '] exists'
 
            # check sequence parameter names
            param_names = ParameterName.objects.filter(schema=schema)
            self.assertEqual(param_names.count(),6,"parameter names not matched for " + schemaname)
            param = param_names.get(name__exact='name')
            expect(param.full_name).to_equal('Reference Sequence Name')
            expect(param.data_type).to_equal(ParameterName.STRING)
            param = param_names.get(name__exact='length')
            expect(param.full_name).to_equal('Sequence Length')
            expect(param.data_type).to_equal(ParameterName.NUMERIC)
            param = param_names.get(name__exact='genome')
            param = param_names.get(name__exact='md5')
            param = param_names.get(name__exact='species')
            param = param_names.get(name__exact='uri')
            print 'schema[' + schemaname + '] parameter names matched'
             
            # check parameter sets
            pset = datafile.getParameterSets().filter(schema__exact=schema)
            self.assertEqual(pset.count(),1,"count of sequence parametersets not matched!")
             
            # Check all the expected parameters are there
            psm = pset[0]
            pname = 'length'
            expect(psm.get_param(pname).numerical_value).to_equal(48297693)
            pname = 'name'
            expect(psm.get_param(pname).string_value).to_equal('2')
                  
        except DatafileParameter.DoesNotExist:
            self.fail('DatafileParameter[name=\'' + pname + '\'] not found')    
     
        except Schema.DoesNotExist:
            self.fail('check schema[' + schemaname + '] failed')
 
 
        # check parameter sets
        paramsets = datafile.getParameterSets()
        self.assertEqual(paramsets.count(),2,"datafile parameterset count not matched!")      
   
        # Check we won't create a duplicate dataset
        Samfilter(samformat,namespace)(None, instance=self.datafiles[0])
         
        # check parameter sets
        paramsets = datafile.getParameterSets()
        self.assertEqual(paramsets.count(),2,"datafile parameterset count not matched!")      
   
        # finished testSmallHeader
        return
 
    
    def testLargeHeader(self):
        '''
        verify a large header with all line
        '''
        
        samformat = 'SAMFORMAT'
        version="6f8dfe4"
        schema = 'http://mytardis.org/samformat/large/'
        fullname = schema + version + "/"
          
        # run base
        # ----------
        Samfilter(samformat,schema)(None, instance=self.datafiles[1])
          
        # check datafile
        # --------------
        datafile = Dataset_File.objects.get(id=self.datafiles[1].id)
        self.assertEqual(datafile.id,self.datafiles[1].id,"datafile id not matched!") 
          
        # check schemas
        # -------------
        schemas = Schema.objects.filter(namespace__startswith=fullname)
        self.assertEqual(schemas.count(),5,"schema count not matched!")
        
          
        # check parameter sets
        # --------------------
        dataset = Dataset.objects.get(id=self.dataset.id)
        self.assertEqual(dataset.getParameterSets().count(),0,"parameter set not matched!")
                  
        # check header line
        # -----------------
        # check schema
        schemaname = fullname + 'header'
        schema = Schema.objects.get(namespace__exact=schemaname)
        # check parameter sets
        pset = datafile.getParameterSets().filter(schema__exact=schema)
        self.assertEqual(pset.count(),1,"count of sequence parametersets not matched!")
        # Check all the expected parameters are there
        psm = pset[0]
        pname = 'format'
        expect(psm.get_param(pname).string_value).to_equal('1.0')
        pname = 'sorting'
        try:
            psm.get_param(pname)
            self.fail('DatafileParameter[name=\'' + pname + '\'] found in error.')
        except DatafileParameter.DoesNotExist:
            print 'ok! missing DatafileParameter[name=\'' + pname + '\']  expected.'
               
        # check sequence lines
        # --------------------
        # check schema 
        schemaname = fullname + 'sequence'
        schema = Schema.objects.get(namespace__exact=schemaname)
        # check parameter sets
        pset = datafile.getParameterSets().filter(schema__exact=schema)
        self.assertEqual(pset.count(),2,"count of sequence parametersets not matched!")
        # Check all the expected parameters are there
        psm = pset[0]
        pname = 'name'
        pvalue = psm.get_param(pname).string_value
        pname = 'length'
        if pvalue == 'chr1':
            expect(psm.get_param(pname).numerical_value).to_equal(1575)
        elif pvalue == 'chr2':
            expect(psm.get_param(pname).numerical_value).to_equal(1584)
        else:
            self.fail('unknown sequence name[' + pvalue + '] found!')                
  
        # check group lines
        # -----------------
        # check schema 
        schemaname = fullname + 'group'
        schema = Schema.objects.get(namespace__exact=schemaname)
        # check sequence parameter names
        param_names = ParameterName.objects.filter(schema=schema)
        self.assertEqual(param_names.count(),12,"count of parameter names not matched!")
        param = param_names.get(name__exact='rundate')
        expect(param.full_name).to_equal('Run Date')
        expect(param.data_type).to_equal(ParameterName.DATETIME)
        # check DatafileParameterSet
        psets = datafile.getParameterSets().filter(schema__exact=schema)
        self.assertEqual(psets.count(),2,"count of group parametersets not matched!")    
        # check parameter values
        for pset in psets:
            gid = pset.get_param('id').string_value
            gunit = pset.get_param('unit').string_value
            glib = pset.get_param('library').string_value
            gsample = pset.get_param('sample').string_value
            gcenter = pset.get_param('center').string_value
            if gid == 'L1':
                self.assertEqual(gunit,'SC_1_10',"program[id=%s] unit not matched!" % gid)
                self.assertEqual(glib,'SC_1',"program[id=%s] library not matched!" % gid)
                self.assertEqual(gsample,'NA12891',"program[id=%s] center not matched!" % gid)               
                self.assertEqual(gcenter,'name:with:colon',"program[id=%s] center not matched!" % gid)               
            elif gid == 'L2':
                gdate = pset.get_param('rundate').datetime_value
                self.assertEqual(gunit,'SC_2_12',"program[id=%s] unit not matched!" % gid)
                self.assertEqual(glib,'SC_2',"program[id=%s] library not matched!" % gid)
                self.assertEqual(gsample,'NA12891',"program[id=%s] center not matched!" % gid)               
                self.assertEqual(gcenter,'name:with:colon',"program[id=%s] center not matched!" % gid)   
                self.assertEqual(gdate.day,11,"program[rdate=%s] day not matched!" % gid)
                self.assertEqual(gdate.month,11,"program[rdate=%s] month not matched!" % gid)       
                self.assertEqual(gdate.year,2013,"program[rdate=%s] year not matched!" % gid)            
            else:
                self.fail('unexpected group id = ' + gid)
  
        # check program lines
        # -------------------
        # check schema 
        schemaname = fullname + 'program'
        schema = Schema.objects.get(namespace__exact=schemaname)
        # check sequence parameter names
        param_names = ParameterName.objects.filter(schema=schema)
        self.assertEqual(param_names.count(),5,"count of parameter names not matched!")
        # check DatafileParameterSet
        psets = datafile.getParameterSets().filter(schema__exact=schema)
        self.assertEqual(psets.count(),2,"count of program parametersets not matched!")
        # check parameter values
        for pset in psets:
            pid = pset.get_param('id').string_value
            pver = pset.get_param('version').string_value
            if pid == 'P1':
                self.assertEqual(pver,'1.0',"program[id=P1] version not matched!")
            elif pid == 'P2':
                self.assertEqual(pver,'1.1',"program[id=P1] version not matched!")
            else:
                self.fail('unexpected program id = ' + pid)      
 
        # check comment lines
        # -------------------
        # check schema 
        schemaname = fullname + 'comment'
        schema = Schema.objects.get(namespace__exact=schemaname)
        # check sequence parameter names
        param_names = ParameterName.objects.filter(schema=schema)
        self.assertEqual(param_names.count(),1,"count of parameter names not matched!")
        # check parameter sets
        pset = datafile.getParameterSets().filter(schema__exact=schema)
        self.assertEqual(pset.count(),1,"count of comment parametersets not matched!")
        # Check all the expected parameters are there
        params = pset[0].get_params('comment')
        self.assertEqual(params.count(),2,"count of comment parameters not matched!")
        self.assertEqual(params[0].string_value,'this is a comment',"comment[0] not matched!")
        self.assertEqual(params[1].string_value,'this is another comment',"comment[1] not matched!")
  
        # Check we won't create a duplicate dataset
        # -----------------------------------------
        Samfilter(samformat,schema)(None, instance=self.datafiles[1])
        dataset = Dataset.objects.get(id=self.dataset.id)
        expect(dataset.getParameterSets().count()).to_equal(0)
     
        # finished testSmallHeader
        return



if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
'''
Created on 17/03/2015

@author: Nick
'''
import unittest
from os import path, environ
from compare import expect
from django.test import TestCase
from django import settings

from tardis.tardis_portal.filters.fcsformat.template import FilterTemplate 
from tardis.tardis_portal.tests.test_download import get_size_and_sha512sum 
from tardis.tardis_portal.models import User, UserProfile, Location, \
    Experiment, Dataset, ObjectACL, Dataset_File, Replica, Schema, \
    ParameterName, DatafileParameter

class FilterTest(unittest.TestCase):
    
    def __init__(self):
        self.filenames = ("first.fcs", "second.fcs")
        self.fixtures = "fixtures"
        self.experiment = "Test Experiment"
        self.dataset = "Test Dataset"
        self.institution = "Test University"
        self.duser = "django_user"
        self.user = "testuser"
        self.email = "testuser.@tu.edu.au"
        self.password = "password"
        
        environ.setdefault("SETTINGS_MODULE", 'mytardis-filters.settings')
        #settings.configure()
        return

    def setUp(self):
        # Create test owner without enough details
        username, email, password = (self.user,self.email,self.password)
        user = User.objects.create_user(username, email, password)
        profile = UserProfile(user=user, isDjangoAccount=True)
        profile.save()

        Location.force_initialize()

        # Create test experiment and make user the owner of it
        experiment = Experiment(title=self.experiment,
                                institution_name=self.institution,
                                created_by=user)
        experiment.save()
        acl = ObjectACL(
            pluginId=self.duser,
            entityId=str(user.id),
            content_object=experiment,
            canRead=True,
            isOwner=True,
            aclOwnershipType=ObjectACL.OWNER_OWNED,
        )
        acl.save()

        # Create test dataset
        dataset = Dataset(description=self.dataset)
        dataset.save()
        dataset.experiments.add(experiment)
        dataset.save()
        
        # create test datafiles
        self.datafiles = [self.create_datafile(dataset,name) 
                          for name in self.filenames]
        
        return

        
    def create_datafile(self, dataset, filename):
        # get file 
        testfile = path.join(path.dirname(__file__),self.fixtures,filename)
        size, sha512sum = get_size_and_sha512sum(testfile)

        # create datafile
        datafile = Dataset_File(dataset=dataset,
                                filename=path.basename(testfile),
                                size=size,
                                sha512sum=sha512sum)
        datafile.save()
            
        # create replica
        base_url = 'file://' + path.abspath(path.dirname(testfile))
        file_url = 'file://' + path.abspath(testfile)
        location = Location.load_location({'name': 'test-location', 
                                'url': base_url, 'type': 'external', 
                                'priority': 10, 'transfer_provider': 'local'})
        replica = Replica(datafile=datafile, url=file_url, protocol='file',
                              location=location)
        replica.verify()
        replica.save()
            
        # return dataset_file
        return Dataset_File.objects.get(pk=datafile.pk) 


    def tearDown(self):
        pass


# ------------------------------------
    # verify the schema namespace
    # ------------------------------------
    def testSchemaNamespace(self):
        # test small sam file: with one HD and SQ lines
        filterformat = 'FCSFORMAT'
        version="3.1"
        schema = 'http://mytardis.org/fcsformat/'
        fullname = schema + "/" + version + "/"
         
        # run filter
        FilterTemplate(filterformat,schema)(None, instance=self.datafiles[0])
         
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
     
        # finished
        return     


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
import unittest
import os
import os.path
import urllib
import tarfile
import subprocess
import shutil

# directory paths from current directory
DIR_UNITTEST_RT = "v20unittestruntime"
DIR_DOWNLOAD = os.path.join(DIR_UNITTEST_RT, "v20downloads")
DIR_STAGING = os.path.join(DIR_UNITTEST_RT, "v20staging")
DIR_SNAPPY = os.path.join(DIR_STAGING, "snappy")
DIR_DEPOT = os.path.join(DIR_UNITTEST_RT, "v20depot")
DIR_INSTALL = os.path.join(DIR_UNITTEST_RT, "v20install")

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        if not os.path.exists(DIR_UNITTEST_RT):
            os.mkdir(DIR_UNITTEST_RT)
        self._setup_staging()
        self._setup_depot()
        self._setup_install()


    '''
    clear the depot and install.
    '''
    def tearDown(self):
        self._teardown_depot()
        self._teardown_install()
        pass

    '''
    check if snappy is downloaded  to a folder "download".
    if not then download it from a link. 
    extract the snappy in the dowload folder.
    create a staging folder v20staging and install the snappy in that folder using gnu tool commands with --prefix
    and DEST attributes.
    store the stats of the folder somewhere globally.
    this will complete the setup
    '''
    def _setup_staging(self):
        if not os.path.exists(DIR_DOWNLOAD):
            os.mkdir(DIR_DOWNLOAD)
        if not os.path.exists(DIR_STAGING):
            os.mkdir(DIR_STAGING)
        if not os.path.exists(DIR_SNAPPY):
            self._download_snappy()
            self._build_snappy()

    def _setup_depot(self):
        os.mkdir(DIR_DEPOT)

    def _setup_install(self):
        os.mkdir(DIR_INSTALL)

    def _teardown_depot(self):
        if os.path.exists(DIR_DEPOT):
            shutil.rmtree(DIR_DEPOT)

    def _teardown_install(self):
        if os.path.exists(DIR_INSTALL):
            shutil.rmtree(DIR_INSTALL)

    def _download_snappy(self):
        urllib.urlretrieve("http://snappy.googlecode.com/files/snappy-1.0.5.tar.gz", os.path.join(DIR_DOWNLOAD, "snappy-1.0.5.tar.gz"))
        tf = tarfile.open(os.path.join(DIR_DOWNLOAD, "snappy-1.0.5.tar.gz"))
        tf.extractall(DIR_DOWNLOAD)
        #tf.extractall()
        tf.close()

    def _build_snappy(self):
        # Need to work to make it platform independent for prefix
        pwd = os.getcwd()
        subprocess.call([os.path.join(DIR_DOWNLOAD, "snappy-1.0.5", "configure"), "--prefix=/opt/couchbase"])
        subprocess.call(["make", "install", "DESTDIR=" + os.path.join(pwd, DIR_SNAPPY)])

class ManifestTestCases(BaseTestCase):
    def test_test(self):
        print "testing......"

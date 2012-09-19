import unittest
import os
import os.path
import urllib
import tarfile
import subprocess
import shutil
import json
import logging

from commons import CommonConsts, CommonUtils
from manifestutils import ManifestGenerator
from swdepot import SoftwareDepot

# directory paths from current directory
DIR_UNITTEST_RT = "v20unittestruntime"
DIR_DOWNLOAD = os.path.join(DIR_UNITTEST_RT, "v20downloads")
DIR_STAGING = os.path.join(DIR_UNITTEST_RT, "v20staging")
DIR_SNAPPY = os.path.join(DIR_STAGING, "snappy")
DIR_SNAPPY_STAGING = os.path.join(DIR_STAGING, "snappy", "opt", "couchbase") # since we setting --prefix=/opt/couchbase while make install
DIR_DEPOT = os.path.join(DIR_UNITTEST_RT, "v20depot")
DIR_DEPOT_DATAFILES = os.path.join(DIR_DEPOT, CommonConsts.SW_DEPOT_DATAFILES_DIR)
DIR_DEPOT_MANIFESTFILES = os.path.join(DIR_DEPOT, CommonConsts.SW_DEPOT_MANIFEST_FILE_DIR)
DIR_DEPOT_TEMP = os.path.join(DIR_DEPOT, "temp")

DIR_INSTALL = os.path.join(DIR_UNITTEST_RT, "v20install")

SNAPPY_PKG_NAME = "snappy"
SNAPPY_VERSION = "1.0.5"
SNAPPY_PLATFORM = "ubuntu-12.04"
SNAPPY_MANIFEST_FILENAME = "snappy-1.0.5-ubuntu-12.04.json"

class BaseTestCase(unittest.TestCase):

    def setUp(self):
        try:
            self.log = logging.getLogger()
            self.log.info("setup started...")
            if not os.path.exists(DIR_UNITTEST_RT):
                os.mkdir(DIR_UNITTEST_RT)
            self._setup_staging()
            self._setup_depot()
            self._setup_install()
            self.log.info("setup completed.")
        except Exception as e:
            self._teardown_setup()
            raise e


    '''
    clear the depot and install.
    '''
    def tearDown(self):
        self.log.info("tearDown started...")
        self._teardown_depot()
        self._teardown_install()
        self.log.info("tearDown completed.")
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
        os.mkdir(DIR_DEPOT_MANIFESTFILES)
        os.mkdir(DIR_DEPOT_DATAFILES)
        os.mkdir(DIR_DEPOT_TEMP)

    def _setup_install(self):
        os.mkdir(DIR_INSTALL)

    def _teardown_setup(self):
        if os.path.exists(DIR_UNITTEST_RT):
            shutil.rmtree(DIR_UNITTEST_RT)

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
        os.chdir(os.path.join(DIR_DOWNLOAD, "snappy-1.0.5"))
        subprocess.call([ os.path.join(".", "configure"), "--prefix=/opt/couchbase"])
        subprocess.call(["make", "install", "DESTDIR=" + os.path.join(pwd, DIR_SNAPPY)])
        os.chdir(pwd)

    '''
    Util functions for test cases
    '''
    def generate_manifest_file(self):
        m = ManifestGenerator(SNAPPY_PKG_NAME, SNAPPY_VERSION, SNAPPY_PLATFORM, os.path.join(DIR_SNAPPY_STAGING), DIR_DEPOT_TEMP)
        m.generate_manifest()


class ManifestTestCases(BaseTestCase):
    def test_genfile(self):
        '''
        python voltron20.py manifest genfile --package_name="snappy" -ver="1.0.5" -p="ubuntu-12.04" 
        -sd="/tmp/snappy/opt/couchbase" -tfp="/home/suhail/workspace/temp/manifest-files"
        '''
        m = ManifestGenerator(SNAPPY_PKG_NAME, SNAPPY_VERSION, SNAPPY_PLATFORM, os.path.join(DIR_SNAPPY_STAGING), DIR_DEPOT_TEMP)
        m.generate_manifest()
        mfn = CommonUtils.generate_manifest_filename("snappy", "1.0.5", "ubuntu-12.04", "json")
        with open (os.path.join(DIR_DEPOT_TEMP, mfn)) as f:
            manifest = json.load(f)
        assert set([ CommonConsts.MF_KEY_BUILD, CommonConsts.MF_KEY_DEPENDS, CommonConsts.MF_KEY_DIRS, CommonConsts.MF_KEY_FILES]) == set(manifest)
        assert len(manifest[CommonConsts.MF_KEY_DIRS]) == 5
        assert len(manifest[CommonConsts.MF_KEY_FILES]) == 16

class SWDepoTestCases(BaseTestCase):
    def setUp(self):
        BaseTestCase.setUp(self)
        self.generate_manifest_file()


    def test_depot_add(self):
        self._add_snappy_to_depot()
        assert CommonUtils.get_filecount_for_dir_tree(DIR_DEPOT_DATAFILES) == 14

    def test_depot_update(self):
        self._add_snappy_to_depot()
        self._update_snappy_in_depot()
        assert CommonUtils.get_filecount_for_dir_tree(DIR_DEPOT_DATAFILES) == 14

    def test_depot_delete(self):
        self._add_snappy_to_depot()
        self._delete_snappy_from_depot()
        assert not os.path.exists(os.path.join(DIR_DEPOT_MANIFESTFILES, SNAPPY_MANIFEST_FILENAME))
        assert not os.path.exists(os.path.join(DIR_DEPOT_DATAFILES, os.path.basename(SNAPPY_MANIFEST_FILENAME)))

    def test_depot_list(self):
        self._add_snappy_to_depot()
        sd = SoftwareDepot(DIR_DEPOT)
        lst = sd.list()
        assert len(lst) == 1
        assert SNAPPY_MANIFEST_FILENAME in lst

    def _add_snappy_to_depot(self):
        '''
         python voltron20.py depot -l="/cbdepot" add --package_name="snappy" -ver="1.0.5" 
        -p="ubuntu-12.04" -sd="/tmp/snappy/opt/couchbase" -md="/home/suhail/workspace/temp/manifest-files"
        '''
        sd = SoftwareDepot(DIR_DEPOT)
        sd.add(SNAPPY_PKG_NAME, SNAPPY_VERSION, SNAPPY_PLATFORM, DIR_SNAPPY_STAGING, os.path.join(DIR_DEPOT_TEMP))

    def _update_snappy_in_depot(self):
        '''
        python voltron20.py depot -l="/cbdepot" update --package_name="snappy" -ver="1.0.5" 
        -p="ubuntu-12.04" -sd="/tmp/snappy/opt/couchbase" -md="/home/suhail/workspace/temp/manifest-files"        '''
        sd = SoftwareDepot(DIR_DEPOT)
        sd.update(SNAPPY_PKG_NAME, SNAPPY_VERSION, SNAPPY_PLATFORM, DIR_SNAPPY_STAGING, os.path.join(DIR_DEPOT_TEMP))

    def _delete_snappy_from_depot(self):
        '''
         python voltron20.py depot -l="/cbdepot" delete --package_name="snappy" -ver="1.0.5" -p="ubuntu-12.04"
        '''
        sd = SoftwareDepot(DIR_DEPOT)
        sd.delete(SNAPPY_PKG_NAME, SNAPPY_VERSION, SNAPPY_PLATFORM)

    def _list_packages(self):
        sd = SoftwareDepot(DIR_DEPOT)
        sd.list()

    if __name__ == "__main__":
            unittest.main()

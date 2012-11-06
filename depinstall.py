import os.path
import json
import shutil
import urllib2
import urlparse
import hashlib
import logger

from commons import CommonUtils, CommonConsts, ChecksumError, PermissionError, CyclicDependencyError

DEP_STATUS_KEY_INSTALLED = "installed"
DEP_STATUS_KEY_INQUEUE = "in-queue"


class PackageInstaller:
    def __init__(self, name, version, platform, install_dir, depot_location, dep_status={DEP_STATUS_KEY_INSTALLED: [],
                                                                                         DEP_STATUS_KEY_INQUEUE:[]}):
        self._log = logger.Logger.get_logger()
        self._name = name
        self._version = version
        self._platform = platform
        self._depot_location = depot_location
        self._install_dir = install_dir
        self._dep_status = dep_status
        self._installation_success = False
        self._setup()


    def install(self):
        try:
            self._log.info("Started installing package : {0}-{1} for OS : {2} ...".format(self._name, self._version, self._platform))
            self._update_dep_status()
            if self._is_already_installed:
                self._install_update()
            else:
                self._install_fresh()
            self._store_manifestfile()
            self._installation_success = True
            self._update_dep_status()
            self._log.info("Completed installing package : {0}-{1} for OS : {2} .".format(self._name, self._version, self._platform))
        finally:
            self._cleanup()

    def _update_dep_status(self):
        if not  self._installation_success:
            self._dep_status[DEP_STATUS_KEY_INQUEUE].append(self._manifest_filename)
        else:
            self._dep_status[DEP_STATUS_KEY_INQUEUE].remove(self._manifest_filename)
            self._dep_status[DEP_STATUS_KEY_INSTALLED].append(self._manifest_filename)

    def _setup(self):
        try:
            self._manifest_filename = CommonUtils.generate_manifest_filename(self._name, self._version, self._platform, "json")

            self._depot_manifestfile_location = os.path.join(self._depot_location, CommonConsts.SW_DEPOT_MANIFEST_FILE_DIR)
            self._depot_datafile_location = os.path.join(self._depot_location, CommonConsts.SW_DEPOT_DATAFILES_DIR,
                                                         CommonUtils.generate_package_name(self._name, self._version, self._platform))


            self._etc_dir = os.path.join(self._install_dir, "etc", "packages")
            if not os.path.exists(self._etc_dir):
                os.makedirs(self._etc_dir)
            self._pkg_install_dir = self._install_dir
            self._is_already_installed = self._is_already_installed()
            self._temp_dir = os.path.join(self._pkg_install_dir, os.path.splitext(self._manifest_filename)[0] + "-INSTALL-TEMP")
            os.mkdir(self._temp_dir)
            self._manifest = self._get_manifest_object()
        except Exception as e:
            self._cleanup()
            self._log.error(e)
            raise e

    def _cleanup(self):
        try:
            if os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
            ''' TODO: clean up by tracking the installed files
            if not self._is_already_installe    d and not self._installation_success:
                if os.path.exists(self._pkg_install_dir):
                    shutil.rmtree(self._pkg_install_dir)
            '''
        except Exception as e:
            print "Error during cleanup - ", e

    def  _is_already_installed(self):
        if os.path.exists(os.path.join(self._etc_dir, self._manifest_filename)):
            return True
        return False

    def _store_manifestfile(self):
        mf_temp_file = self._get_local_temp_manifest_filepath()
        shutil.copy(mf_temp_file, self._etc_dir)

    def _get_manifest_object(self):
        try:
            mf_path = self._get_local_manifest_file()
            with open(mf_path, "rb") as f:
                return json.load(f)
        except Exception as e:
            raise ValueError("Error while retrieving manifest file: {0} from Software Depot: {1}.Error is {2}".format(self._manifest_filename, self._depot_location, e))

    #TODO: Security (Authenticaton, etc) 
    def _get_local_manifest_file(self):
        manifest_depo_path = os.path.join(self._depot_manifestfile_location, self._manifest_filename)
        manifest_temp_path = self._get_local_temp_manifest_filepath()
        #urllib.urlretrieve(manifest_depo_path, manifest_temp_path)
        self._retrieve_file(manifest_depo_path, manifest_temp_path)
        return manifest_temp_path


    def _get_local_temp_manifest_filepath(self):
        return os.path.join(self._temp_dir, self._manifest_filename)

    def _install_fresh(self):
        if CommonConsts.MF_KEY_DEPENDS in self._manifest:
            self._process_dependencies(self._manifest[CommonConsts.MF_KEY_DEPENDS])
        if CommonConsts.MF_KEY_DIRS in self._manifest:
            self._process_directories(self._manifest[CommonConsts.MF_KEY_DIRS])
        if CommonConsts.MF_KEY_FILES in self._manifest:
            self._process_files(self._manifest[CommonConsts.MF_KEY_FILES])

    def _install_update(self):
        print "Updating.."
        if CommonConsts.MF_KEY_FILES in self._manifest:
            self._process_files(self._manifest[CommonConsts.MF_KEY_FILES])

    def _process_dependencies(self, deps):
        for dep in deps:
            self._install_dependency(dep)


    def _process_directories(self, dirs):
        for d in dirs:
            p = os.path.join(self._pkg_install_dir, d[CommonConsts.MF_KEY_FILES_ATTR_PATH])
            if not os.path.exists(p):
                os.makedirs(p, 0755)

    def _process_files(self, files):
        for f in files:
            destfile = os.path.join(self._pkg_install_dir, f[CommonConsts.MF_KEY_FILES_ATTR_PATH])
            if os.path.exists(destfile):
                self._update_file(f)
            else:
                self._install_file(f)

    def _install_dependency(self, dep):
        mfn = dep[CommonConsts.MF_KEY_DEPENDS_ATTR_MANIFEST]
        if not mfn:
            mfn = CommonUtils.generate_manifest_filename(dep[CommonConsts.MF_KEY_DEPENDS_ATTR_PACKAGE],
                                                         dep[CommonConsts.MF_KEY_DEPENDS_ATTR_VERSION],
                                                         dep[CommonConsts.MF_KEY_DEPENDS_ATTR_PLATFORM],
                                                         "json")
        if mfn in self._dep_status[DEP_STATUS_KEY_INSTALLED]:
            return
        elif mfn in self._dep_status[DEP_STATUS_KEY_INQUEUE]:
            raise CyclicDependencyError("FATAL: Cyclic dependency found in manifest : {0} for {1} while installing package: {2}".format(self._manifest_filename,
                                                                                                                                        mfn, self._name))
        pi = PackageInstaller(dep[CommonConsts.MF_KEY_DEPENDS_ATTR_PACKAGE],
                                                         dep[CommonConsts.MF_KEY_DEPENDS_ATTR_VERSION],
                                                         dep[CommonConsts.MF_KEY_DEPENDS_ATTR_PLATFORM],
                                                         self._install_dir, self._depot_location, self._dep_status)
        pi.install()

    def _update_file(self, f):
        try:
            self._verify_file(f)
        except ChecksumError, PermissionError:
            self._install_file(f)

    def _install_file(self, f):
        srcfile = self._get_source_file(f)
        destfile = self._get_destination_file(f)
        self._log.debug("Installing file... \n src: {0} \n dest: {1} ".format(srcfile, destfile))
        #urllib.urlretrieve(srcfile, destfile) 
        self._retrieve_file(srcfile, destfile) # TODO: need to optimize here (use pycurl)
        self._log.debug("File retrieved from depot: {0}".format(srcfile))
        os.chmod(destfile, int(f[CommonConsts.MF_KEY_FILES_ATTR_MODE], 8))
        if not self._verify_file(f):
            os._exit(os.EX_DATAERR)

    def _retrieve_file(self, srcfile, destfile):
        if not urlparse.urlparse(srcfile).scheme:
            srcfile = "file:" + srcfile
        response = urllib2.urlopen(srcfile)
        content = response.read()
        with open(destfile, "w") as f:
            f.write(content)


    """Check the sha1 of and installed file and verifies its permission"""
    def _verify_file(self, f):
        fullpath = self._get_destination_file(f)
        digest = hashlib.new("sha1")
        digest.update(open(fullpath, "rb").read())
        if digest.hexdigest() != f[CommonConsts.MF_KEY_FILES_ATTR_SHA1]:
            raise ChecksumError("FATAL: SHA1 doesn't match for installed file: {0}".format(fullpath))
        mode = CommonUtils.get_filepermission(fullpath)
        if mode != f[CommonConsts.MF_KEY_FILES_ATTR_MODE]:
            raise PermissionError("FATAL: Permission mode doesn't match for installed file: {0}".format(fullpath))
        return True


    def _get_source_file(self, f):
        return os.path.join(self._depot_datafile_location, f[CommonConsts.MF_KEY_FILES_ATTR_SHA1])

    def _get_destination_file(self, f):
        return os.path.join(self._pkg_install_dir, f[CommonConsts.MF_KEY_FILES_ATTR_PATH])







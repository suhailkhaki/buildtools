import os.path
import json
import shutil
import urllib
import hashlib

from commons import CommonUtils, CommonConsts, ChecksumError, PermissionError, CyclicDependencyError

DEP_STATUS_KEY_INSTALLED = "installed"
DEP_STATUS_KEY_INQUEUE = "in-queue"


class PackageInstaller:
    def __init__(self, name, version, platform, install_dir, depot_location, dep_status={DEP_STATUS_KEY_INSTALLED: [],
                                                                                         DEP_STATUS_KEY_INQUEUE:[]}):
        self._name = name
        self._version = version
        self._platform = platform
        self._depot_location = depot_location
        self._install_dir = install_dir
        self._dep_status = dep_status
        self._installation_success = False
        self._setup()

    @classmethod
    def get_instance_from_args(cls, args, dep_status={DEP_STATUS_KEY_INSTALLED: [],
                                                      DEP_STATUS_KEY_INQUEUE:[]}):
        return cls(args.package_name, args.version, args.platform, args.install_dir, args.depot_location, dep_status)

    @classmethod
    def get_instance_from_manifest_filename(cls, manifest_filename, install_dir, depot_location, dep_status={DEP_STATUS_KEY_INSTALLED: [],
                                                                                                             DEP_STATUS_KEY_INQUEUE:[]}):
        fn_wo_ext = os.path.splitext(manifest_filename)[0]
        arglist = fn_wo_ext.split("-")
        return cls(arglist[0], arglist[1], arglist[2], install_dir, depot_location, dep_status)

    def install(self):
        try:
            self._update_dep_status()
            if self._is_already_installed:
                self._verify_installation()
            else:
                self._install_fresh()
            self._installation_success = True
            self._update_dep_status()
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
                                                         CommonUtils.get_package_depo_name_from_manifest_file(self._manifest_filename))

            self._pkg_install_dir = os.path.join(self._install_dir, os.path.splitext(self._manifest_filename)[0])
            self._temp_dir = os.path.join(self._pkg_install_dir, os.path.splitext(self._manifest_filename)[0] + "-INSTALL-TEMP")
            self._is_already_installed = False
            if os.path.exists(self._pkg_install_dir):
                self._is_already_installed = True
            else:
                os.mkdir(self._pkg_install_dir)
            self._temp_dir = os.path.join(self._pkg_install_dir, os.path.splitext(self._manifest_filename)[0] + "-INSTALL-TEMP")
            os.mkdir(self._temp_dir)
            self._manifest = self._get_manifest_object()
        except Exception as e:
            self._cleanup()
            raise e

    def _cleanup(self):
        try:
            if os.path.exists(self._temp_dir):
                shutil.rmtree(self._temp_dir)
            if not self._is_already_installed and not self._installation_success:
                if os.path.exists(self._pkg_install_dir):
                    shutil.rmtree(self._pkg_install_dir)
        except Exception as e:
            print "Error during cleanup - ", e

    def _get_temp_dir(self, manifest_filename):
        return os.path.join(self._pkg_install_dir, os.path.splitext(manifest_filename)[0])

    def _get_manifest_object(self):
        mf_path = self._get_local_manifest_file_path()
        with open(mf_path, "rb") as f:
            return json.load(f)

    #TODO: Security (Authenticaton, etc) 
    def _get_local_manifest_file_path(self):
        manifest_depo_path = os.path.join(self._depot_manifestfile_location, self._manifest_filename)
        manifest_temp_path = os.path.join(self._temp_dir, self._manifest_filename)
        urllib.urlretrieve(manifest_depo_path, manifest_temp_path)
        return manifest_temp_path

    def _install_fresh(self):
        if 'depends' in self._manifest:
            self._process_dependencies(self._manifest["depends"])
        if 'dirs' in self._manifest:
            self._process_directories(self._manifest["dirs"])
        if 'files' in self._manifest:
            self._process_files(self._manifest["files"])

    def _verify_installation(self):
        print "verifying installation."
        if 'files' in self._manifest:
            self._process_files(self._manifest["files"])
        print "verification completed."

    #TODO: Cyclic dependency
    def _process_dependencies(self, deps):
        for dep in deps:
            self._install_dependency(dep)


    def _process_directories(self, dirs):
        for d in dirs:
            p = os.path.join(self._pkg_install_dir, d["path"])
            if not os.path.exists(p):
                os.makedirs(p, 0755)

    def _process_files(self, files):
        for f in files:
            destfile = os.path.join(self._pkg_install_dir, f["path"])
            if os.path.exists(destfile):
                self._verify_file(f)
            else:
                self._install_file(f)

    def _install_dependency(self, dep):
        mfn = dep["manifest"]
        if not mfn:
            mfn = CommonUtils.generate_manifest_filename(dep["package"], dep["version"], dep["platform"], "json")
        if mfn in self._dep_status[DEP_STATUS_KEY_INSTALLED]:
            return
        elif mfn in self._dep_status[DEP_STATUS_KEY_INQUEUE]:
            raise CyclicDependencyError("FATAL: Cyclic dependency found in manifest : {0} for {1} while installing package: {2}".format(self._manifest_filename,
                                                                                                                                        mfn, self._name))
        pi = PackageInstaller.get_instance_from_manifest_filename(mfn, self._install_dir, self._depot_location, self._dep_status)
        pi.install()

    """Check the sha1 of and installed file and verifies its permission"""
    def _verify_file(self, f):
        fullpath = os.path.join(self._pkg_install_dir, f["path"])
        digest = hashlib.new("sha1")
        digest.update(open(fullpath, "rb").read())
        if digest.hexdigest() != f["sha1"]:
            raise ChecksumError("FATAL: SHA1 doesn't match for installed file: {0}".format(fullpath))
        mode = CommonUtils.get_filepermission(fullpath)
        if mode != f["mode"]:
            raise PermissionError("FATAL: SHA1 doesn't match for installed file: {0}".format(fullpath))
        return True

    def _install_file(self, f):
        srcfile = os.path.join(self._depot_datafile_location, f["sha1"])
        destfile = os.path.join(self._pkg_install_dir, f["path"])
        urllib.urlretrieve(srcfile, destfile)
        os.chmod(destfile, int(f["mode"], 8))
        if not self._verify_file(f):
            os._exit(os.EX_DATAERR)






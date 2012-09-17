import os
import hashlib
import shutil
import json

from commons import CommonConsts, CommonUtils, ChecksumError, PermissionError, PackageExistsError

class SoftwareDepot:
    def __init__(self, depot_location):
        self._location = depot_location
        self._depot_df_path = os.path.join(depot_location, CommonConsts.SW_DEPOT_DATAFILES_DIR)
        self._depot_mf_path = os.path.join(depot_location, CommonConsts.SW_DEPOT_MANIFEST_FILE_DIR)
        #self._depot_temp_path = os.path.join()


    def list(self):
        return set(os.listdir(self._depot_mf_path))


    #TODO:
    # Create a directory structure on depot too to avoid a conflict if a same files is present in different dirs ??

    def add(self, package, version, platform, staging_dir, manifest_filepath):
        try:
            manifest_filename = CommonUtils.generate_manifest_filename(package, version, platform, "json")
            if os.path.exists(os.path.join(self._depot_mf_path, manifest_filename)):
                raise PackageExistsError("Package manifest file already exists in depot. Package name : {0}, manifest file: {1}.\n\
                                             Either uninstall the package first or use update command to install the package.".format(CommonUtils.get_package_depo_name_from_manifest_file(manifest_filename),
                                                                                                                                      manifest_filename))
            input_manifest_file = os.path.join(manifest_filepath, manifest_filename)
            self._deploy_package(input_manifest_file, staging_dir)
        except Exception as e:
            self._cleanup(manifest_filename)
            raise e

    def update(self, package, version, platform, staging_dir, manifest_filepath):
        try:
            manifest_filename = CommonUtils.generate_manifest_filename(package, version, platform, "json")
            input_manifest_file = os.path.join(manifest_filepath, manifest_filename)
            self._deploy_package(input_manifest_file, staging_dir)

        except Exception as e:
            self._cleanup(manifest_filename)
            raise e

    def delete(self, package, version, platform,):
        manifest_filename = CommonUtils.generate_manifest_filename(package, version, platform, "json")
        self._cleanup(manifest_filename)



    def _deploy_package(self, manifest_file, staging_dir):
        depot_package_name = CommonUtils.get_package_depo_name_from_manifest_file(os.path.split(manifest_file)[1])
        depot_pkg_dest_path = os.path.join(self._depot_df_path, depot_package_name)
        if not os.path.exists(depot_pkg_dest_path):
                os.makedirs(depot_pkg_dest_path)
        with open(manifest_file, "rb") as f:
            manifest = json.load(f)
            dirs_m = manifest[CommonConsts.MF_KEY_DIRS]
            files_m = manifest[CommonConsts.MF_KEY_FILES]
            for file_ in files_m:
                fullpath = os.path.join(staging_dir, file_[CommonConsts.MF_KEY_FILES_ATTR_PATH])
                contents = open(fullpath, 'rb').read()
                sha1 = hashlib.sha1(contents).hexdigest()
                if sha1 != file_[CommonConsts.MF_KEY_FILES_ATTR_SHA1]:
                    raise ChecksumError("FATAL: File modified in staging area before installation: {0}".format(file_[CommonConsts.MF_KEY_FILES_ATTR_PATH]))
                mode = CommonUtils.get_filepermission(fullpath)
                if mode != file_["mode"]:
                    raise PermissionError("FATAL: SHA1 doesn't match for installed file: {0}".format(fullpath))
                dest_file = os.path.join(depot_pkg_dest_path, sha1)
                shutil.copy(fullpath, dest_file)
        shutil.copy(manifest_file, self._depot_mf_path)


    def _cleanup(self, manifest_filename):
        try:
            depot_mf = os.path.join(self._depot_mf_path, manifest_filename)
            if os.path.exists(depot_mf):
                os.remove(depot_mf)
            depot_pkg = CommonUtils.get_package_depo_name_from_manifest_file(manifest_filename)
            depot_df = os.path.join(self._location, CommonConsts.SW_DEPOT_DATAFILES_DIR , depot_pkg)
            if os.path.exists(depot_df):
                shutil.rmtree(depot_df)
        except Exception as e:
            print "Exception while cleanup: ", e




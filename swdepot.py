import os
import hashlib
import shutil
import json

from commons import CommonConsts, CommonUtils, ChecksumError, PermissionError

class SoftwareDepot:
    def __init__(self, depot_location):
        self._location = depot_location

    @classmethod
    def get_instance_from_args(cls, args):
        return cls(args.depot_location)

    def add_by_args(self, args):
        self.add(args.manifest_file, args.staging_dir)

    #TODO:
    # Exception - e.g IO -> for already existing package, etc.
    # Create a directory structure on depot too to avoid a conflict if a same files is present in different dirs ??
    def add(self, manifest_file, staging_dir):
        try:
            depot_package_name = CommonUtils.get_package_depo_name_from_manifest_file(manifest_file)
            dest_path = os.path.join(self._location, CommonConsts.SW_DEPOT_DATAFILES_DIR , depot_package_name)
            os.makedirs(dest_path)
            with open(manifest_file, "rb") as f:
                manifest = json.load(f)
                dirs_m = manifest["dirs"]
                files_m = manifest["files"]
                for file_ in files_m:
                    fullpath = os.path.join(staging_dir, file_["path"])
                    contents = open(fullpath, 'rb').read()
                    sha1 = hashlib.sha1(contents).hexdigest()
                    if sha1 != file_["sha1"]:
                        raise ChecksumError("FATAL: File modified in staging area before installation: {0}".format(file_["path"]))
                    mode = CommonUtils.get_filepermission(fullpath)
                    if mode != file_["mode"]:
                        raise PermissionError("FATAL: SHA1 doesn't match for installed file: {0}".format(fullpath))
                    dest_file = os.path.join(dest_path, sha1)
                    shutil.copy(fullpath, dest_file)
            manifest_dest_path = os.path.join(self._location, CommonConsts.SW_DEPOT_MANIFEST_FILE_DIR)
            shutil.copy(manifest_file, manifest_dest_path)
        except Exception as e:
            self._cleanup(dest_path)
            raise e

    def _cleanup(self, dest_path):
        try:
            shutil.rmtree(dest_path)
        except Exception as e:
            print "Exception while cleanup: ", e




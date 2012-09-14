import os.path
import stat

class CommonUtils:

    @staticmethod
    def generate_manifest_filename(package_name, version, platform, file_ext):
        return package_name + "-" + version + "-" + platform + "." + file_ext

    @staticmethod
    def get_package_depo_name_from_manifest_file(manifest_file):
        return os.path.splitext(os.path.basename(manifest_file))[0]

    # Based on # https://stomp.colorado.edu/blog/blog/2010/10/22/on-python-stat-octal-and-file-system-permissions/ (2012-06-25)
    @staticmethod
    def get_filepermission(path):
        """Returns the permission of a file."""
        return oct(stat.S_IMODE(os.stat(path).st_mode))

class CommonConsts:
    SW_DEPOT_MANIFEST_FILE_DIR = "manifestfiles"
    SW_DEPOT_DATAFILES_DIR = "datafiles"

''' Exceptions '''
class ChecksumError(Exception):
    pass

class PermissionError(Exception):
    pass

class CyclicDependencyError(Exception):
    pass

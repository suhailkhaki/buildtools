
import os
import hashlib
import stat
import json
from commons import CommonUtils

class ManifestGenerator:
    def __init__(self, package_name, version, platform, stage_dir, _target_file_path):
        self._package_name = package_name
        self._version = version
        self._platform = platform
        self._staging_dir = stage_dir
        self._target_file_path = _target_file_path

    @classmethod
    def instance_from_args(cls, args):
        return cls(args.package_name, args.version, args.platform, args.stage_dir, args.target_file_path)

    def generate_manifest(self):
        manifest = {'build':[], 'depends':[], 'dirs':[], 'files': []}

        for dirpath, dirnames, files in os.walk(self._staging_dir):
            dir_rel_path = os.path.relpath(dirpath, self._staging_dir)
            if dir_rel_path != ".":
                manifest['dirs'].append({'path':dir_rel_path})
            for file_ in files:
                fullpath = os.path.join(dirpath, file_)
                sha1 = HashGenerator(fullpath).generate_hash()
                filename = os.path.relpath(fullpath, self._staging_dir)
                mode = CommonUtils.get_filepermission(fullpath)
                manifest['files'].append({'path': filename, 'sha1': sha1,
                                      'mode': mode})

        if self._target_file_path is None:
            return json.dumps(manifest)
        self._write_to_file(manifest)


    def _write_to_file(self, manifest):
        with open(os.path.join(self._target_file_path, self._generate_file_name()), "w") as f:
            f.write(json.dumps(manifest))

    def _generate_file_name(self):
        return CommonUtils.generate_manifest_filename(self._package_name, self._version, self._platform, "json")


class HashGenerator:

    def __init__(self, abs_file_name):
        self._abs_file_name = abs_file_name

    @classmethod
    def instance_from_args(cls, args):
        return cls(args.abs_file_name)

    def generate_hash(self, algo="sha1"):
        contents = open(self._abs_file_name, 'rb').read()
        if algo == "sha1":
            return hashlib.sha1(contents).hexdigest()
        else:
            raise ValueError("Not Supported algo")





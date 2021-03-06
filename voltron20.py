import sys
import argparse
from manifestutils import ManifestGenerator
import swdepot
import depinstall
from depinstall import PackageInstaller

def _define_arguments():
    parser = argparse.ArgumentParser(prog="voltron20", description='Build Software.')
    sub_parsers = parser.add_subparsers(dest="subparser_name")

    parser_manifest = sub_parsers.add_parser("manifest", help="Utility for manifest file.")
    parser_depot = sub_parsers.add_parser("depot", help="Software depot management.")
    parser_install = sub_parsers.add_parser("install", help="Package Installer.")

    _define_parser_manifest(parser_manifest)
    _define_parser_depot(parser_depot)
    _define_parser_install(parser_install)

    return parser.parse_args()



def _define_parser_manifest(parser):
    sub_parsers = parser.add_subparsers(dest="subparser_name")

    parser_genfile = sub_parsers.add_parser("genfile", help="Generate manifest file.")
    parser_genfile.add_argument("--package_name", "-pkg", dest="package_name", required=True, help="Name of the package.")
    parser_genfile.add_argument("--version", "-ver", dest="version", required=True, help="Package version.")
    parser_genfile.add_argument("--platform", "-p", dest="platform", required=True, help="Target platform.")
    parser_genfile.add_argument("--stage_dir", "-sd", dest="stage_dir", required=True, help="Staging directory.")
    parser_genfile.add_argument("--target_file_path", "-tfp", dest="target_file_path", help="Target file path.")
    parser_genfile.set_defaults(func=_handle_manifest_genfile)


    parser_gensha1 = sub_parsers.add_parser("gensha1", help="Generate sha1 string for given file.")
    parser_gensha1.add_argument("file_path", help="Provide the file path.")

def _define_parser_depot(parser):
    parser.add_argument("-location", "-l", dest="depot_location", help="Location of software depot.")
    sub_parsers = parser.add_subparsers(dest="subparser_name")

    parser_list = sub_parsers.add_parser("list", help="Lists all the packages in the software depot.")
    parser_list.set_defaults(func=_handle_depot_list)

    parser_add = sub_parsers.add_parser("add", help="Adds a package to software depot.")
    parser_add.add_argument("--package_name", "-pkg", dest="package_name", required=True, help="Name of the package.")
    parser_add.add_argument("--version", "-ver", dest="version", required=True, help="Package version.")
    parser_add.add_argument("--platform", "-p", dest="platform", required=True, help="Target platform.")
    parser_add.add_argument("--stage_dir", "-sd", dest="staging_dir", required=True, help="Staging directory with absolute path.")
    parser_add.add_argument("--manifest_dirpath", "-md", dest="manifest_dir", required=True, help="Absolute path of manifest directory.")
    parser_add.set_defaults(func=_handle_depot_add)

    parser_update = sub_parsers.add_parser("update", help="Updates a package in software depot.")
    parser_update.add_argument("--package_name", "-pkg", dest="package_name", required=True, help="Name of the package.")
    parser_update.add_argument("--version", "-ver", dest="version", required=True, help="Package version.")
    parser_update.add_argument("--platform", "-p", dest="platform", required=True, help="Target platform.")
    parser_update.add_argument("--stage_dir", "-sd", dest="staging_dir", required=True, help="Staging directory with absolute path.")
    parser_update.add_argument("--manifest_dir", "-md", dest="manifest_dir", required=True, help="Absolute path of manifest directory.")
    parser_update.set_defaults(func=_handle_depot_update)

    parser_del = sub_parsers.add_parser("delete", help="Deletes a package in software depot.")
    parser_del.add_argument("--package_name", "-pkg", dest="package_name", required=True, help="Name of the package.")
    parser_del.add_argument("--version", "-ver", dest="version", required=True, help="Package version.")
    parser_del.add_argument("--platform", "-p", dest="platform", required=True, help="Target platform.")
    parser_del.set_defaults(func=_handle_depot_delete)

def _define_parser_install(parser):
    parser.add_argument("--package_name", "-pkg", dest="package_name", required=True, help="Name of the package.")
    parser.add_argument("--version", "-ver", dest="version", required=True, help="Package version.")
    parser.add_argument("--platform", "-p", dest="platform", required=True, help="Target platform.")
    parser.add_argument("--install_dir", "-d", dest="install_dir", required=True, help="Root installation directory path")
    parser.add_argument("--depot_location", "-depol", dest="depot_location", required=True, help="Location of software depot.")
    parser.set_defaults(func=_handle_install)
    '''
    sub_parsers = parser.add_subparsers(dest="subparser_name")

    parser_verify = sub_parsers.add_parser("verify", help="Verify the package.")
    parser_verify.add_argument("name", help="Package name.")
    parser_verify.add_argument("staging_dir_path", help="Staging direcverify_before_installtory path.")
    '''

def _handle_manifest_genfile(args):
    mangen = ManifestGenerator(args.package_name, args.version, args.platform, args.stage_dir, args.target_file_path)
    mangen.generate_manifest()
    print "Manifest generated."

def _handle_depot_list(args):
    depot = swdepot.SoftwareDepot(args.depot_location)
    depot.list()

def _handle_depot_add(args):
    depot = swdepot.SoftwareDepot(args.depot_location)
    depot.add(args.package_name, args.version, args.platform, args.staging_dir, args.manifest_dir)
    print "Package added."

def _handle_depot_update(args):
    depot = swdepot.SoftwareDepot(args.depot_location)
    depot.update(args.package_name, args.version, args.platform, args.staging_dir, args.manifest_dir)
    print "Package updated."

def _handle_depot_delete(args):
    depot = swdepot.SoftwareDepot(args.depot_location)
    depot.delete(args.package_name, args.version, args.platform)
    print "Package deleted."

def _handle_install(args):
    PackageInstaller(args.package_name, args.version, args.platform, args.install_dir, args.depot_location).install()
    print "Installation completed."

def main():
    argv = _define_arguments()
    argv.func(argv)

if __name__ == "__main__":
    sys.exit(main())

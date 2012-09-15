Preamble
--------

Please see http://hub.internal.couchbase.com/confluence/display/cbeng/Building+Couchbase+Server+2.x

Overview
---------
Voltron20 is a utility to build a software from its binaries. It manages a software depot (repository) that stores all the dependancies required to build a software. 
Voltron20 workflow has three stages

1. Staging : The dependency package is installed manually in a staging area following the standard installations steps defined for that package installation. Initial manifest file can also be generated by using manifest utility provided by voltron20.

2. Deployment : Based on the manifest file, the package is deployed in the software depot.

3. Installation: Package is installed as per configuration provided in manifest file for that given package. Any dependency defined in the manifest file is installed recursively.


Example 1 - Snappy
------------------
In this example, 
* Staging -> Step 1,2 and 3
* Deployment -> Step 4
* Installation -> Step 5

1. Download Snappy and extract it:
	`http://snappy.googlecode.com/files/snappy-1.0.5.tar.gz`

2. Compile Snappy:
  `./configure --prefix=/opt/couchbase`
  `gmake install DESTDIR=/tmp/snappy`

3. Generate manifest fil`
  `python voltron20.py manifest genfile --package_name="snappy" -ver="1.0.5" -p="ubuntu-12.04" -stgdir="/tmp/snappy/opt/couchbase" tfp="/home/suhail/workspace/temp/manifest-files"`

4. Deploy the binaries to our software depot
  `python voltron20.py depot -l="/cbdepot" add -sd="/tmp/snappy/opt/couchbase" -mf="/home/suhail/workspace/temp/manifest-files/snappy-1.0.5-ubuntu-12.04.json"`

5. Install it to the directory named install
  `install --package_name="snappy" -ver="1.0.5" -p="ubuntu-12.04" -d="/home/suhail/cbinstall" -depol="/cbdepot"`

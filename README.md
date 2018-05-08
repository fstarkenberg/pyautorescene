pyautorescene
=============
pyautorescene automates the process of returning un-rarred scene releases back into their former glory.  It makes use of [PyReScene](https://bitbucket.org/Gfy/pyrescene) and [srrDB](http://srrdb.com) to make the whole process has hands off as possible.

Requirements
------------
The main requirement is that you have already installed PyReScene from source as per the [instructions](https://bitbucket.org/Gfy/pyrescene).  This tool does not work with the pre-compiled .exes.

Installation
------------
1. Clone this repository to your local machine
2. Via terminal/command prompt navigate to the folder
3. Run `python setup.py install`

Usage
-----
Currently, the best and most tested method of executing this script is `autorescene.py -va --find-sample -o /path/to/output /path/to/input`

It is **seriously** recommended to output to a completely separate folder that you're happy to delete. 

<pre>
stick$ autorescene.py --help
usage: autorescene.py [--opts] input1 [input2] ...

automated rescening of unrarred/renamed scene files

positional arguments:
  input                 file or directory of files to be parsed

optional arguments:
  -h, --help            show this help message and exit
  -a, --auto-reconstruct
                        full auto rescene - this will scan directories, locate
                        files, check srrdb, and a release into a release dir
                        with original rars and nfo/sfv/etc and sample, if srs
                        exists - this is the same as -jkx
  -j, --rescene         recreate rars from extracted file/srr
  -k, --resample        recreate sample from original file/srs
  --find-sample         if sample creation fails, look for sample file on disk
  -o OUTPUT, --output OUTPUT
                        set the directory for all output
  -v, --verbose         verbose output for debugging purposes
  --rename              rename scene releases to their original scene
                        filenames
  -x, --extract-stored  extract stored files from srr (nfo, sfv, etc)
  -e EXTENSION, --extension EXTENSION
                        list of extensions to check against srrdb (default:
                        .mkv, .avi, .mp4)
  --keep-srr            keep srr in output directory
  --keep-srs            keep srs in output directory
</pre>


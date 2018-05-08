#!/usr/bin/python

from __future__ import print_function
import argparse, os, sys, errno
from colorama import Fore, init
import shutil
import zlib

from utils.srrdb import *
from utils.srr import SRR
from utils.srs import SRS

SUCCESS = Fore.GREEN + "  [SUCCESS] " + Fore.RESET
FAIL = Fore.RED + "  [FAIL] " + Fore.RESET

#list of processes releases
release_list = dict()
missing_files = []

def arg_parse():
    parser = argparse.ArgumentParser(
        description='automated rescening of unrarred/renamed scene files',
        usage=os.path.basename(sys.argv[0]) + ' [--opts] input1 [input2] ...')

    parser.add_argument('input', nargs='*',
                        help='file or directory of files to be parsed', default='')
    parser.add_argument('-a', '--auto-reconstruct', action='store_true',
                        dest="auto_reconstruct",
                        help='full auto rescene - this will scan directories, locate files, '
                        'check srrdb, and a release into a release dir with original rars and '
                        'nfo/sfv/etc and sample, if srs exists - this is the same as -jkx')
    parser.add_argument('-j', '--rescene', action='store_true',
                        help='recreate rars from extracted file/srr')
    parser.add_argument('-k', '--resample', action='store_true',
                        help='recreate sample from original file/srs')
    parser.add_argument('--find-sample', action='store_true',
                        help='if sample creation fails, look for sample file on disk')
    parser.add_argument('--find-subs', action='store_true',
                        help='look for sub rar if file is missing')
    parser.add_argument('-o', '--output', help='set the directory for all output')
    parser.add_argument('-v', '--verbose', action='store_true',
                        help='verbose output for debugging purposes')
    parser.add_argument('--rename', action='store_true',
                        help='rename scene releases to their original scene filenames')
    parser.add_argument('-x', '--extract-stored', action='store_true',
                        help='extract stored files from srr (nfo, sfv, etc)')
    parser.add_argument('-e', '--extension', action='append', default=[],
                        help='list of extensions to check against srrdb '
                        '(default: .mkv, .avi, .mp4)')
    parser.add_argument('-m', '--min-filesize', help='set a minimum filesize in MB of a file to '
                        'check')
    parser.add_argument('--keep-srr', action='store_true',
                        help='keep srr in output directory')
    parser.add_argument('--keep-srs', action='store_true',
                        help='keep srs in output directory')

    args = parser.parse_args()

    return vars(args)

def calc_crc(fpath):
    if not os.path.isfile(fpath):
        return None

    prev = 0
    for line in open(fpath, "rb"):
        prev = zlib.crc32(line, prev)

    return "%08X"%(prev & 0xFFFFFFFF)

def copy_file(finput, foutput):
    if not os.path.isfile(finput):
        raise ValueError("finput must be a file")
    if not os.path.isdir(foutput):
        raise ValueError("foutput must be a file")
    if not os.path.splitext(finput)[1][0] != ".":
        return None
    try:
        shutil.copy2(finput, foutput)
    except IOError as e:
        return (None, "Unable to rename file: " + e)

    return True

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST and os.path.isdir(path):
            return True
        else:
            raise OSError(e)
    else:
        return True

def find_file(startdir, fname, fcrc):
    if not os.path.isdir(startdir):
        raise ValueError("startdir must be a directory")

    for root, dirs, files in os.walk(startdir):
        if fname in files:
            if calc_crc(os.path.join(root, fname)) == fcrc.zfill(8):
                #sample found!
                return os.path.join(root, fname)

    return False

def search_srrdb_crc(crc):
    #search srrdb for releases matching crc32
    verbose("\t - Searching srrdb.com for matching CRC", end="")
    try:
        results = search_by_crc(crc)
    except Exception as e:
        verbose("%s -> %s" % (FAIL, e))
        return False

    if not results:
        verbose("%s -> %s" % (FAIL, "No matching results"))
        return False
    else:
        verbose("%s" % SUCCESS)

    #handle multiple releases having same crc32 
    # (this should only happen with dupe srr's being uploaded)
    if len(results) > 1:
        #we need to work out which rls to use
        #check filename/size/etc
        verbose("\t\t %s More than one release found matching CRC %s. This is most likely an issue, please report it on IRC (#srrdb @ irc.efnet.net)." % (FAIL, crc))
        return False

    release = results[0]
    verbose("\t\t - Matched release: %s" % release['release'])

    return release

def check_file(args, fpath):
    if not os.path.splitext(fpath)[1] in args['extension']:
        return False
    if args['min_filesize'] and os.path.getsize(fpath) < args['min_filesize']:
        return False

    if args['output']:
        doutput = args['output']
    else:
        doutput = os.path.dirname(fpath)

    verbose("* Found potential file: " + os.path.basename(fpath))

    #calculate crc32 of file
    verbose("\t - Calculating crc for file: %s" % fpath, end="")

    release_crc = calc_crc(fpath)
    if not release_crc:
        verbose("%s" % (FAIL))
        return False
    else:
        verbose("%s -> %s" % (SUCCESS, release_crc))

    release = search_srrdb_crc(release_crc)
    if not release:
        return False
    else:
        #keep track of the releases we are processing
        if not release['release'] in release_list:
            release_list[release['release']] = dict()
            release_list[release['release']]['rescene'] = False
            release_list[release['release']]['resample'] = False
            release_list[release['release']]['extract'] = False
        elif release_list[release['release']]['rescene'] and release_list[release['release']]['resample']:
            verbose("\t - Skipping, already processed.")
            return True

    verbose("\t - Downloading SRR from srrdb.com", end="")
    # download srr
    try:
        srr_path = download_srr(release['release'])
    except Exception as e:
        verbose("%s -> %s" % (FAIL, e))
        return False
    else:
        verbose("%s" % SUCCESS)

    release_srr = SRR(srr_path)
    srr_finfo = release_srr.get_archived_fname_by_crc(release_crc)

    if os.path.basename(doutput.lower()).lower() != release['release'].lower():
        #output dir is not specific to rls/doesnt match release
        doutput = os.path.join(doutput, release['release'])
        if not os.path.isdir(doutput):
            verbose("\t - Creating output directory: %s" % (doutput), end="")
            try:
                mkdir(doutput)
            except Exception as e:
                verbose("%s -> Unable to create directory: %s" % (FAIL, e))
                return False
            else:
                verbose("%s" % (SUCCESS))

    verbose("\t - Setting output directory to: %s" % doutput)

    #rename file
    if args['rename']:
        if len(srr_finfo) != 1:
            return False

        if srr_finfo[0].file_name != os.path.basename(fpath):
            verbose("\t\t - file has been renamed, renaming to: %s" % srr_finfo[0].file_name, end="")
            (ret, mesg) = copy_file(fpath, os.path.join(doutput, srr_finfo[0].file_name))

            if not ret:
                verbose("%s -> %s", (FAIL, mesg))
            else:
                verbose("%s" % (SUCCESS))

    if (args['extract_stored'] or args['auto_reconstruct']) and not release_list[release['release']]['extract']:
        verbose("\t - Extracting stored files from SRR", end="")
        try:
            matches = release_srr.extract_stored_files_regex(doutput)

        except Exception as e:
            verbose("%s -> %s" % (FAIL, e))
            return False

        else:
            verbose("%s" % SUCCESS)

            for match in matches:
                if match[0].endswith(".srs"):
                    srs_path = match[0]

                verbose("\t\t - %s" % os.path.relpath(match[0], doutput))
            release_list[release['release']]['extract'] = True

    if (args['rescene'] or args['auto_reconstruct']) and not release_list[release['release']]['rescene']:
        verbose("\t - Reconstructing original RARs from SRR", end="")

        rename_hints = {srr_finfo[0].file_name: os.path.basename(fpath)}
        try:
            release_srr.reconstruct_rars(os.path.dirname(fpath), doutput, rename_hints)
        except Exception as e:
            verbose("%s -> %s" % (FAIL, e))

        else:
            verbose("%s" % (SUCCESS))
            release_list[release['release']]['rescene'] = True


    if (args['resample'] or args['auto_reconstruct']) and not release_list[release['release']]['resample']:
        if release['hasSRS'] == "yes":
            try:
                srs_path
            except NameError:
                srs_path = ""

                verbose("\t\t - Extracting SRS from SRR file for Sample reconstruction", end="")
                release_srs = release_srr.get_srs(doutput)

                if len(release_srs) != 1:
                    verbose("%s -> more than one SRS in this SRR.  Please reconstruct manually." % FAIL)
                else:
                    srs_path = release_srs[0][0]

            if srs_path != "":
                sample = SRS(srs_path)
                verbose("\t - Recreating Sample .. expect output from SRS\n-------------------------------")

                try:
                    sample.recreate(fpath, os.path.dirname(srs_path))
                except Exception as e:
                    verbose("-------------------------------")
                    verbose("\t - %s -> failed to recreate sample: %s." % (FAIL,e))

                    #sample reconstruction failed.. should we try check local disk for a sample?
                    if args['find_sample']:
                        verbose("\t - Searching for sample on local disk")
                        sample_file = find_file(os.path.dirname(fpath), sample.get_filename(), sample.get_crc())
                        if sample_file:
                            verbose("\t\t - %s - Found sample -> %s" % (SUCCESS, sample_file))
                            try:
                                print(sample_file)
                                print(os.path.dirname(srs_path))
                                copy_file(sample_file, os.path.dirname(srs_path))
                                release_list[release['release']]['resample'] = True
                            except Exception as e:
                                verbose("\t\t - %s - Could not copy file to %s -> %s" % (FAIL, os.path.dirname(srs_path), e))
                                missing_files.append(release['release']+"/Sample/"+sample.get_filename())
                        else:
                            missing_files.append(release['release']+"/Sample/"+sample.get_filename())
                    else:
                        missing_files.append(release['release']+"/Sample/"+sample.get_filename())
                else:
                    verbose("-------------------------------")
                    verbose("\t - %s -> sample recreated successfully" % (SUCCESS))
                    release_list[release['release']]['resample'] = True
            else:
                missing_files.append(release['release']+"/Sample/"+sample.get_filename())

        else:
            verbose("\t - No SRS found for sample recreation %s" % (FAIL))

        if args['find_subs']:
            print("finding subs")

if __name__ == "__main__":
    args = arg_parse()
    # initialize pretty colours
    init()

    #define verbose
    verbose = print if args['verbose'] else lambda *a, **k: None

    if not args['extension']:
        args['extension'] = ['.mkv', '.avi', '.mp4']
    if args['min_filesize']:
        #convert from MB to Bytes
        args['min_filesize'] = int(args['min_filesize']) * 1048576

    if args['output']:
        if not os.path.isdir(args['output']):
            sys.exit("output option needs to be a valid directory")
        verbose("Setting output directory to: " + args['output'] + "\n")

    cwd = os.getcwd()
    for path in args['input']:
        if os.path.isfile(path):
            check_file(args, path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for sfile in files:
                    check_file(args, os.path.join(root, sfile))

    if len(missing_files) > 0:
        print("Rescene process complete, the following files need to be manually aquired:")
        print(*missing_files, sep='\n')

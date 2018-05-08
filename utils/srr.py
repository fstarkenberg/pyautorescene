import os,re,subprocess
import re
from rescene import info, extract_files, reconstruct

class SRR:
    def __init__(self, filename, binary=None):
        if not os.path.isfile(filename):
            raise AttributeError("srr must be a file")

        if not filename.endswith(".srr"):
            raise AttributeError("srr file must have the .srr extension")

        self.filename = filename
        if binary is None:
            if os.name == 'posix':
                self.binary = '/usr/bin/srr'
            elif os.name == 'nt':
                self.binary = 'srr'
            else:
                self.binary = binary

    # search an srr for all archived-files that match given crc
    # returns array of FileInfo's matching the crc
    def get_archived_fname_by_crc(self, crc):
        matches = []

        for _, value in info(self.filename)['archived_files'].items():
            if crc == value.crc32.zfill(8):
                matches.append(value)

        return matches

    # search an srr for all archived-files that much a given filename
    # returns an array of FileInfo's matching the fname
    def get_archived_crc_by_fname(self, fname):
        matches = []

        for key, value in info(self.filename)['archived_files'].items():
            if fname == key:
                matches.append(value)

        return matches

    def get_srs(self, path):
        if not os.path.isdir(path):
            raise AttributeError("path must be a valid directory")

        matches = []
        for sfile in info(self.filename)['stored_files'].keys():
            if sfile.endswith(".srs"):
                result = extract_files(self.filename, path,
                                       extract_paths=True, packed_name=sfile)
                matches += result

        return matches

    def extract_stored_files_regex(self, path, regex=".*"):
        if not os.path.isdir(path):
            raise AttributeError("path must be a valid directory")

        matches = []

        for key in info(self.filename)["stored_files"].keys():
            if re.search(regex, key):
                result = extract_files(self.filename, path,
                                       extract_paths=True, packed_name=key)
                matches += result

        return matches

    def reconstruct_rars(self, dinput, doutput, hints):
        if not os.path.isdir(dinput):
            raise AttributeError("input folder must be a valid directory.")
        if not os.path.isdir(doutput):
            raise AttributeError("output folder must be a valid directory")

        try:
            res = reconstruct(self.filename, dinput, doutput, hints=hints,
                              auto_locate_renamed=True, extract_files=False)

            if res == -1:
                raise ValueError("One or more of the original files already exist in " + doutput)
        except:
            raise

        return True

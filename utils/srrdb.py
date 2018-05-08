import json
import tempfile
import os
import requests

srrdb_api 	= "http://www.srrdb.com/api/search/"
srrdb_download 	= "http://www.srrdb.com/download/srr/"
srrdb_details 	= "http://www.srrdb.com/release/details/"

def search_by_crc(crc):
    if len(crc) != 8:
        #crc must have 8 characters
        raise ValueError("CRC must have length of 8")

    crc_search = srrdb_api + "archive-crc:" + crc

    try:
        response = requests.get(crc_search)
        data = response.json()
    except:
        raise

    if 'resultsCount' not in data or int(data['resultsCount']) < 1:
        return None

    return data['results']


def download_srr(rls, path=None):
    if not rls or rls == "":
        raise ValueError("Release must have a valid name")

    srr_download = srrdb_download + rls

    if not path or path == "":
        path = tempfile.gettempdir()

    if not os.path.isdir(path):
        raise IOError("Output directory \"", path, "\" does not exist.")

    #create path for file to be stored
    path = os.path.join(path, os.path.basename(srr_download + ".srr"))

    try:
        response = requests.get(srr_download)

        if response.content == "The requested file does not exist.":
            return (False, "Release does not exist on srrdb.com")

        if response.content == "You've reached the daily limit.":
            return (False, "You've reached the daily SRR download limit.")

        with open(path, "wb") as local_file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    local_file.write(chunk)
                    local_file.flush()
    except:
        raise

    return path

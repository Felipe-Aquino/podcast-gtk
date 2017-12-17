from urllib import request
import shutil

USER_AGENT = 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'

def file_request(url, file_name):
    req = request.Request(url, data=None, headers={ 'User-Agent': USER_AGENT})

    with request.urlopen(req) as response, open(file_name, 'wb') as out_file:
        shutil.copyfileobj(response, out_file)
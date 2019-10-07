"""
This module is not meant to be imported, but used to write a proper "file system functionality extension".

File system functionality extension

(Key-value) stores offer a dict-like interface to many different storage systems because these can all be seen through
the key-value lenses (often in more than one natural way) and because there is a natural way to intepret the basic
operations of getting, setting, deleting, listing and counting items.

But as we move upward from the root functionality, we'll start to discover elements and operations that only make sense
for a group of systems, but not another.

Let's take file systems for example: Applicable to local file systems, remote server files (through ssh or ftp),
AWS s3, dropbox, google drive, etc. These all have a distinction between folders and files, concepts like file size and
extension, and have operations that are natural for the hierarchical organization of files into folders:
isdir, isfile, mkdir, (path) join, listdir, getsize, copyfile, etc.

We'd like to implement our unified approach here too, so that one can enhance stores with file system persisters,
in a consistent and therefore DRY-COC-SOC manner.

"""

from warnings import warn

raise ImportError('This module is not meant to be imported, but used to write a proper '
                  '"file system functionality extension".')

import abc
import os
import re
from glob import iglob, glob
from shutil import copyfile

from s3fs import S3FileSystem

DFLT_S3_HOST = 'https://s3.amazonaws.com'
BOTO_CLIENT_VERIFY = None

LOCAL_FTYPE = 'local'
S3_FTYPE = 's3'
S3_PATH_PREFIX = 's3://'
S3_PATH_PREFIX_LEN = len(S3_PATH_PREFIX)
MIN_UTC_MS_AFTER_WHICH_TO_CONSIDER_TS_AS_REL_SECS = 1e8

s3_root_s = ':::'
s3_root_p = re.compile(s3_root_s)


def mk_s3_root(root, s3_access, s3_secret):
    return s3_root_s.join([root, s3_access, s3_secret])


def extract_s3_creds_from_root(root):
    split = s3_root_p.split(root)
    if len(split) == 3:
        root, s3_access, s3_secret = split[0], split[1], split[2]
    else:
        s3_access, s3_secret = None, None
    return root, s3_access, s3_secret


class FaccException(Exception):

    def __init__(self, message):
        self.message = message

    def __str__(self):
        return 'FaccException::{}'.format(self.message)

    @classmethod
    def not_implemented(cls):
        return FaccException('Not implemented')


class GenericFileAccess(object):

    def __init__(self, path=None):
        self._path = path

    @abc.abstractmethod
    def isdir(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def isfile(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def mkdir(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def join(self, p1, p2):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def listdir(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def glob(self, pattern):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def open(self, path, mode='rb'):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def getsize(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def basename(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def copyfile(self, src, dst):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def rm(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def rmdir(self, path):
        raise FaccException.not_implemented()

    @abc.abstractmethod
    def format_file_name(self, **kwargs):
        """
            Generate file name from passed components that is accepted
            by specific filesystem
        :param kwargs:
        :return:
        """

        raise FaccException.not_implemented()

    def __contains__(self, path=None):

        if path is None:
            path = self._path

        if path is None:
            return False

        return self.isdir(path) or self.isfile(path)

    def __len__(self):
        if self._path is None:
            return 0

        if self.isdir(self._path):
            return len(self.listdir(self._path))
        else:
            return self.getsize(self._path)

    def __iter__(self):
        if self._path and self.isdir(self._path):
            for items in self.listdir(self._path):
                yield items

    def __str__(self):
        return '{}::{}'.format(self.__class__.__name__, self._path)

    @classmethod
    def filepath_search(cls, filepath, search_paths=()):
        """
        Searches for a filepath that actually resolves to a file (i.e. os.path.isfile(filepath) returns True.
        Will first check the input filepath as is.
        If not found, will then loop through search_paths in that order, and try to find the file with the listed paths
        (i.e. prefixes).
        If it exhausted all possibilities, will return None.
        :param filepath: The filepath (seed) to search for
        :param search_paths: A list of path prefixes to look for the file
        :return: A filepath that will be found (if using open(filepath) for example), or None if not found
        """
        if os.path.isfile(filepath):
            return filepath
        else:
            for path in search_paths:
                candidate_filepath = os.path.join(path, filepath)
                if os.path.isfile(candidate_filepath):
                    return candidate_filepath
            return None  # if couldn't find a match at this point, return None

    @classmethod
    def dirpath_search(cls, dirpath, search_paths=()):
        """
        Searches for a dirpath that actually resolves to a file (i.e. os.path.isdir(dirpath) returns True.
        Will first check the input dirpath as is.
        If not found, will then loop through search_paths in that order, and try to find the folder with the listed paths
        (i.e. prefixes).
        If it exhausted all possibilities, will return None.
        :param dirpath: The dirpath (seed) to search for
        :param search_paths: A list of path prefixes to look for the file
        :return: A dirpath that will be found (if using open(filepath) for example), or None if not found
        """
        if os.path.isdir(dirpath):
            return dirpath
        else:
            for path in search_paths:
                candidate_dirpath = os.path.join(path, dirpath)
                if os.path.isdir(candidate_dirpath):
                    return candidate_dirpath
            return None  # if couldn't find a match at this point, return None

    @classmethod
    def ftype_of(cls, ref):
        if ref.startswith(os.path.sep):
            return LOCAL_FTYPE
        elif ref.startswith('s3://'):
            return S3_FTYPE
        else:
            raise ValueError(
                "Couldn't figure out the ftype for: {}".format(ref))


class LocalFileAccess(GenericFileAccess):
    def __init__(self, path=None):
        GenericFileAccess.__init__(self, path)

    def isdir(self, path):
        return os.path.isdir(path)

    def isfile(self, path):
        return os.path.isfile(path)

    def mkdir(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def join(self, p1, p2):
        return os.path.join(p1, p2)

    def listdir(self, path):
        return [os.path.join(path, l) for l in os.listdir(path)]

    def glob(self, pattern):
        return glob(pattern)

    def open(self, path, mode='rb'):
        return open(path, mode)

    def getsize(self, path):
        return os.path.getsize(path)

    def basename(self, path):
        return os.path.basename(path)

    def copyfile(self, src, dst):
        copyfile(src, dst)

    def rm(self, path):
        os.remove(path)

    def rmdir(self, path):
        os.rmdir(path)


class S3FileAccess(GenericFileAccess):

    def __init__(self, fs, path=None):
        GenericFileAccess.__init__(self, path)
        self.fs = fs

    def isdir(self, path):
        if self.fs.exists(path):
            try:
                self.fs.info(path)
                return False
            except:
                return True
        else:
            return False

    def isfile(self, path):
        if self.fs.exists(path):
            try:
                self.fs.info(path)
                return True
            except:
                return False
        else:
            return False

    def mkdir(self, path):
        self.fs.mkdir(path)

    def join(self, p1, p2):
        return os.path.join(p1, p2)

    def listdir(self, path):
        return self.fs.ls(path)

    def glob(self, pattern):
        return self.fs.glob(pattern)

    def open(self, path, mode='rb'):
        return self.fs.open(path, mode)

    def getsize(self, path):
        if self.fs.exists(path):
            try:
                info = self.fs.info(path)
                return info['Size']
            except Exception as ex:
                raise Exception("File does not exist : {}".format(ex.message))
        else:
            raise Exception("File does not exist")

    def basename(self, path):
        split = path.split('/')
        return split[-1]

    def copyfile(self, src, dst):
        self.fs.copy(src, dst)

    def rm(self, path):
        self.fs.rm(path)

    def rmdir(self, path):
        self.fs.rmdir(path)

    def format_file_name(self, **kwargs):
        pass


class FileAccess(object):
    """
        Factory class that provides factory method for file access depending on schema type
        >>> type(FileAccess.factory(LOCAL_FTYPE)).__name__
        'LocalFileAccess'
        >>> type(FileAccess.factory(S3_FTYPE)).__name__
        'S3FileAccess'
    """

    @staticmethod
    def factory(type, s3_access=None, s3_secret=None, **kwargs):
        """
        s3 keys should be taken from a config file or through boto3 auth mechanisms if they dynamically change
        :param s3_access:
        :param s3_secret:
        :return:
        """
        if type == LOCAL_FTYPE:
            return LocalFileAccess(**kwargs)
        if type == S3_FTYPE:
            # Not sure about the readability, but negating the env var value does the trick
            # Read as: if not running on Slox, verify = {not False is True}, else verify={not True is False}
            client_kwargs = {
                'endpoint_url': DFLT_S3_HOST,
                'verify': BOTO_CLIENT_VERIFY
            }
            fs = S3FileSystem(anon=False,
                              key=s3_access,
                              secret=s3_secret,
                              client_kwargs=client_kwargs,
                              config_kwargs={'signature_version': 's3v4'},
                              **kwargs)
            return S3FileAccess(fs)


if __name__ == "__main__":

    rootdir = os.path.expanduser('~/tmp/')
    filepath = os.path.join(rootdir, '011.mp3')
    lfa = FileAccess.factory(type=LOCAL_FTYPE, path=filepath)
    print((len(lfa)))
    for i in lfa:
        print(i)

    print(lfa)

    print((filepath in lfa))

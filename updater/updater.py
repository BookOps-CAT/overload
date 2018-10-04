# updates overload
import shutil
import os
import sys
import time
import subprocess
from distutils.dir_util import copy_tree


def run_update(src_directory):
    # print 'source dir:', src_directory
    if os.path.isfile('overload.exe'):

        CREATE_NO_WINDOW = 0x08000000

        # kill the app
        try:
            subprocess.call(
                'TASKKILL /F /IM overload.exe',
                creationflags=CREATE_NO_WINDOW)
            time.sleep(1)
        except:
            pass

        # delete content of the main folder except updater.exe
        entries = [f for f in os.listdir('.') if 'updater' not in f]
        for f in entries:
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

        # copy updated files
        entries = [f for f in os.listdir(src_directory) if 'updater' not in f]
        for f in entries:
            if os.path.isdir(src_directory + '\\' + f):
                copy_tree(src_directory + '\\' + f, os.getcwd() + '\\' + f)
            else:
                shutil.copy2(src_directory + '\\' + f, os.getcwd())

        # apply patches
        # find if any new patches have been copied
        entries = [f for f in os.listdir('.') if 'patch' in f]
        # run patches in order
        for f in sorted(entries):
            subprocess.call(f, creationflags=CREATE_NO_WINDOW)

        subprocess.call(
            'overload.exe',
            creationflags=CREATE_NO_WINDOW)


if __name__ == '__main__':
    run_update(sys.argv[1])

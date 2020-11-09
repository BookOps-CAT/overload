"""
date: 2020-07-28
This patch moves data persited in USERS/.../AppData/Roaming/Overload/ folder to
USERS/BookOps Apps/Overload/
Increased security policies of the library in Windows 10 block our apps - this is a walkaround
for this issue.
"""

import os
import shutil


OLD_APP_DIR = os.path.join(os.environ["APPDATA"], "Overload")
NEW_APP_DIR = os.path.join(os.environ["USERPROFILE"], "BookOps Apps\\Overload")
PATCHING_RECORD = os.path.join(NEW_APP_DIR, "changesLog\\patching_record.txt")


# copy all app data to a new folder
if not os.path.isdir(NEW_APP_DIR):
    try:
        shutil.move(OLD_APP_DIR, NEW_APP_DIR)
        # updating patching record
        with open(PATCHING_RECORD, "a") as file:
            file.write(
                "0.0.3 - applied (moves app data to USERS/.../BookOps Apps/Overload/ directory.)\n"
            )
    except Exception as e:
        pass

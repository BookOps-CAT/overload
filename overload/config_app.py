import json

from setup_dirs import USER_DATA
from credentials import decrypt_file_data, store_in_vault, evaluate_worldcat_creds


def decrypt_creds(key, fh):
    data = decrypt_file_data(key, fh)
    jdata = json.loads(data)

    # store data in user_data

    print(jdata)


if __name__ == "__main__":
    key = ""
    decrypt_creds(key, "creds.bin")

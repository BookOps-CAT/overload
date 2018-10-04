# handles initial ingests services credentials and
# stores them in Windows Credential manager

import shelve
import os.path
from Crypto.Cipher import AES
import keyring


from setup_dirs import CREDS_DIR, USER_DATA


def identify_credentials_location():
    """
    creates a path to folder where credentials are
    stored
    returns:
        path (str)
    """

    user_data = shelve.open(USER_DATA)
    try:
        update_dir = user_data['paths']['update_dir']
        if update_dir == '':
            return None
        creds_dir = os.path.join(
            os.path.split(update_dir)[0], CREDS_DIR)
        return creds_dir
    except KeyError:
        return None
    finally:
        user_data.close()


def encrypt_file_data(key, source, dst):
    """
    encrypts data in a file
    args:
        key (encryption key)
        source (path to file to be encrypted)
        dst (path to encrypted file)
    """

    cipher = AES.new(key, AES.MODE_EAX)
    with open(source, 'rb') as file:
        data = file.read()
        ciphertext, tag = cipher.encrypt_and_digest(data)
        file_out = open(dst, 'wb')
        [file_out.write(x) for x in (cipher.nonce, tag, ciphertext)]


def decrypt_file_data(key, fh):
    """
    decrypts data in a file
    args:
        key (encryption key)
        fh (file handle)
    """

    with open(fh, 'rb') as file:
        nonce, tag, ciphertext = [file.read(x) for x in (16, 16, -1)]
        cipher = AES.new(key, AES.MODE_EAX, nonce)
        data = cipher.decrypt_and_verify(ciphertext, tag)
        return data


def standard_from_vault(application, user):
    """
    gets password for appliction/user from Windows Credential Locker
    args:
        application
        user
    returns:
        password
    """

    password = keyring.get_password(application, user)
    return password


def standard_to_vault(application, user, password):
    """
    stores credentials in Windows Credential Locker
    args:
        applicaiton (name of application)
        user (name of user)
        password
    """

    # check if credentials already stored and if so
    # delete and store updated ones
    if not standard_from_vault(application, user):
        keyring.set_password(application, user, password)
    else:
        keyring.delete_password(application, user)
        keyring.set_password(application, user, password)

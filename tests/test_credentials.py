# -*- coding: utf-8 -*-

import unittest
import os
import keyring


from context import credentials


class TestCredentials(unittest.TestCase):

    def setUp(self):
        self.creds = 'creds.json'
        self.key = 'some_key-0123456'
        self.encrypt_creds = 'creds.bin'
        self.app = 'myapp-test'
        self.user = 'test_user1'
        self.passw = 'test-pass'

    def tearDown(self):
        try:
            os.remove(self.encrypt_creds)
        except WindowsError:
            pass
        try:
            keyring.delete_password(self.app, self.user)
        except keyring.errors.PasswordDeleteError:
            pass

    def test_identify_credential_location(self):
        loc = credentials.identify_credentials_location()
        self.assertTrue(
            os.path.isdir(loc))

    def test_encrypt_file_data_produces_file(self):
        credentials.encrypt_file_data(
            self.key, self.creds, self.encrypt_creds)
        self.assertTrue(
            os.path.isfile(self.encrypt_creds))

    def test_decrypt_file_data(self):
        source_file = open(self.creds, 'rb')
        source_data = source_file.read()
        credentials.encrypt_file_data(
            self.key, self.creds, self.encrypt_creds)
        decrypted_data = credentials.decrypt_file_data(
            self.key, self.encrypt_creds)
        self.assertEqual(
            source_data, decrypted_data)

    def test_storing_and_retrieving_pass_from_Windows_vault(self):
        self.assertIsNone(
            credentials.standard_to_vault(
                self.app, self.user, self.passw))
        self.assertEqual(
            credentials.standard_from_vault(self.app, self.user),
            self.passw)


if __name__ == '__main__':
    unittest.main()

# -*- coding: utf-8 -*-

# run after test_platform, so the logic is validated first
# requires dev platform authorization named "Platform DEV" in USER_DATA

import unittest
from mock import patch
import requests_mock
import os

from context import SHEET_SCOPE, FDRIVE_SCOPE


class TestGooCommunications(unittest.TestCase):

    def setUp(self):
        self.token = 'goo_token.json'

    # def tearDown(self):
    # 	# delete token
    # 	os.remove(self.token)

    def test_get_auth(self):
        auth = goo_comms.get_auth()


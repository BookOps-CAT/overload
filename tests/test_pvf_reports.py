# -*- coding: utf-8 -*-

import unittest
import shelve
import pandas as pd

from context import reports


class Test_Reports(unittest.TestCase):
    def setUp(self):
        d = {
            '1': {
                'vendor_id': 'ven0001',
                'vendor': 'TEST VENDOR1',
                'updated_by_vendor': False,
                'callNo_match': True,
                'target_callNo': 'TEST CALL',
                'vendor_callNo': 'TEST CALL',
                'inhouse_dups': [],
                'target_sierraId': '01234567',
                'mixed': ['00000003'],
                'other': ['00000004'],
                'action': 'attach'},
            '2': {
                'vendor_id': 'ven0002',
                'vendor': 'TEST VENDOR2',
                'updated_by_vendor': True,
                'callNo_match': False,
                'target_callNo': 'TEST CALL A',
                'vendor_callNo': 'TEST CALL B',
                'inhouse_dups': [],
                'target_sierraId': '02345678',
                'mixed': [],
                'other': [],
                'action': 'overlay'},
            '3': {
                'vendor_id': 'ven0003',
                'vendor': 'TEST VENDOR3',
                'updated_by_vendor': True,
                'callNo_match': True,
                'target_callNo': 'TEST CALL A',
                'vendor_callNo': 'TEST CALL A',
                'inhouse_dups': [],
                'target_sierraId': '2345678',
                'mixed': [],
                'other': [],
                'action': 'insert'},
            '4': {
                'vendor_id': 'ven0004',
                'vendor': 'TEST VENDOR4',
                'updated_by_vendor': True,
                'callNo_match': True,
                'target_callNo': 'TEST CALL A',
                'vendor_callNo': 'TEST CALL A',
                'inhouse_dups': [],
                'target_sierraId': None,
                'mixed': [],
                'other': [],
                'action': 'insert'},
            '5': {
                'vendor_id': 'ven0005',
                'vendor': 'TEST VENDOR5',
                'updated_by_vendor': False,
                'callNo_match': True,
                'target_callNo': 'TEST CALL A',
                'vendor_callNo': 'TEST CALL A',
                'inhouse_dups': [],
                'target_sierraId': '',
                'mixed': [],
                'other': [],
                'action': 'insert'}
        }
        stats_shelf = shelve.open('temp')
        for key, value in d.iteritems():
            stats_shelf[key] = value
        stats_shelf.close()

    def cleanUp(self):
        stats_shelf = shelve.open('temp')
        stats_shelf.clear()
        stats_shelf.close()

    def test_shelf2dataframe(self):
        df = reports.shelf2dataframe('temp', 'nypl')
        self.assertIsInstance(
            df, pd.DataFrame)
        self.assertEqual(
            list(df.columns.values),
            ['action', 'callNo_match', 'inhouse_dups', 'mixed', 'other', 'target_callNo', 'target_sierraId', 'updated_by_vendor', 'vendor', 'vendor_callNo', 'vendor_id'])
        self.assertEqual(
            df.shape, (5, 11))
        # check if replaces empty strings with np.NaN values
        self.assertEqual(
            df.index[df['mixed'].isnull()].tolist(),
            [2, 4, 3, 5])

    def test_shelf2dataframe_sierra_id_formatting(self):
        df = reports.shelf2dataframe('temp', 'nypl')
        print df.head()

    def test_create_nypl_stats(self):
        df = reports.shelf2dataframe('temp', 'nypl')
        stats = reports.create_stats('nypl', df)
        self.assertEqual(
            stats.shape, (5, 7))
        self.assertEqual(
            stats.columns.tolist(),
            ['vendor', 'attach', 'insert', 'update', 'total', 'mixed', 'other'])
        self.assertEqual(
            stats.iloc[0]['attach'], 1)
        self.assertEqual(
            stats.iloc[0]['vendor'], 'TEST VENDOR1')
        self.assertEqual(
            stats.iloc[0]['insert'], 0)
        self.assertEqual(
            stats.iloc[0]['update'], 0)
        self.assertEqual(
            stats.iloc[0]['total'], 1)
        self.assertEqual(
            stats.iloc[0]['mixed'], 1)
        self.assertEqual(
            stats.iloc[0]['other'], 1)
        self.assertEqual(
            stats.iloc[1]['attach'], 0)
        self.assertEqual(
            stats.iloc[1]['vendor'], 'TEST VENDOR2')
        self.assertEqual(
            stats.iloc[1]['insert'], 0)
        self.assertEqual(
            stats.iloc[1]['update'], 1)
        self.assertEqual(
            stats.iloc[1]['total'], 1)
        self.assertEqual(
            stats.iloc[1]['mixed'], 0)
        self.assertEqual(
            stats.iloc[1]['other'], 0)

    def test_create_bpl_stats(self):
        df = reports.shelf2dataframe('temp', 'bpl')
        stats = reports.create_stats('bpl', df)
        self.assertEqual(
            stats.shape, (5, 5))
        self.assertEqual(
            stats.columns.tolist(),
            ['vendor', 'attach', 'insert', 'update', 'total'])
        self.assertEqual(
            stats.iloc[0]['attach'], 1)
        self.assertEqual(
            stats.iloc[0]['vendor'], 'TEST VENDOR1')
        self.assertEqual(
            stats.iloc[0]['insert'], 0)
        self.assertEqual(
            stats.iloc[0]['update'], 0)
        self.assertEqual(
            stats.iloc[0]['total'], 1)
        self.assertEqual(
            stats.iloc[1]['attach'], 0)
        self.assertEqual(
            stats.iloc[1]['vendor'], 'TEST VENDOR2')
        self.assertEqual(
            stats.iloc[1]['insert'], 0)
        self.assertEqual(
            stats.iloc[1]['update'], 1)
        self.assertEqual(
            stats.iloc[1]['total'], 1)

    def test_report_dups(self):
        df = reports.shelf2dataframe('temp', 'nypl')
        dups = reports.report_dups('NYPL', 'branches', df)
        self.assertEqual(
            dups.index.tolist(), [1])

    def test_callNo_issues(self):
        df = reports.shelf2dataframe('temp', 'bpl')
        callNo = reports.report_callNo_issues(df, 'cat')
        self.assertEqual(
            list(callNo.columns.values),
                ['vendor', 'vendor_id', 'target_id', 'vendor_callNo', 'target_callNo', 'duplicate bibs'])
        self.assertEqual(
            callNo.index.tolist(),[2])


if __name__ == '__main__':
    unittest.main()

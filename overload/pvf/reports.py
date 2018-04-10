# creates pvr statistical reports

import pandas as pd
import numpy as np
import shelve


def generate_processing_summary(system, library, agent, batch_meta):
    """
    creates a summary for processed batch
    args:
        system (nypl or bpl)
        library (branches or research)
        agent (cat, sel, acq)
    return:
        list of summary lines
    """
    meta = shelve.open(batch_meta)
    summary = []
    summary.append(
        'system: {}, library: {}, user: {}\n'.format(
            system.upper(), library, agent.upper()))
    summary.append(
        'total processed files: {}  '.format(
            meta['processed_files']))
    summary.append(
        'total process records: {}\n'.format(
            meta['processed_bibs']))
    summary.append(
        'file names: {}\n'.format(
            ','.join(
                name.split('/')[-1] for name in meta['file_names'])))
    summary.append(
        'processing time: {}\n'.format(
            meta['processing_time']))
    meta.close()
    return summary


def shelf2dataframe(batch_stats):
    stats = shelve.open(batch_stats)
    frames = []
    for key, value in stats.iteritems():
        frames.append(pd.DataFrame(value, index=[int(key)]))
    df = pd.concat(frames).replace('', np.NaN)
    stats.close()
    return df


def create_stats(df):
    frames = []
    n = 0
    for vendor, data in df.groupby('vendor'):
        n += 1
        attach = data[
            data['action'] == 'attach']['action'].count()
        insert = data[
            data['action'] == 'insert']['action'].count()
        update = data[
            data['action'] == 'overlay']['action'].count()
        frames.append(pd.DataFrame(
            data={
                'vendor': vendor,
                'attach': attach,
                'insert': insert,
                'update': update,
                'total': attach + insert + update},
            columns=['vendor', 'attach', 'insert', 'update', 'total'],
            index=[n]))
    df_rep = pd.concat(frames)
    return df_rep


def report_dups(system, library, df):
    if system == 'nypl':
        if library == 'branches':
            other = 'research'
        else:
            other = 'branches'
        dups = '{} dups'.format(library)

    df_rep = df[[
        'vendor_id', 'vendor', 'target_sierraId',
        'inhouse_dups', 'mixed', 'other']]

    df_rep = df_rep[
        df_rep['inhouse_dups'].notnull()|df_rep['mixed'].notnull()|df_rep['other'].notnull()].replace(np.NaN, '')
    df_rep.columns = ['vendor', 'vendor_id', 'target_id', dups, 'mixed', other]

    return df_rep


def report_callNo_issues(df):
    df_call = df[~df['callNo_match']]
    df_call = df_call[
        ['vendor', 'vendor_id', 'target_sierraId',
         'vendor_callNo', 'target_callNo', 'inhouse_dups']].replace(np.NaN, '')
    df_call.columns = ['vendor', 'vendor_id', 'target_id', 'vendor_callNo', 'target_callNo', 'duplicate bibs']
    return df_call


def report_details(system, library, df):
    if system == 'nypl':
        if library == 'branches':
            other = 'research bibs'
        else:
            other = 'branches bibs'
        dups = '{} dups'.format(library)

    df = df.sort_index()
    print df.columns.tolist()
    df = df[[
        'vendor', 'vendor_id', 'action', 'target_sierraId',
        'updated_by_vendor',
        'callNo_match', 'vendor_callNo', 'target_callNo',
        'inhouse_dups', 'mixed', 'other']]
    df.columns = [
        'vendor', 'vendor_id', 'action', 'target_id',
        'updated',
        'callNo_match', 'vendor_callNo', 'target_callNo',
        dups, 'mixed bibs', other]
    df = df.replace(np.NaN, '')
    return df

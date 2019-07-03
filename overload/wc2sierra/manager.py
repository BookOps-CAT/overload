# module controlling upgrade/catalog from Worldcat process
import csv
import logging
import os

from bibs.bibs import (BibOrderMeta, create_initials_field,
                       write_marc21, create_controlfield,
                       create_target_id_field, create_command_line_field)
from bibs.parsers import (parse_isbn, remove_oclcNo_prefix)
from bibs.crosswalks import string2xml, marcxml2array
from bibs.bpl_callnum import create_bpl_fiction_callnum
from bibs.nypl_callnum import (create_nypl_fiction_callnum,
                               create_nypl_recap_callnum,
                               create_nypl_recap_item)
from bibs.sierra_dicts import NW2SEXPORT_COLS, BW2SEXPORT_COLS
from bibs.xml_bibs import (get_oclcNo, get_cuttering_fields,
                           get_tag_008, get_record_leader, get_tag_300a)
from connectors.worldcat.session import (SearchSession, MetadataSession,
                                         is_positive_response, no_match,
                                         extract_record_from_response)
from credentials import get_from_vault, evaluate_worldcat_creds
from criteria import (meets_upgrade_criteria, meets_catalog_criteria,
                      meets_user_criteria)
from datastore import (session_scope, WCSourceBatch, WCSourceMeta, WCHit)
from db_worker import (insert_or_ignore, delete_all_table_data,
                       retrieve_record, retrieve_one_related,
                       retrieve_records, retrieve_related, update_hit_record,
                       update_meta_record)
from errors import OverloadError
from logging_setup import LogglyAdapter
from source_parsers import sierra_export_data
from utils import save2csv
from setup_dirs import W2S_MULTI_ORD


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def update_progbar(progbar):
    """creates progbar ticks"""
    progbar['value'] += 1
    progbar.update()


def store_meta(model, record):
    pass


def interpret_search_response(response, db_session, wcsmid):
    if is_positive_response(response) and \
            not no_match(response):
        hit = True
        doc = string2xml(response.content)
        insert_or_ignore(
            db_session, WCHit, wcsmid=wcsmid,
            hit=hit, search_marcxml=doc)
    else:
        hit = False
        insert_or_ignore(
            db_session, WCHit, wcsmid=wcsmid,
            hit=hit, search_marcxml=None)

    return hit


def remove_previous_process_data():
    with session_scope() as db_session:
        # deletes WCSourceBatch data and all related tables
        delete_all_table_data(db_session, WCSourceBatch)
        module_logger.debug('Data from previous run has been deleted.')

    try:
        os.remove(W2S_MULTI_ORD)
    except WindowsError:
        pass


def get_credentials(api):
    module_logger.debug('Acquiring Worldcat credentials.')
    creds = get_from_vault(api, 'Overload')
    return evaluate_worldcat_creds(creds)


def request_record(session, oclcNo):
    if oclcNo:
        res = session.get_record(oclcNo)
        module_logger.info('Metadata API request: {}'.format(res.url))
        if is_positive_response(res) and not no_match(res):
            module_logger.info('Match found.')
            xml_record = extract_record_from_response(res)
            return xml_record
        else:
            module_logger.info('No record found.')
    else:
        module_logger.info(
            'Metadata API request skipped: no data to query')


def create_local_fields(
        marcxml, system, library,
        order_data=None, recap_no=None):
    module_logger.debug('Creating local fields.')

    local_fields = []
    leader_string = get_record_leader(marcxml)
    cuttering_opts = get_cuttering_fields(marcxml)
    tag_008 = get_tag_008(marcxml)
    tag_300a = get_tag_300a(marcxml)

    if system == 'NYPL' and library == 'branches':
        callNum = create_nypl_fiction_callnum(
            leader_string, tag_008, tag_300a, cuttering_opts, order_data)
        local_fields.append(callNum)
    elif system == 'NYPL' and library == 'research':
        callNum = create_nypl_recap_callnum(recap_no)
        local_fields.append(callNum)
        itemField = create_nypl_recap_item(order_data, recap_no)
        module_logger.debug('Created itemField: {}'.format(str(itemField)))
        local_fields.append(itemField)
    elif system == 'BPL':
        callNum = create_bpl_fiction_callnum(
            leader_string, tag_008, tag_300a, cuttering_opts, order_data)
        local_fields.append(callNum)
    else:
        module_logger.warning(
            'Call number creation for {}-{} not implemented yet'.format(
                system, library))

    initials = create_initials_field(
        system, library, 'W2Sbot')
    local_fields.append(initials)

    return local_fields


def nypl_oclcNo_field(marcxml):
    oclcNo = get_oclcNo(marcxml)
    oclcNo = remove_oclcNo_prefix(oclcNo)
    tag_001 = create_controlfield('001', oclcNo)
    return tag_001


def selected2marc():
    pass


def launch_process(source_fh, data_source, dst_fh, system, library,
                   progbar1, progbar2,
                   process_label, hits, nohits, meet_crit_counter,
                   fail_user_crit_counter, fail_glob_crit_counter,
                   action, encode_level, mat_type, cat_rules, cat_source,
                   recap_range, id_type='ISBN', api=None):
    """
    work notes:
    1. iterate through the source files and extract bib/order metadata
    2. temporarily persist this data in local datastore
    3. iterate over the batch and find best hit for each
    4. persist in local store matched record as a pymarc object
    5. display results (with all data needed for Sierra import) to user
    5. allow user to decide what to write to final file

    args:
        source_fh: str, file path
        progbar: tkinter widget
        counter: tkinter StringVar
        hits: tkinter IntVar
        nohits: tkinter IntVar
    """
    module_logger.debug('Launching W2S process.')
    remove_previous_process_data()

    # calculate max counter
    process_label.set('reading:')
    with open(source_fh, 'r') as file:
        reader = csv.reader(file)
        # skip header
        header = reader.next()
        # check if Sierra export file has a correct structure
        if data_source == 'Sierra export':
            if system == 'NYPL':
                if header != NW2SEXPORT_COLS:
                    raise OverloadError(
                        'Sierra Export format incorrect.\nPlease refer to help'
                        'for more info.')
            elif system == 'BPL':
                if header != BW2SEXPORT_COLS:
                    raise OverloadError(
                        'Sierra Export format incorrect.\nPlease refer to help'
                        'for more info.')

        # calculate pogbar max values
        c = 0
        for row in reader:
            c += 1
        progbar1['maximum'] = c * 4
        progbar2['maximum'] = c

    # keep track of recap call numbers
    if recap_range:
        recap_no = recap_range[0]

    with session_scope() as db_session:
        # create batch record
        batch_rec = insert_or_ignore(
            db_session, WCSourceBatch, file=source_fh)
        db_session.flush()
        batch_id = batch_rec.wcsbid

        # parse depending on the data source
        if data_source == 'IDs list':
            with open(source_fh, 'r') as file:
                reader = csv.reader(file)
                # skip header
                reader.next()
                if id_type == 'ISBN':
                    for row in reader:
                        meta = BibOrderMeta(
                            system=system,
                            dstLibrary=library,
                            t020=[parse_isbn(row[0])])
                        insert_or_ignore(
                            db_session, WCSourceMeta,
                            wcsbid=batch_id, meta=meta)
                        update_progbar(progbar1)
                        update_progbar(progbar2)
                elif id_type == 'UPC':
                    # to be implemented
                    pass
        elif data_source == 'Sierra export':
            data = sierra_export_data(source_fh, system, library)
            for meta, single_order in data:
                if system == 'NYPL' and library == 'research':
                    if not single_order:
                        row = [
                            'b{}a'.format(meta.sierraId),
                            meta.title]
                        save2csv(W2S_MULTI_ORD, row)
                        progbar1['maximum'] = progbar1['maximum'] - 3
                    else:
                        insert_or_ignore(
                            db_session, WCSourceMeta,
                            wcsbid=batch_id, meta=meta)
                else:
                    insert_or_ignore(
                        db_session, WCSourceMeta,
                        wcsbid=batch_id, meta=meta)
                update_progbar(progbar1)
                update_progbar(progbar2)

    processed_counter = 0
    found_counter = 0
    not_found_counter = 0
    creds = get_credentials(api)

    # query Worldcat
    process_label.set('querying:')
    # reset progbar2
    progbar2['value'] = 0
    with session_scope() as db_session:
        metas = retrieve_records(
            db_session, WCSourceMeta, wcsbid=batch_id)
        with SearchSession(creds) as session:
            for m in metas:
                module_logger.debug(m.meta)
                hit = False
                if m.meta.t001:
                    res = session.cql_query(
                        m.meta.t001, 'OCLC #', mat_type, cat_source)
                    module_logger.debug('OCLC # request: {}'.format(res.url))

                    hit = interpret_search_response(res, db_session, m.wcsmid)

                    if hit:
                        found_counter += 1
                    else:
                        not_found_counter += 1

                    hits.set(found_counter)
                    nohits.set(not_found_counter)

                if m.meta.t010 and not hit:
                    res = session.cql_query(
                        m.meta.t010, 'LCCN', mat_type, cat_source)
                    module_logger.debug('LCCN request: {}'.format(res.url))

                    hit = interpret_search_response(res, db_session, m.wcsmid)

                    if hit:
                        found_counter += 1
                    else:
                        not_found_counter += 1

                    hits.set(found_counter)
                    nohits.set(not_found_counter)

                if m.meta.t020 and not hit:
                    # will iterate over all ISBNs if no hits
                    found = False
                    for isbn in m.meta.t020:
                        res = session.cql_query(
                            isbn, 'ISBN', mat_type, cat_source)
                        module_logger.debug('ISBN request: {}'.format(res.url))

                        hit = interpret_search_response(
                            res, db_session, m.wcsmid)

                        if hit:
                            found = True
                            found_counter += 1
                            break  # stop searching

                    if not found:
                        not_found_counter += 1

                    hits.set(found_counter)
                    nohits.set(not_found_counter)

                if m.meta.t024 and not hit:
                    found = False
                    for upc in m.meta.t024:
                        res = session.cql_query(
                            upc, 'UPC', mat_type, cat_source)
                        module_logger.debug('ISBN request: {}'.format(res.url))

                        hit = interpret_search_response(
                            res, db_session, m.wcsmid)

                        if hit:
                            found = True
                            found_counter += 1
                            break  # stop searching

                    if not found:
                        not_found_counter += 1

                    hits.set(found_counter)
                    nohits.set(not_found_counter)

                update_progbar(progbar1)
                update_progbar(progbar2)
                processed_counter += 1

        db_session.commit()

    #     # verify found matches meet set criteria
    #     process_label.set('downloading:')
    #     # reset progbar2
    #     progbar2['value'] = 0

    #     with MetadataSession(creds) as session:
    #         metas = retrieve_related(
    #             db_session, WCSourceMeta, 'wchits', wcsbid=batch_id)
    #         for m in metas:
    #             if m.wchits.hit:
    #                 oclcNo = get_oclcNo(m.wchits.search_marcxml)
    #                 xml_record = request_record(session, oclcNo)
    #                 if xml_record is not None:
    #                     update_hit_record(
    #                         db_session, WCHit, m.wchits.wchid,
    #                         match=oclcNo,
    #                         match_marcxml=xml_record)
    #             update_progbar(progbar1)
    #             update_progbar(progbar2)
    #     db_session.commit()

    #     # check if meet criteria & write (will be replaced with user selection)
    #     process_label.set('analyzing:')
    #     progbar2['value'] = 0
    #     rows = retrieve_records(
    #         db_session, WCHit, hit=True)
    #     for row in rows:
    #         xml_record = row.match_marcxml

    #         if meets_upgrade_criteria(xml_record):
    #             if meets_user_criteria(
    #                     xml_record,
    #                     encode_level,
    #                     mat_type,
    #                     cat_rules,
    #                     cat_source):
    #                 if action == 'upgrade':
    #                     meet_crit_counter.set(
    #                         meet_crit_counter.get() + 1)

    #                     marc_record = marcxml2array(xml_record)[0]

    #                     # check if Sierra bib # provided and use
    #                     # for overlay command line
    #                     if data_source == 'Sierra export':
    #                         order_data = retrieve_record(
    #                             db_session,
    #                             WCSourceMeta,
    #                             wcsmid=row.wcsmid).meta
    #                         if order_data.sierraId:
    #                             overlay_tag = create_target_id_field(
    #                                 system,
    #                                 order_data.sierraId)
    #                             marc_record.add_ordered_field(
    #                                 overlay_tag)

    #                     if system == 'NYPL':
    #                         marc_record.remove_fields('001', '949')
    #                         tag_001 = nypl_oclcNo_field(xml_record)
    #                         marc_record.add_ordered_field(tag_001)
    #                         tag_949 = create_command_line_field(
    #                             '*b3=h;')
    #                         marc_record.add_ordered_field(tag_949)

    #                     initials = create_initials_field(
    #                         system, library, 'W2Sbot')
    #                     # add Sierra bib code 3

    #                     marc_record.add_ordered_field(initials)
    #                     write_marc21(dst_fh, marc_record)

    #                 elif action == 'catalog':
    #                     if meets_catalog_criteria(xml_record, library):
    #                         # add call number & write to file
    #                         if data_source == 'Sierra export':
    #                             order_data = retrieve_record(
    #                                 db_session,
    #                                 WCSourceMeta,
    #                                 wcsmid=row.wcsmid).meta

    #                             local_fields = create_local_fields(
    #                                 xml_record, system, library, order_data,
    #                                 recap_no)
    #                             overlay_tag = create_target_id_field(
    #                                 system,
    #                                 order_data.sierraId)
    #                             local_fields.append(overlay_tag)
    #                         else:
    #                             # data source a list of IDs
    #                             local_fields = create_local_fields(
    #                                 xml_record, system, library)

    #                         if local_fields:
    #                             meet_crit_counter.set(
    #                                 meet_crit_counter.get() + 1)

    #                             # move this block to separate method that
    #                             # will be called later by user afer the
    #                             # selection of records

    #                             marc_record = marcxml2array(xml_record)[0]
    #                             marc_record.remove_fields('949')
    #                             for field in local_fields:
    #                                 marc_record.add_ordered_field(field)
    #                             if system == 'NYPL':
    #                                 marc_record.remove_fields('001')
    #                                 tag_001 = nypl_oclcNo_field(xml_record)
    #                                 marc_record.add_ordered_field(tag_001)
    #                                 tag_949 = create_command_line_field(
    #                                     '*b3=h;')
    #                                 marc_record.add_ordered_field(tag_949)
    #                                 recap_no += 1

    #                             update_hit_record(
    #                                 db_session, WCHit, row.wchid,
    #                                 prepped_marc=marc_record)
    #                     else:
    #                         fail_glob_crit_counter.set(
    #                             fail_glob_crit_counter.get() + 1)
    #             else:
    #                 fail_user_crit_counter.set(
    #                     fail_user_crit_counter.get() + 1)
    #         else:
    #             fail_glob_crit_counter.set(
    #                 fail_glob_crit_counter.get() + 1)

    #         update_progbar(progbar1)
    #         update_progbar(progbar2)

    #         # make sure W2S stays within assigned Recap range
    #         if system == 'NYPL' and library == 'research':
    #             if action == 'catalog':
    #                 if recap_no > recap_range[1]:
    #                     raise OverloadError(
    #                         'Used all available ReCAP call numbers '
    #                         'assigned for W2S.')

    # # show completed
    # progbar1['value'] = progbar1['maximum']
    # progbar2['value'] = progbar2['maximum']


def get_meta_by_id(session, meta_ids):
    meta = []
    for mid in meta_ids:
        instance = retrieve_one_related(
            session, WCSourceMeta, 'wchits', wcsmid=mid)
        meta.append(instance)
    return meta


def retrieve_bibs_batch(meta_ids):
    data = []
    with session_scope() as db_session:
        recs = get_meta_by_id(db_session, meta_ids)
        for r in recs:
            sierra_data = dict(
                title=r.meta.title,
                sierraId=r.meta.sierraId,
                oid=r.meta.oid,
                locs=r.meta.locs,
                venNote=r.meta.venNote,
                note=r.meta.note,
                intNote=r.meta.intNote,
                choice=r.selected)
            if r.wchits.prepped_marc:
                worldcat_data = str(r.wchits.prepped_marc)
            else:
                worldcat_data = None
            data.append((r.wchits.wchid, sierra_data, worldcat_data))
        db_session.expunge_all()

    return data


def count_total():
    meta_ids = []
    with session_scope() as db_session:
        recs = retrieve_records(db_session, WCSourceMeta)
        total = 0
        for rec in recs:
            total += 1
            meta_ids.append(rec.wcsmid)
    return total, meta_ids


def persist_choice(meta_ids, selected):
    with session_scope() as db_session:
        for mid in meta_ids:
            update_meta_record(
                db_session, WCSourceMeta, mid,
                selected=selected)


def create_marc_file(dst_fh, set_holdings):
    with session_scope() as db_session:
        recs = retrieve_related(
            db_session, WCSourceMeta, 'wchits', selected=True)
        for r in recs:
            marc = r.wchits.prepped_marc
            if marc:
                write_marc21(dst_fh, marc)

                if set_holdings:
                    oclcNo = r.wchits.match
                    # set holdings here

from unidecode import unidecode

from cs_context import (
    ONS,
    session_scope,
    WCHit,
    WCSourceMeta,
    retrieve_record,
    retrieve_related,
    xml2string,
    string2xml,
    results2record_list,
    meets_upgrade_criteria,
    meets_catalog_criteria,
    meets_user_criteria,
    has_records,
    create_rec_lvl_range,
    marcxml2array,
    meets_rec_lvl,
    is_english_cataloging,
    get_cat_lang,
    get_datafield_040,
    meets_mat_type,
    get_record_leader,
    get_cuttering_fields,
    get_subject_fields,
)


def check_criteria_output(ids, lvl):
    with session_scope() as session:
        lvl_range = create_rec_lvl_range(lvl)

        for n in ids:
            rec = retrieve_record(session, WCHit, wchid=n)
            res = results2record_list(rec.query_results)
            # print(xml2string(res))
            c = 0
            for r in res:
                print("wchid: {}, rec: {}".format(n, c))
                print("\tis_english_cataloging: {}".format(is_english_cataloging(r)))
                print(
                    "\tmeets_rec_lvl: {}, \t\tlvl range: {}".format(
                        meets_rec_lvl(r, lvl_range), lvl_range
                    )
                )
                print("\tmeets_mat_type: {}".format(meets_mat_type(r)))
                print("\tmeets_user_criteria: {}".format(meets_user_criteria(r, lvl)))
                print(
                    "\tmeets_catalog_criteria: {}".format(
                        meets_catalog_criteria(r, "branches")
                    )
                )
                c += 1


def check_cutter_subject_options(ids):
    with session_scope() as session:
        for n in ids:
            rec = retrieve_record(session, WCHit, wchid=n)
            res = results2record_list(rec.query_results)
            # print(xml2string(res))
            c = 0
            for r in res:
                print("wchid: {}, rec: {}".format(n, c))
                print("cuttering opts: {}".format(get_cuttering_fields(r)))
                print("subject opts: {}".format(get_subject_fields(r)))
                c += 1


def uni_test():
    for i in [43, 49, 53, 73, 78, 96, 154, 160, 161, 162, 163, 164, 176]:
        with session_scope() as session:
            rec = retrieve_record(session, WCHit, wchid=i)
            marcxml = rec.match_marcxml
            bib = xml2string(marcxml)
            print(bib)
            try:
                tags = get_cuttering_fields(marcxml)
            except AttributeError:
                continue
            try:
                last_name = tags["100"]
            except KeyError:
                continue
            try:
                last_name = last_name.strip().decode("utf-8")
                last_name = unidecode(unicode(last_name)).upper()
                # print(last_name)
            except UnicodeEncodeError:
                # print(last_name)
                print("Error on record no: {}".format(i))


def find_dup_oclcNo():
    oclcNos = []
    uniqueNos = set()
    with session_scope() as session:
        recs = retrieve_related(session, WCSourceMeta, "wchits", selected=True)
        for r in recs:
            if r.wchits.match_oclcNo:
                oclcNos.append(r.wchits.match_oclcNo)
                # print("{} = {}".format(r.wchits.match_oclcNo, r.wchits.holdings_status))

    for o in oclcNos:
        if o in uniqueNos:
            print(o)
        else:
            uniqueNos.add(o)


def fix_holdings():
    with MetadataSession(credentials=token) as session:
        responses = session.holdings_set_batch(oclc_numbers)
        holdings = holdings_responses(responses)
        if holdings:
            for oclcNo, holding in holdings.items():
                rec = retrieve_record(db_session, WCHit, match_oclcNo=oclcNo)
                if holding[0] in ("set", "exists"):
                    holding_set = True
                else:
                    holding_set = False
                update_hit_record(
                    db_session,
                    WCHit,
                    rec.wchid,
                    holding_set=holding_set,
                    holding_status=holding[0],
                    holding_response=holding[1],
                )

    db_session.commit()


if __name__ == "__main__":

    # check_criteria_output([1, 5, 7, 11, 12], "level 3")
    # check_cutter_subject_options([2])
    # uni_test()
    find_dup_oclcNo()

from bibs.xml_bibs import (get_record_leader, get_datafield_040,
                           get_cat_lang, get_tag_005, get_tag_008,
                           get_tag_300a)
from bibs.parsers import (extract_record_lvl, is_picture_book, is_fiction,
                          get_audience_code)


def is_english_cataloging(marcxml):
    """
    args:
        marcxml
    """
    field = get_datafield_040(marcxml)
    code = get_cat_lang(field)
    if not code or code == 'eng':
        return True
    else:
        return False


def create_rec_lvl_range(rec_lvl):
    """
    gui values:
        'Level 1 - blank, I, 4 ',
        'Level 2 & up - M, K, 7, 1, 2',
        'Level 3 & up - 3, 8'
    """
    default = [' ', 'I', '4']
    try:
        lvl = rec_lvl[6]
        if lvl == '1':
            return default
        elif lvl == '2':
            default.extend(['M', 'K', '7', '1', '2'])
            return default
        elif lvl == '3':
            default.extend(['M', 'K', '7', '1', '2', '3', '8'])
            return default
    except IndexError:
        return default
    except TypeError:
        return default


def meets_rec_lvl(marcxml, rec_lvl_range):
    leader_string = get_record_leader(marcxml)
    match_lvl = extract_record_lvl(leader_string)
    if match_lvl in rec_lvl_range:
        return True
    else:
        return False


def meets_user_criteria(marcxml, rec_lvl, rec_type='any',
                        cat_rules='any', cat_source='any'):
    """
    verifies if record meets all criteria set by a user
    args:
        marcxml: xml
        rec_lvl: str,
    """

    rec_lvl_range = create_rec_lvl_range(rec_lvl)
    if meets_rec_lvl(marcxml, rec_lvl_range):
        return True
    else:
        return False

    # add the rest of criteria here
    # rec type
    # cat rules
    # cat source


def meets_upgrade_criteria(marcxml, local_timestamp=None):
    """
    Validates bibliographic record meets upgrade criteria
    args:
        marcxml: xml, bibliographic record in MARCXML format
    returns:
        Boolean
    """

    if is_english_cataloging(marcxml):
        if local_timestamp:
            # compare
            wc_timestamp = float(get_tag_005(marcxml))
            if float(local_timestamp) < wc_timestamp:
                # worldcat record has been updated
                return True
            else:
                return False
        else:
            return True
    else:
        return False


def meets_catalog_criteria(marcxml):
    """
    sets criteria for Worldcat records to be fully cataloged;
    at the moment records we will process only print fiction
    materials, records must follow anglo-american cataloging
    rules (040$b blank or eng)
    args:
        marcxml: xml, record in MARCXML format
    returns:
        Boolean
    """

    # print materials and fiction only
    leader_string = get_record_leader(marcxml)
    tag_008 = get_tag_008(marcxml)
    audn_code = get_audience_code(leader_string, tag_008)
    tag_300a = get_tag_300a(marcxml)

    if is_fiction(leader_string, tag_008) or \
            is_picture_book(audn_code, tag_300a):
        return True
    else:
        return False
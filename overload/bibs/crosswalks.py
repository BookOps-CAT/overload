from io import BytesIO
import xml.etree.ElementTree as ET

from pymarc import Record, Field, parse_xml_to_array

try:
    from bibs import InhouseBibMeta
except:
    pass


def platform2pymarc_obj(data=None):
    """
    converts platform bib data into pymarc object
    args:
        data in json format
    return:
        pymarc Record obj
    """
    record = Record(to_unicode=True, force_utf8=True)
    # parse variable fields
    varFields = data.get("varFields")
    for f in varFields:
        if f.get("fieldTag") == "_":
            record.leader = f.get("content")
        # control fields case
        elif f.get("subfields") is None:
            field = Field(
                tag=f.get("marcTag"),
                indicators=[f.get("ind1"), f.get("ind2")],
                data=f.get("content"),
            )
            record.add_field(field)
        else:  # variable fields
            subfields = []
            for d in f.get("subfields"):
                subfields.append(d.get("tag"))
                subfields.append(d.get("content"))
            field = Field(
                tag=f.get("marcTag"),
                indicators=[f.get("ind1"), f.get("ind2")],
                subfields=subfields,
            )
            record.add_field(field)
    return record


def platform2meta(results=None):
    """
    extracts meta from Platform results
    args:
        results (json format)
    return:
        list of inhouse bibs meta
    """

    bibs = []
    data = results.get("data")
    for b in data:
        # get Sierra data
        bid = b.get("id")
        locations = [x.get("code") for x in b.get("locations")]
        bib = platform2pymarc_obj(b)
        # parse marc data
        meta = InhouseBibMeta(bib, sierraId=bid, locations=locations)
        bibs.append(meta)
    return bibs


def bibs2meta(results=None):
    # results are deduped to accomodate two separate Z3950
    # searches for 10 and 13 digit ISBNs
    bibs = []
    bibs_ids = set()
    if results:
        for bib in results:
            meta = InhouseBibMeta(bib)
            if meta.sierraId not in bibs_ids:
                bibs_ids.add(meta.sierraId)
                bibs.append(meta)
    return bibs


def string2xml(marcxml_as_string):
    return ET.fromstring(marcxml_as_string)


def xml2string(marcxml):
    return ET.tostring(marcxml, encoding="utf-8")


def marcxml2array(marcxml):
    """
    serializes marcxml into pymarc array
    args:
        marcxml: xml
    returns:
        records: pymarc records array
    """
    records = BytesIO(ET.tostring(marcxml, encoding="utf-8"))
    return parse_xml_to_array(records)

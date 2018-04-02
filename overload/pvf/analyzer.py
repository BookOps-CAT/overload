# compares vendor bib meta and inhouse bib meta and returns analysis object


class PVRReport:
    """
    A general analysis report class.
    Use analysis classes specific to each system.
    """
    def __init__(self, meta_vendor, meta_inhouse):
        self._meta_vendor = meta_vendor
        self._meta_inhouse = meta_inhouse
        self.vendor_resource_id = None
        self.vendor = meta_vendor.vendor
        self.updated_by_vendor = False
        self.callNo_match = False
        self.vendor_callNo = meta_vendor.bCallNumber
        self.inhouse_callNo_matched = None
        self.inhouse_dups = []
        self.target_sierraId = None
        self.action = 'insert'

        self._determine_resource_id()
        self._order_inhouse_meta()

    def _determine_resource_id(self):
        if self._meta_vendor.t001 is not None:
            self.vendor_resource_id = self._meta_vendor.t001
        elif self._meta_vendor.t020 != []:
            self.vendor_resource_id = self._meta_vendor.t020[0]
        elif self._meta_vendor.t024 != []:
            self.vendor_resource_id = self._meta_vendor.t024[0]

    def _order_inhouse_meta(self):
        # will remove any duplicates from the Sierra results
        # order from the newest bib to the oldest
        descending_order = []
        bib_order = dict()
        n = -1
        for meta in self._meta_inhouse:
            n += 1
            bib_order[meta.sierraId] = n

        for key, value in sorted(bib_order.iteritems(), reverse=True):
            descending_order.append(self._meta_inhouse[value])
        self._meta_inhouse = descending_order

    def _determine_record_updated(self, meta_inhouse):
        updated = False
        if self._meta_vendor.t005 is None:
            pass
        elif meta_inhouse.t005 is None:
            updated = True
        elif self._meta_vendor.t005 > meta_inhouse.t005:
            updated = True
        return updated

    def _determine_callNo_match(self, meta_inhouse):
        match = False
        if self._meta_vendor.bCallNumber is None or \
                meta_inhouse.bCallNumber is None:
            match = True
        elif self._meta_vendor.bCallNumber == \
                meta_inhouse.bCallNumber:
            match = True
        return match

    def to_dict(self):
        return {
            'resource_id': self.vendor_resource_id,
            'vendor': self.vendor,
            'updated_by_vendor': self.updated_by_vendor,
            'callNo_match': self.callNo_match,
            'inhouse_callNo_matched': self.inhouse_callNo_matched,
            'inhouse_dups': ','.join(self.inhouse_dups),
            'target_sierraId': self.target_sierraId,
            'action': self.action}

    def __repr__(self):
        return "<PVF Report(vendor_resource_id={}, vendor={}, " \
            "callNo_match={}, inhouse_callNo_matched={}, " \
            "updated_by_vendor={}, " \
            "inhouse_dups={}, target_sierraId={}, action={})>".format(
                self.vendor_resource_id,
                self.vendor,
                self.callNo_match,
                self.inhouse_callNo_matched,
                self.updated_by_vendor,
                self.inhouse_dups,
                self.target_sierraId,
                self.action)


class PVR_NYPLReport(PVRReport):
    """
    Creates a NYPL analysis report of a vendor record in relation
    to retrieved from the catalog existing matching bibs
    """
    def __init__(self, library, agent, meta_vendor, meta_inhouse):
        PVRReport.__init__(self, agent, meta_vendor, meta_inhouse)
        self.library = library
        self._matched = []
        self.mixed = []
        self.other = []

        self._group_by_library()

        if agent == 'cat':
            self._cataloging_workflow()
        elif agent == 'sel':
            self._selection_workflow()
        elif agent == 'acq':
            self._acquisition_workflow()

    def _group_by_library(self):

        for meta in self._meta_inhouse:
            if self._meta_vendor.dstLibrary == self.library:
                # correct library
                self.matched.append(meta)
            elif meta.ownLibrary == 'mixed':
                self.mixed.append(meta.sierraId)
            else:
                self.other.append(meta.sierraId)

    def _cataloging_workflow(self):
        print 'nypl cat activated'

    def _selection_workflow(self):
        pass

    def _acquisition_workflow(self):
        pass

    def to_dict(self):
        return {
            'resource_id': self.vendor_resource_id,
            'vendor': self.vendor,
            'updated_by_vendor': self.updated_by_vendor,
            'callNo_match': self.callNo_match,
            'inhouse_callNo_matched': self.inhouse_callNo_matched,
            'inhouse_dups': ','.join(self.inhouse_dups),
            'target_sierraId': self.target_sierraId,
            'mixed': ','.join(self.mixed),
            'other': ','.join(self.other),
            'action': self.action}

    def __repr__(self):
        return "<PVF Report(vendor_resource_id={}, vendor={}, " \
            "callNo_match={}, inhouse_callNos={}, updated_by_vendor={}, " \
            "inhouse_dups={}, target_sierraId={}, mixed={}, "\
            "other={}, action={})>".format(
                self.vendor_resource_id,
                self.vendor,
                self.callNo_match,
                self.inhouse_callNos,
                self.updated_by_vendor,
                self.inhouse_dups,
                self.target_sierraId,
                self.mixed,
                self.other,
                self.action)









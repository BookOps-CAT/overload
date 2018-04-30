import Tkinter as tk
import ttk
import tkMessageBox
import tkFileDialog
import shelve
import os.path
import shutil
import logging
import os
from pymarc.exceptions import RecordLengthInvalid


from bibs import bibs
from validation import validate_files
from validators.marcedit import delete_validation_report
from gui_utils import ToolTip, BusyManager
import overload_help
import reports
from errors import OverloadError
from manager import run_processing, save_stats
from setup_dirs import MY_DOCS, USER_DATA, CVAL_REP, \
    BATCH_META, BATCH_STATS


module_logger = logging.getLogger('overload_console.pvr_gui')


class OrderTemplate(tk.Frame):
    def __init__(self, parent):
        self.parent = parent
        tk.Frame.__init__(self, self.parent, background='white')
        self.top = tk.Toplevel(self, background='white')
        self.cur_manager = BusyManager(self)
        self.top.iconbitmap('./icons/templates.ico')
        self.top.title('Record Templates')

        # variables
        self.template_name = tk.StringVar()
        self.acqType = tk.StringVar()
        self.claim = tk.StringVar()
        self.oCode1 = tk.StringVar()
        self.oCode2 = tk.StringVar()
        self.oCode3 = tk.StringVar()
        self.oCode4 = tk.StringVar()
        self.oForm = tk.StringVar()
        self.oNote = tk.StringVar()
        self.oType = tk.StringVar()
        self.vendor = tk.StringVar()
        self.lang = tk.StringVar()
        self.country = tk.StringVar()
        self.identity = tk.StringVar()
        self.genNote = tk.StringVar()
        self.intNote = tk.StringVar()
        self.oldOrdNo = tk.StringVar()
        self.selector = tk.StringVar()
        self.venAddr = tk.StringVar()
        self.venNote = tk.StringVar()
        self.venTitleNo = tk.StringVar()
        self.blanketPO = tk.StringVar()
        self.shipTo = tk.StringVar()
        self.requestor = tk.StringVar()
        self.paidNote = tk.StringVar()
        self.bForm = tk.StringVar()

        # layout of the main frame
        self.top.columnconfigure(0, minsize=5)
        self.top.columnconfigure(1, minsize=200)
        # self.top.columnconfigure(7, minsize=5)
        self.top.columnconfigure(9, minsize=5)
        self.top.columnconfigure(15, minsize=5)
        # self.top.rowconfigure(19, minsize=5)
        self.top.rowconfigure(21, minsize=5)
        self.top.rowconfigure(23, minsize=10)

        # templates list
        ttk.Label(self.top, text='available:').grid(
            row=0, column=1, sticky='sw', pady=10)
        scrollbar = ttk.Scrollbar(self.top, orient=tk.VERTICAL)
        scrollbar.grid(
            row=1, column=2, sticky='nsw', rowspan=20, padx=2, pady=10)
        self.templateLst = tk.Listbox(
            self.top,
            yscrollcommand=scrollbar.set)
        self.templateLst.bind('<Double-Button-1>', self.show_details)
        self.templateLst.grid(
            row=1, column=1, sticky='snew', rowspan=20, pady=10)
        scrollbar['command'] = self.templateLst.yview

        # template name
        ttk.Label(self.top, text='template:').grid(
            row=0, column=4, sticky='sw', padx=5, pady=10)
        self.templateEnt = ttk.Entry(
            self.top, textvariable=self.template_name)
        self.templateEnt.grid(
            row=0, column=5, columnspan=8, sticky='sew', pady=10)

        # fixed fields frame
        self.fixedFrm = ttk.LabelFrame(
            self.top,
            text='order fixed fields')
        self.fixedFrm.grid(
            row=1, rowspan=12, column=4, columnspan=5,
            sticky='snew', padx=5, pady=5)
        self.fixedFrm.columnconfigure(2, minsize=5)
        self.fixedFrm.rowconfigure(12, minsize=5)

        # fixed fields widgets
        ttk.Label(self.fixedFrm, text='ACQ Type', style='Small.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='sw')
        self.acqTypeCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.acqType)
        self.acqTypeCbx.grid(
            row=1, column=0, columnspan=2, sticky='sew')

        ttk.Label(self.fixedFrm, text='Claim', style='Small.TLabel').grid(
            row=2, column=0, columnspan=2, sticky='sw')
        self.claimCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.claim)
        self.claimCbx.grid(
            row=3, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 1',
            style='Small.TLabel').grid(
            row=4, column=0, sticky='sw')
        self.oCode1Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode1)
        self.oCode1Cbx.grid(
            row=5, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 2',
            style='Small.TLabel').grid(
            row=6, column=0, columnspan=2, sticky='sw')
        self.oCode2Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode2)
        self.oCode2Cbx.grid(
            row=7, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 3',
            style='Small.TLabel').grid(
            row=8, column=0, columnspan=2, sticky='sw')
        self.oCode3Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode3)
        self.oCode3Cbx.grid(
            row=9, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='OrderCode 4',
            style='Small.TLabel').grid(
            row=10, column=0, columnspan=2, sticky='sw')
        self.oCode4Cbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oCode4)
        self.oCode4Cbx.grid(
            row=11, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Form',
            style='Small.TLabel').grid(
            row=0, column=3, columnspan=2, sticky='sw')
        self.oFormCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oForm)
        self.oFormCbx.grid(
            row=1, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Order Note',
            style='Small.TLabel').grid(
            row=2, column=3, columnspan=2, sticky='sw')
        self.oNoteCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oNote)
        self.oNoteCbx.grid(
            row=3, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Order Type',
            style='Small.TLabel').grid(
            row=4, column=3, columnspan=2, sticky='sw')
        self.oTypeCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.oType)
        self.oTypeCbx.grid(
            row=5, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Vendor',
            style='Small.TLabel').grid(
            row=6, column=3, columnspan=2, sticky='sw')
        self.vendorCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.vendor)
        self.vendorCbx.grid(
            row=7, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Language',
            style='Small.TLabel').grid(
            row=8, column=3, columnspan=2, sticky='sw')
        self.langCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.lang)
        self.langCbx.grid(
            row=9, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.fixedFrm, text='Country',
            style='Small.TLabel').grid(
            row=10, column=3, columnspan=2, sticky='sw')
        self.countryCbx = ttk.Combobox(
            self.fixedFrm, textvariable=self.country)
        self.countryCbx.grid(
            row=11, column=3, columnspan=2, sticky='sew')

        # variable fields frame
        self.varFrm = ttk.LabelFrame(
            self.top,
            text='order variable fields')
        self.varFrm.grid(
            row=1, rowspan=12, column=10, columnspan=5,
            sticky='snew', padx=5, pady=5)
        self.varFrm.columnconfigure(2, minsize=5)
        self.varFrm.rowconfigure(12, minsize=5)

        # variable field widgets
        ttk.Label(self.varFrm, text='Identity', style='Small.TLabel').grid(
            row=0, column=0, columnspan=2, sticky='sw')
        self.identityEnt = ttk.Entry(
            self.varFrm, textvariable=self.identity)
        self.identityEnt.grid(
            row=1, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='General Note',
            style='Small.TLabel').grid(
            row=2, column=0, columnspan=2, sticky='sw')
        self.genNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.genNote)
        self.genNoteEnt.grid(
            row=3, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Internal Note',
            style='Small.TLabel').grid(
            row=4, column=0, columnspan=2, sticky='sw')
        self.intNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.intNote)
        self.intNoteEnt.grid(
            row=5, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Old Order No.',
            style='Small.TLabel').grid(
            row=6, column=0, columnspan=2, sticky='sw')
        self.oldOrdNoEnt = ttk.Entry(
            self.varFrm, textvariable=self.oldOrdNo)
        self.oldOrdNoEnt.grid(
            row=7, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Selector',
            style='Small.TLabel').grid(
            row=8, column=0, columnspan=2, sticky='sw')
        self.selectorEnt = ttk.Entry(
            self.varFrm, textvariable=self.selector)
        self.selectorEnt.grid(
            row=9, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Vendor Addr',
            style='Small.TLabel').grid(
            row=10, column=0, columnspan=2, sticky='sw')
        self.venAddrEnt = ttk.Entry(
            self.varFrm, textvariable=self.venAddr)
        self.venAddrEnt.grid(
            row=11, column=0, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Vendor Note',
            style='Small.TLabel').grid(
            row=0, column=3, columnspan=2, sticky='sw')
        self.venNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.venNote)
        self.venNoteEnt.grid(
            row=1, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Vendor Title No.',
            style='Small.TLabel').grid(
            row=2, column=3, columnspan=2, sticky='sw')
        self.venTitleNoEnt = ttk.Entry(
            self.varFrm, textvariable=self.venTitleNo)
        self.venTitleNoEnt.grid(
            row=3, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Blanket PO',
            style='Small.TLabel').grid(
            row=4, column=3, columnspan=2, sticky='sw')
        self.blanketPOEnt = ttk.Entry(
            self.varFrm, textvariable=self.blanketPO)
        self.blanketPOEnt.grid(
            row=5, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Ship To', style='Small.TLabel').grid(
            row=6, column=3, columnspan=2, sticky='sw')
        self.shipToEnt = ttk.Entry(
            self.varFrm, textvariable=self.shipTo)
        self.shipToEnt.grid(
            row=7, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Requestor', style='Small.TLabel').grid(
            row=8, column=3, columnspan=2, sticky='sw')
        self.requestorEnt = ttk.Entry(
            self.varFrm, textvariable=self.requestor)
        self.requestorEnt.grid(
            row=9, column=3, columnspan=2, sticky='sew')

        ttk.Label(
            self.varFrm, text='Paid Note', style='Small.TLabel').grid(
            row=10, column=3, columnspan=2, sticky='sw')
        self.paidNoteEnt = ttk.Entry(
            self.varFrm, textvariable=self.paidNote)
        self.paidNoteEnt.grid(
            row=11, column=3, columnspan=2, sticky='sew')

        # sierra bibliographic format frame
        self.bibFrm = ttk.LabelFrame(
            self.top, text='Sierra bibliographic format')
        self.bibFrm.grid(
            row=20, column=4, columnspan=11, sticky='snew', padx=10, pady=10)
        self.bibFrm.rowconfigure(2, minsize=5)

        ttk.Label(
            self.bibFrm, text='Bib Form', style='Small.TLabel').grid(
            row=0, column=0, sticky='sw')
        self.bFormCbx = ttk.Combobox(
            self.bibFrm, textvariable=self.bForm)
        self.bFormCbx.grid(
            row=1, column=0, sticky='sew')

        # bottom buttons
        # button's frame
        # self.btnFrm = ttk.Frame(
        #     self.top)
        # self.btnFrm.grid(
        #     row=22, column=1, columnspan=12, padx=10, pady=10)
        # self.btnFrm.columnconfigure(0, minsize=200)
        # self.btnFrm.columnconfigure(1, minsize=10)
        # self.btnFrm.columnconfigure(2, minsize=5)

        self.newBtn = ttk.Button(
            self.top,
            text='new',
            command=self.create_template)
        self.newBtn.grid(
            row=22, column=1, columnspan=3, sticky='swe', padx=50, pady=5)

        self.saveBtn = ttk.Button(
            self.top,
            text='save',
            # width=8,
            command=self.save_template)
        self.saveBtn.grid(
            row=22, column=4, sticky='nwe', padx=10, pady=5)

        self.deleteBtn = ttk.Button(
            self.top,
            text='delete',
            # width=8,
            command=self.delete_template)
        self.deleteBtn.grid(
            row=22, column=6, sticky='nwe', padx=10, pady=5)

        self.helpBtn = ttk.Button(
            self.top,
            text='help',
            # width=8,
            command=self.help)
        self.helpBtn.grid(
            row=22, column=10, sticky='nwe', padx=10, pady=5)

        self.closeBtn = ttk.Button(
            self.top,
            text='close',
            # width=8,
            command=self.top.destroy)
        self.closeBtn.grid(
            row=22, column=13, sticky='nwe', padx=10, pady=5)

    def show_details(self):
        print 'showing details'

    def create_template(self):
        print 'creating new template'

    def save_template(self):
        print 'saving'

    def delete_template(self):
        print 'deleting'

    def help(self):
        print 'helping'


class ProcessVendorFiles(tk.Frame):
    """
    GUI to processing vendor files module which preprocesses records
    for Sierra import
    """

    def __init__(self, parent, controller, **app_data):
        self.parent = parent
        tk.Frame.__init__(self, parent, background='white')
        self.controller = controller
        self.activeW = app_data['activeW']
        self.activeW.trace('w', self.observer)

        self.cur_manager = BusyManager(self)

        # widget variables
        self.target_name = tk.StringVar()
        self.target = None
        self.file_count = tk.StringVar()
        self.marcVal = tk.IntVar()
        self.locVal = tk.IntVar()
        self.processed = tk.StringVar()
        self.archived = tk.StringVar()
        self.validated = tk.StringVar()
        self.last_directory_check = tk.IntVar()
        self.last_directory = None
        self.files = None
        self.system = tk.StringVar()
        self.system.trace('w', self.system_observer)
        self.library = tk.StringVar()
        self.agent = tk.StringVar()
        self.agent.trace('w', self.agent_observer)
        self.template = tk.StringVar()

        # logos
        self.nyplLogo = tk.PhotoImage(file='./icons/nyplLogo.gif')
        self.bplLogo = tk.PhotoImage(file='./icons/bplLogo.gif')

        # layout of the main frame
        self.rowconfigure(0, minsize=5)
        self.rowconfigure(1, minsize=120)
        self.rowconfigure(15, minsize=10)
        self.columnconfigure(0, minsize=5)
        self.columnconfigure(2, minsize=10)
        self.columnconfigure(4, minsize=5)

        # layout of the base frame
        self.baseFrm = ttk.LabelFrame(
            self,
            text='Process Vendor File')
        self.baseFrm.grid(
            row=1, column=1, rowspan=6, sticky='snew')
        self.baseFrm.rowconfigure(0, minsize=10)
        self.baseFrm.rowconfigure(2, minsize=5)
        self.baseFrm.rowconfigure(4, minsize=5)
        self.baseFrm.rowconfigure(7, minsize=5)
        self.baseFrm.rowconfigure(9, minsize=5)
        self.baseFrm.rowconfigure(14, minsize=10)
        self.baseFrm.rowconfigure(18, minsize=10)
        self.baseFrm.columnconfigure(0, minsize=10)
        self.baseFrm.columnconfigure(7, minsize=10)

        # layout of target parameters
        self.targetFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.targetFrm.grid(
            row=1, column=1, columnspan=6, sticky='snew')

        # system drop down menu
        self.systemLbl = ttk.Label(
            self.targetFrm,
            text='system:')
        self.systemLbl.grid(
            row=0, column=0, sticky='snew')
        self.systemCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.system,
            width=10)
        self.systemCbx.grid(
            row=0, column=1, sticky='nsw', padx=5, pady=10)

        # destination library drop down menu
        self.libraryLbl = ttk.Label(
            self.targetFrm,
            text='destination:')
        self.libraryLbl.grid(
            row=0, column=2, sticky='snew')
        self.libraryCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.library,
            width=10)
        self.libraryCbx.grid(
            row=0, column=3, sticky='nsw', padx=5, pady=10)

        # department drop down menu
        self.agentLbl = ttk.Label(
            self.targetFrm,
            text='department:')
        self.agentLbl.grid(
            row=0, column=4, sticky='snew')
        self.agentCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.agent)
        self.agentCbx.grid(
            row=0, column=5, columnspan=3, sticky='snew', padx=5, pady=10)

        # query method/database
        self.query_targetLbl = ttk.Label(
            self.targetFrm,
            text='query database/method:')
        self.query_targetLbl.grid(
            row=1, column=0, columnspan=2, sticky='snew')
        self.query_targetCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.target_name)
        self.query_targetCbx.grid(
            row=1, column=2, columnspan=6, sticky='snew', padx=5, pady=10)

        # templates to be applied
        self.templateLbl = ttk.Label(
            self.targetFrm,
            text='apply template:')
        self.templateLbl.grid(
            row=2, column=0, columnspan=2, sticky='snew')
        self.templateCbx = ttk.Combobox(
            self.targetFrm,
            textvariable=self.template)
        self.templateCbx.grid(
            row=2, column=2, columnspan=5, sticky='sew', padx=5, pady=10)
        # edit template button
        edit = tk.PhotoImage(file='./icons/edit.gif')
        self.templateBtn = ttk.Button(
            self.targetFrm,
            image=edit,
            command=self.create_template)
        self.templateBtn.grid(
            row=2, column=7, sticky='ne', padx=5)
        self.templateBtn.image = edit

        # browse & ftp buttons
        self.selectBtn = ttk.Button(
            self.baseFrm,
            text='browse files',
            command=self.select,
            cursor='hand2',
            width=12)
        self.selectBtn.grid(
            row=3, column=1, sticky='nw', padx=5, pady=10)
        self.ftpBtn = ttk.Button(
            self.baseFrm,
            text='get via FTP',
            command=self.ftp,
            cursor='hand2',
            width=12)
        self.ftpBtn.grid(
            row=3, column=2, sticky='nw', padx=5, pady=10)

        # default output directory
        self.default_directoryCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='previous output directory',
            variable=self.last_directory_check)
        self.default_directoryCbtn.grid(
            row=3, column=3, sticky='snew')

        # selected files
        self.selectedLbl = ttk.Label(
            self.baseFrm,
            textvariable=self.file_count)
        self.selectedLbl.grid(
            row=5, column=1, columnspan=2, sticky='nw')

        self.selected_filesEnt = ttk.Entry(
            self.baseFrm,
            style='Flat.TEntry',
            state='readonly')
        self.selected_filesEnt.grid(
            row=6, column=1, columnspan=6, sticky='nwe')

        # validation area
        self.validateLbl = ttk.Label(
            self.baseFrm,
            text='validation:')
        self.validateLbl.grid(
            row=8, column=1, sticky='nw')
        self.marcEditValCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='MARCEdit validation',
            variable=self.marcVal).grid(
            row=8, column=2, sticky='snw')
        self.localValCbtn = ttk.Checkbutton(
            self.baseFrm,
            cursor='hand2',
            text='local specs validation',
            variable=self.locVal).grid(
            row=8, column=3, columnspan=2, sticky='snw', padx=15)

        self.processBtn = ttk.Button(
            self.baseFrm,
            text='process',
            command=self.process,
            cursor='hand2',
            width=12)
        self.processBtn.grid(
            row=13, column=1, sticky='nw')

        self.progbar = ttk.Progressbar(
            self.baseFrm,
            mode='determinate',
            orient=tk.HORIZONTAL,)
        self.progbar.grid(
            row=13, column=2, sticky='snew', pady=10)

        # report layout
        self.reportFrm = ttk.Frame(
            self.baseFrm,
            borderwidth=2,
            relief='ridge')
        self.reportFrm.grid(
            row=15, column=1, rowspan=3, columnspan=6, sticky='snew')

        self.reportFrm.rowconfigure(0, minsize=5)
        self.reportFrm.rowconfigure(4, minsize=5)
        self.reportFrm.rowconfigure(7, minsize=5)
        self.reportFrm.columnconfigure(0, minsize=2)
        self.reportFrm.columnconfigure(2, minsize=50)
        self.reportFrm.columnconfigure(4, minsize=50)
        self.reportFrm.columnconfigure(6, minsize=50)
        self.reportFrm.columnconfigure(7, minsize=2)

        self.validatedLbl = ttk.Label(
            self.reportFrm,
            textvariable=self.validated)
        self.validatedLbl.grid(
            row=1, column=1, columnspan=6, sticky='nw')

        self.processedLbl = ttk.Label(
            self.reportFrm,
            textvariable=self.processed)
        self.processedLbl.grid(
            row=2, column=1, columnspan=6, sticky='nw')

        self.archivedLbl = ttk.Label(
            self.reportFrm,
            textvariable=self.archived)
        self.archivedLbl.grid(
            row=3, column=1, columnspan=6, sticky='nw')

        self.valid_reportBtn = ttk.Button(
            self.reportFrm,
            text='validation',
            command=self.errors,
            cursor='hand2',
            width=10)
        self.valid_reportBtn.grid(
            row=5, column=1, sticky='sw')
        self.createToolTip(
            self.valid_reportBtn,
            'display validation reports')

        self.statsBtn = ttk.Button(
            self.reportFrm,
            text='stats',
            command=self.batch_summary_window,
            cursor='hand2',
            width=10)
        self.statsBtn.grid(
            row=5, column=3, sticky='sw')
        self.createToolTip(
            self.statsBtn,
            'display statistics of your last processing')

        self.archiveBtn = ttk.Button(
            self.reportFrm,
            text='archive',
            command=self.archive,
            cursor='hand2',
            width=10)
        self.archiveBtn.grid(
            row=5, column=5, sticky='sw')
        self.createToolTip(
            self.archiveBtn,
            'save statistics and archive output MARC files')

        # default logo
        logo = tk.PhotoImage(file='./icons/PVRsmall.gif')
        self.logoDsp = ttk.Label(
            self, image=logo)
        # prevent image to be garbage collected by Python
        self.logoDsp.image = logo
        self.logoDsp.grid(
            row=1, column=8, columnspan=3, sticky='snew')

        # default activation labels
        self.libraryLbl = ttk.Label(
            self, textvariable=self.library,
            style='Bold.TLabel')
        self.libraryLbl.grid(
            row=2, column=9, sticky='new')

        self.agentLbl = ttk.Label(
            self, textvariable=self.agent,
            style='Bold.TLabel')
        self.agentLbl.grid(
            row=3, column=9, sticky='new')

        # navigation buttons
        self.helpBtn = ttk.Button(
            self,
            text='help',
            command=self.help,
            cursor='hand2',
            width=12)
        self.helpBtn.grid(
            row=5, column=8, columnspan=3, sticky='sew')

        self.closeBtn = ttk.Button(
            self,
            text='close',
            command=lambda: controller.show_frame('Main'),
            cursor='hand2',
            width=12)
        self.closeBtn.grid(
            row=6, column=8, columnspan=3, sticky='sew')

    def createToolTip(self, widget, text):
        toolTip = ToolTip(widget)

        def enter(event):
            toolTip.showtip(text)

        def leave(event):
            toolTip.hidetip()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def select(self):

        # determine last used directory
        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if 'pvr_last_open_dir' in paths:
            last_open_dir = paths['pvr_last_open_dir']
        else:
            last_open_dir = MY_DOCS

        # select files for processing
        files = tkFileDialog.askopenfilenames(
            parent=self,
            title='Select files',
            initialdir=last_open_dir)

        if len(files) > 0:
            self.files = files
            # update selected qty
            self.file_count.set('{} file(s) selected:'.format(len(self.files)))
            names = []
            for file in self.files:
                name = file.split('/')[-1]
                names.append(name)
            self.selected_filesEnt['state'] = '!readonly'
            self.selected_filesEnt.delete(0, tk.END)
            self.selected_filesEnt.insert(0, ','.join(names))
            self.selected_filesEnt['state'] = 'readonly'

            # save accessed directory for the future
            last_open_dir = '/'.join(self.files[-1].split('/')[:-1])
            paths = user_data['paths']
            paths['pvr_last_open_dir'] = last_open_dir
            user_data['paths'] = paths
            user_data.close()

            self.reset()

    def ftp(self):
        tkMessageBox.showwarning(
            'Under construction', 'Feature not implemented yet.\n'
            'Stay tuned...')

    def create_template(self):
        # tkMessageBox.showwarning(
        #     'Under construction', 'Feature not implemented yet.\n'
        #     'Stay tuned...')
        OrderTemplate(self)

    def process(self):
        self.reset()
        delete_validation_report()

        user_data = shelve.open(USER_DATA)

        # store parameters for the next time
        user_data['pvr_system'] = self.system.get()
        user_data['pvr_library'] = self.library.get()
        user_data['pvr_agent'] = self.agent.get()
        user_data['pvr_locval'] = self.locVal.get()
        user_data['pvr_marcval'] = self.marcVal.get()
        user_data['pvr_template'] = self.template.get()

        # record used connection target
        if 'Z3950' in self.target_name.get():
            name = self.target_name.get().split(' (')[0]
            method = 'Z3950'
        elif 'Sierra API' in self.target_name.get():
            name = self.target_name.get().split(' (')[0]
            method = 'Sierra API'
        elif 'Platform API' in self.target_name.get():
            name = self.target_name.get().split(' (')[0]
            method = 'Platform API'
        else:
            name = None
            method = None
        self.target = {'target': name, 'method': method}
        user_data['pvr_default_target'] = self.target

        # ask for folder for output marc files
        dir_opt = {}
        dir_opt['mustexist'] = False
        dir_opt['parent'] = self
        dir_opt['title'] = 'Please select directory for output files'

        if self.last_directory_check.get() == 0:
            dir_opt['initialdir'] = MY_DOCS
            d = tkFileDialog.askdirectory(**dir_opt)
            if d != '':
                self.last_directory = d
                paths = user_data['paths']
                paths['pvr_default_save_dir'] = d
                user_data['paths'] = paths
                # update tooltip displaying the folder
                self.createToolTip(
                    self.default_directoryCbtn,
                    self.last_directory)
            else:
                m = 'Please select a destination folder for ' \
                    'output MARC files to procceed.'
                tkMessageBox.showwarning('Missing Destination Folder', m)
        else:
            if 'pvr_default_save_dir' in user_data[
                    'paths']:
                self.last_directory = user_data[
                    'paths']['pvr_default_save_dir']
            else:
                dir_opt['initialdir'] = MY_DOCS
                d = tkFileDialog.askdirectory(**dir_opt)
                if d != '':
                    self.last_directory = d
                    paths = user_data['paths']
                    paths['pvr_default_save_dir'] = d
                    user_data['paths'] = paths
                    # update tooltip displaying the folder
                    self.createToolTip(
                        self.default_directoryCbtn,
                        self.last_directory)
                else:
                    m = 'Please select a destination folder for ' \
                        'output MARC files to procceed.'
                    tkMessageBox.showwarning('Missing Destination Folder', m)
        user_data.close()

        # verify all paramaters are present
        required_params = True
        missing_params = []
        if self.system.get() == '':
            required_params = False
            missing_params.append('Please select system')
        if self.system.get() == 'NYPL':
            if self.library.get() == '':
                required_params = False
                missing_params.append('Please select destination library')
            if self.agent.get() == '':
                required_params = False
                missing_params.append('Please select department')
        if self.target_name.get() == '':
            required_params = False
            missing_params.append('Please select query target')
        if self.files is None:
            required_params = False
            missing_params.append('Please select files for processing.')
        if self.last_directory is None:
            required_params = False
            missing_params.append(
                'Please select a directory to output processed files')

        if not required_params:
            tkMessageBox.showwarning(
                'Missing parameters', '\n '.join(missing_params))
        else:
            # run process
            self.cur_manager.busy()

            # calculate maximum for progbar
            legal_files = True
            total_bib_count = 0
            for file in self.files:
                try:
                    bib_count = bibs.count_bibs(file)
                    total_bib_count += bib_count
                except RecordLengthInvalid:
                    self.cur_manager.notbusy()
                    legal_files = False
                    m = 'Attempted to process non-MARC file,\n' \
                        'or invalid MARC file: {}'.format(file)
                    tkMessageBox.showerror('Incorrect file', m)

            if legal_files:
                self.progbar['maximum'] = total_bib_count

            # run validation if requested
            if self.marcVal.get() == 1:
                marcval = True
            else:
                marcval = False
                self.validated.set('validation: MARC syntax check skipped')
            if self.locVal.get() == 1:
                locval = True
            else:
                msg = self.validated.get() + ', local specs check skipped'
                self.validated.set(msg)
                locval = False

            # run validation if one of the validations selected
            if marcval or locval:
                try:
                    valid_files = validate_files(self.files, marcval, locval)
                    if valid_files:
                        self.validated.set('validation: records are A-OK!')
                    else:
                        self.cur_manager.notbusy()
                        self.validated.set('validation: !errors found!')
                        m = 'Some of the records in selected file(s) \n' \
                            'do not validate in MARCEdit.\n' \
                            'Please see error report for details.'
                        tkMessageBox.showerror('Validation', m)
                except OverloadError as e:
                    valid_files = False
                    self.cur_manager.notbusy()
                    tkMessageBox.showerror('Validation', e)

            # allow processing if both validations skipped
            if not marcval and not locval:
                valid_files = True

            if legal_files and valid_files:

                try:
                    run_processing(
                        self.files, self.system.get().lower(),
                        self.library.get(), self.agent.get()[:3],
                        self.target['method'], self.target['target'],
                        self.last_directory,
                        self.progbar)

                    # confirm files have been processed
                    self.processed.set(
                        'processed: {} file(s) including {} record(s)'.format(
                            len(self.files), total_bib_count))

                    # launch processing report
                    self.batch_summary_window()

                except OverloadError as e:
                    self.cur_manager.notbusy()
                    tkMessageBox.showerror(
                        'Processing Error', e)
                finally:
                    self.cur_manager.notbusy()

    def archive(self):
        try:
            save_stats()
        except OverloadError as e:
            tkMessageBox.showerror('Stats error', e)

        # move created files to the archive
        archive_files = []
        for file in os.listdir(self.last_directory):
            if file.endswith('.mrc') and (
                    '.DUP-' in file or '.NEW-' in file):
                archive_files.append(file)
        if len(archive_files) > 0:
            self.topA = tk.Toplevel(self, background='white')
            # self.topD.minsize(width=800, height=500)
            self.topA.iconbitmap('./icons/archive.ico')
            self.topA.title('Select files to be archived')

            self.topA.columnconfigure(0, minsize=10)
            self.topA.columnconfigure(4, minsize=10)
            self.topA.rowconfigure(0, minsize=10)

            n = 1
            self.check_id = dict()
            for file in archive_files:
                self.check_id[file] = tk.IntVar()
                check = ttk.Checkbutton(
                    self.topA,
                    cursor='hand2',
                    text=file,
                    variable=self.check_id[file])
                check.grid(
                    row=n, column=1)
                n += 1
            self.topA.rowconfigure(n + 1, minsize=10)
            ttk.Button(
                self.topA,
                text='archive',
                width=12,
                cursor='hand2',
                command=self.move_files).grid(
                    row=n + 2, column=1, sticky='nw', padx=5)
            ttk.Button(
                self.topA,
                text='close',
                width=12,
                cursor='hand2',
                command=self.topA.destroy).grid(
                    row=n + 2, column=3, sticky='nw', padx=5)
            self.topA.rowconfigure(n + 3, minsize=10)

    def move_files(self):
        batch = shelve.open(BATCH_META)
        system = batch['system']
        batch.close()

        user_data = shelve.open(USER_DATA)
        paths = user_data['paths']
        if system == 'bpl' and \
                'bpl_archive_dir' in paths:
            archive_dir = paths['bpl_archive_dir']
        elif system == 'nypl' and \
                'nyp_archive_dir' in paths:
            archive_dir = paths['nyp_archive_dir']
        else:
            archive_dir = None
            m = 'Please select archive directory in Settings'
            tkMessageBox.showerror('Error', m)
        user_data.close()

        if archive_dir is not None:
            all_archived = True
            for file, value in self.check_id.iteritems():
                if value.get() == 1:
                    # check if file exists
                    src = '{}/{}'.format(self.last_directory, file)
                    dst = '{}/{}'.format(archive_dir, file)
                    if os.path.exists(dst):
                        renaming = True
                        n = 1
                        while renaming:
                            file = '{}{}{}'.format(file[:-5], n, file[-4:])
                            dst = '{}/{}'.format(archive_dir, file)
                            if not os.path.exists(dst):
                                renaming = False
                            else:
                                n += 1

                    # archive selected
                    try:
                        shutil.copy2(src, dst)
                        os.remove(src)
                    except IOError:
                        all_archived = False
                        module_logger.error(
                            'Archiving error: not able to move '
                            'file: {} to: {}'.format(
                                src, dst))
                        m = 'Encounted error while ' \
                            'archiving file:\n{}'.format(src)
                        tkMessageBox.showerror('Archiving error', m)
                        self.topA.destroy()
            if all_archived:
                self.archived.set('archived: completed')
                m = 'Your MARC files have been added to the archive'
                tkMessageBox.showinfo('Archiving message', m)
                self.topA.destroy()

    def errors(self):
        # local specs validation will be saved in a different file
        # and displayed in a cumulative report

        if os.path.isfile(CVAL_REP):
            self.topV = tk.Toplevel(self, background='white')
            self.topV.minsize(width=800, height=500)
            self.topV.iconbitmap('./icons/report.ico')
            self.topV.title('Vendor files validation report')

            self.topV.columnconfigure(0, minsize=10)
            self.topV.columnconfigure(1, minsize=750)
            self.topV.columnconfigure(11, minsize=10)
            self.topV.rowconfigure(0, minsize=10)
            self.topV.rowconfigure(1, minsize=450)
            self.topV.rowconfigure(11, minsize=10)
            self.topV.rowconfigure(13, minsize=10)

            self.yscrollbarV = tk.Scrollbar(self.topV, orient=tk.VERTICAL)
            self.yscrollbarV.grid(
                row=1, column=10, rowspan=10, sticky='nse', padx=2)
            self.xscrollbarV = tk.Scrollbar(self.topV, orient=tk.HORIZONTAL)
            self.xscrollbarV.grid(
                row=10, column=1, columnspan=9, sticky='new', padx=2)

            self.reportVTxt = tk.Text(
                self.topV,
                borderwidth=0,
                wrap=tk.NONE,
                xscrollcommand=self.xscrollbarV.set,
                yscrollcommand=self.yscrollbarV.set)
            self.reportVTxt.grid(
                row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
            self.reportVTxt.tag_config('red', foreground='red', underline=1)

            self.yscrollbarV.config(command=self.reportVTxt.yview)
            self.xscrollbarV.config(command=self.reportVTxt.xview)

            tk.Button(
                self.topV,
                text='close',
                width=12,
                cursor='hand2',
                command=self.topV.destroy).grid(
                row=12, column=6, sticky='nw', padx=5)

            # generate report
            self.create_validation_report()
        else:
            m = 'Validation report not available'
            tkMessageBox.showwarning('validation report', m)

    def batch_summary_window(self):

        self.topD = tk.Toplevel(self, background='white')
        # self.topD.minsize(width=800, height=500)
        self.topD.iconbitmap('./icons/report.ico')
        self.topD.title('Vendor files report')

        self.topD.columnconfigure(0, minsize=10)
        self.topD.columnconfigure(1, minsize=750)
        self.topD.columnconfigure(11, minsize=10)
        self.topD.rowconfigure(0, minsize=10)
        self.topD.rowconfigure(1, minsize=450)
        self.topD.rowconfigure(11, minsize=10)
        self.topD.rowconfigure(13, minsize=10)

        self.yscrollbarD = tk.Scrollbar(self.topD, orient=tk.VERTICAL)
        self.yscrollbarD.grid(
            row=1, column=10, rowspan=9, sticky='nse', padx=2)
        self.xscrollbarD = tk.Scrollbar(self.topD, orient=tk.HORIZONTAL)
        self.xscrollbarD.grid(
            row=10, column=1, columnspan=9, sticky='swe')

        self.reportDTxt = tk.Text(
            self.topD,
            borderwidth=0,
            wrap=tk.NONE,
            yscrollcommand=self.yscrollbarD.set,
            xscrollcommand=self.xscrollbarD.set)
        self.reportDTxt.grid(
            row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
        self.reportDTxt.tag_config('blue', foreground='blue', underline=1)
        self.reportDTxt.tag_config('red', foreground='red')

        self.yscrollbarD.config(command=self.reportDTxt.yview)
        self.xscrollbarD.config(command=self.reportDTxt.xview)

        ttk.Button(
            self.topD,
            text='detailed view',
            width=12,
            cursor='hand2',
            command=self.detailed_view_window).grid(
            row=12, column=2, sticky='nw', padx=5)

        ttk.Button(
            self.topD,
            text='close',
            width=12,
            cursor='hand2',
            command=self.topD.destroy).grid(
            row=12, column=6, sticky='nw', padx=5)

        # generate report
        self.create_processing_report()

    def detailed_view_window(self):

        self.topB = tk.Toplevel(self, background='white')
        # self.topD.minsize(width=800, height=500)
        self.topB.iconbitmap('./icons/report.ico')
        self.topB.title('Vendor files detailed view')

        self.topB.columnconfigure(0, minsize=10)
        self.topB.columnconfigure(1, minsize=750)
        self.topB.columnconfigure(11, minsize=10)
        self.topB.rowconfigure(0, minsize=10)
        self.topB.rowconfigure(1, minsize=450)
        self.topB.rowconfigure(11, minsize=10)
        self.topB.rowconfigure(13, minsize=10)

        self.yscrollbarB = tk.Scrollbar(self.topB, orient=tk.VERTICAL)
        self.yscrollbarB.grid(
            row=1, column=10, rowspan=9, sticky='nse', padx=2)
        self.xscrollbarB = tk.Scrollbar(self.topB, orient=tk.HORIZONTAL)
        self.xscrollbarB.grid(
            row=10, column=1, columnspan=9, sticky='swe')

        self.reportBTxt = tk.Text(
            self.topB,
            borderwidth=0,
            wrap=tk.NONE,
            yscrollcommand=self.yscrollbarB.set,
            xscrollcommand=self.xscrollbarB.set)
        self.reportBTxt.grid(
            row=1, column=1, rowspan=9, columnspan=9, sticky='snew')
        self.reportBTxt.tag_config('blue', foreground='blue', underline=1)
        self.reportBTxt.tag_config('red', foreground='red')

        self.yscrollbarB.config(command=self.reportBTxt.yview)
        self.xscrollbarB.config(command=self.reportBTxt.xview)

        ttk.Button(
            self.topB,
            text='close',
            width=12,
            cursor='hand2',
            command=self.topB.destroy).grid(
            row=12, column=6, sticky='nw', padx=5)

        # generate report
        self.create_detailed_report()

    def create_validation_report(self):
        # reset report
        self.reportVTxt.delete(1.0, tk.END)

        # create new MARCEdit validation report
        self.reportVTxt.insert(
            tk.END, 'MARCEdit validation report(s):\n\n', 'red')
        mReport = open(CVAL_REP, 'r')
        for line in mReport:
            self.reportVTxt.insert(tk.END, line)
        mReport.close()
        self.reportVTxt['state'] = tk.DISABLED

    def create_processing_report(self):
        # reset report
        self.reportDTxt.delete(1.0, tk.END)

        # generate summary
        try:
            summary = reports.generate_processing_summary(BATCH_META)
            for line in summary:
                self.reportDTxt.insert(tk.END, line)
        except KeyError:
            self.reportDTxt.insert(tk.END, 'SUMMARY PARSING ERROR\n')
        self.reportDTxt.insert(tk.END, ('-' * 60) + '\n')

        # create dataframe to be tabulated
        try:
            module_logger.info(
                'Mapping BATCH_STATS to dataframe for general '
                'stats report.')
            df = reports.shelf2dataframe(BATCH_STATS)
        except KeyError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe. '
                'Error: {}'.format(e))
            df = None
        except ValueError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe.'
                'Error: {}'.format(e))
            df = None

        # generate vendor stats
        module_logger.info(
            'Generating vendor breakdown section for '
            '{}.'.format(self.system.get()))
        self.reportDTxt.insert(tk.END, 'Vendor breakdown:\n', 'blue')
        if df is not None:
            if df.size > 0:
                stats = reports.create_stats(self.system.get(), df)
                self.reportDTxt.insert(tk.END, stats.to_string())
            elif df.size == 0:
                self.reportDTxt.insert(tk.END, 'Nothing to report.')
        else:
            self.reportDTxt.insert(tk.END, 'STATS PARSING ERROR\n')
        self.reportDTxt.insert(
            tk.END, '\n' + ('-' * 120) + '\n')

        # report duplicates
        module_logger.info(
            'Generating duplicate reports section for {}-{}.'.format(
                self.system.get(), self.library.get()))
        self.reportDTxt.insert(tk.END, 'Duplicates report:\n', 'blue')
        if df is not None:
            dups = reports.report_dups(
                self.system.get(), self.library.get(), df)
            if dups.size == 0:
                self.reportDTxt.insert(tk.END, 'All clear\n')
            else:
                self.reportDTxt.insert(tk.END, dups.to_string() + '\n')
        else:
            self.reportDTxt.insert(
                tk.END, 'DUPLICATE REPORT PARSING ERROR\n')
        self.reportDTxt.insert(
            tk.END, '\n' + ('-' * 120) + '\n')

        # report callNo issues
        module_logger.info(
            'Generating call number issues section.')
        self.reportDTxt.insert(tk.END, 'Call number issues:\n', 'blue')
        if df is not None:
            callNos = reports.report_callNo_issues(df)
            if callNos.size == 0:
                self.reportDTxt.insert(tk.END, 'All clear\n')
            else:
                self.reportDTxt.insert(tk.END, callNos.to_string() + '\n')
        else:
            self.reportDTxt.insert(
                tk.END, 'CALL NUMBER CONFLICTS PARSING ERROR\n')
        self.reportDTxt.insert(
            tk.END, '\n' + ('-' * 120) + '\n')

        # prevent edits
        self.reportDTxt['state'] = tk.DISABLED

    def create_detailed_report(self):
        # reset report
        self.reportBTxt.delete(1.0, tk.END)

        # create dataframe to be tabulated
        try:
            df = reports.shelf2dataframe(BATCH_STATS)
        except KeyError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe. '
                'Error: {}'.format(e))
            df = None
        except ValueError as e:
            module_logger.error(
                'Unable to map BATCH_STATS to dataframe.'
                'Error: {}'.format(e))
            df = None

        module_logger.info(
            'Generating detailed report for {}-{}'.format(
                self.system.get(), self.library.get()))
        if df is not None:
            df = reports.report_details(
                self.system.get(), self.library.get(), df)
            self.reportBTxt.insert(tk.END, df.to_string())
        else:
            self.reportBTxt.insert(tk.END, 'DETAILED REPORT PARSING ERROR')

        # prevent edits
        self.reportBTxt['state'] = tk.DISABLED

    def help(self):
        # add scrollbar
        help = overload_help.open_help('process_vendor_help.txt')
        help_popup = tk.Toplevel(background='white')
        help_popup.iconbitmap('./icons/help.ico')
        yscrollbar = tk.Scrollbar(help_popup, orient=tk.VERTICAL)
        yscrollbar.grid(
            row=0, column=1, rowspan=10, sticky='nsw', padx=2)
        helpTxt = tk.Text(
            help_popup,
            background='white',
            relief=tk.FLAT,
            yscrollcommand=yscrollbar.set)
        helpTxt.grid(
            row=0, column=0, sticky='snew', padx=10, pady=10)
        yscrollbar.config(command=helpTxt.yview)
        for line in help:
            helpTxt.insert(tk.END, line)
        helpTxt['state'] = tk.DISABLED

    def reset(self):
        self.validated.set('validation:')
        self.processed.set('processed:')
        self.archived.set('archived:')
        self.progbar['value'] = 0

    def set_logo(self):
        # change logo
        if self.system.get() == 'NYPL':
            self.logoDsp.configure(image=self.nyplLogo)
            self.logoDsp.image = self.nyplLogo
        elif self.system.get() == 'BPL':
            self.logoDsp.configure(image=self.bplLogo)
            self.logoDsp.image = self.bplLogo

    def system_observer(self, *args):
        user_data = shelve.open(USER_DATA)
        conns_display = []
        # self.target_name.set('')
        if self.system.get() == 'BPL':
            # display only relevant connections
            if 'Z3950s' in user_data:
                for conn, params in user_data['Z3950s'].iteritems():
                    if params['library'] == 'BPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')
            if 'SierraAPIs' in user_data:
                for conn, params in user_data['SierraAPIs'].iteritems():
                    if params['library'] == 'BPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')

            # disable unwanted widgets
            self.library.set('')
            self.libraryCbx['state'] = 'disabled'
            self.agent.set('cataloging')
            self.agentCbx['state'] = 'disabled'

        elif self.system.get() == 'NYPL':
            # display only relevant connections
            if 'Z3950s' in user_data:
                for conn, params in user_data['Z3950s'].iteritems():
                    if params['library'] == 'NYPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')
            if 'SierraAPIs' in user_data:
                for conn, params in user_data['SierraAPIs'].iteritems():
                    if params['library'] == 'NYPL':
                        conns_display.append(
                            conn + ' (' + params['method'] + ')')
            if 'PlatformAPIs' in user_data:
                for conn, params in user_data['PlatformAPIs'].iteritems():
                    conns_display.append(
                        conn + ' (' + params['method'] + ')')
            self.libraryCbx['state'] = '!disabled'
            self.libraryCbx['state'] = 'readonly'
            self.agentCbx['state'] = '!disabled'
            self.agentCbx['state'] = 'readonly'

        # change log
        self.set_logo()

        # empty comobox selected target name if not on the list for the
        # system
        if self.target_name.get() not in conns_display:
            self.target_name.set('')
        # set list for drop down values
        self.query_targetCbx['values'] = conns_display
        self.query_targetCbx['state'] = 'readonly'
        user_data.close()

    def agent_observer(self, *args):
        if self.agent.get() == 'cataloging':
            self.templateCbx.set('')
            self.templateCbx['state'] = 'disabled'
        else:
            self.templateCbx['state'] = '!disabled'
            self.templateCbx['state'] = 'readonly'

    def observer(self, *args):
        if self.activeW.get() == 'ProcessVendorFiles':
            # reset values
            self.file_count.set('0 files(s) selected:')
            self.validated.set('validation:')
            self.processed.set('processed:')
            self.archived.set('archived:')
            self.selected_filesEnt['state'] = '!readonly'
            self.selected_filesEnt.delete(0, tk.END)
            self.selected_filesEnt['state'] = 'readonly'
            self.systemCbx['values'] = ['BPL', 'NYPL']
            self.systemCbx['state'] = 'readonly'
            self.libraryCbx['values'] = ['branches', 'research']
            self.libraryCbx['state'] = 'readonly'
            self.agentCbx['values'] = [
                'cataloging', 'selection', 'acquisition']
            self.agentCbx['state'] = 'readonly'

            # default database target
            user_data = shelve.open(USER_DATA)

            if 'pvr_default_target' in user_data:
                self.target_name.set(
                    '{} ({})'.format(
                        user_data['pvr_default_target']['target'],
                        user_data['pvr_default_target']['method']))
                self.target = user_data['pvr_default_target']

            # set default validation
            if 'pvr_marcval' in user_data:
                self.marcVal.set(user_data['pvr_marcval'])
            if 'pvr_locval' in user_data:
                self.locVal.set(user_data['pvr_locval'])
            if 'pvr_default_save_dir' in user_data[
                    'paths']:
                self.last_directory = user_data[
                    'paths']['pvr_default_save_dir']
                self.createToolTip(
                    self.default_directoryCbtn,
                    self.last_directory)
                self.last_directory_check.set(1)

            if 'pvr_system' in user_data:
                self.system.set(user_data['pvr_system'])
            if 'pvr_library' in user_data:
                self.library.set(user_data['pvr_library'])
            if 'pvr_agent' in user_data:
                self.agent.set(user_data['pvr_agent'])
            if 'pvr_template' in user_data:
                self.template.set(user_data['pvr_template'])
            user_data.close()

import os
import re
import uuid
#from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.ar import ARInvoiceTransaksi
from osipkd.models.ak import Jurnal, JurnalItem, Rekening, Sap, RekeningSap, JV_TYPE
from osipkd.models.pemda import (Unit)

#from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem

from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews


SESS_ADD_FAILED = 'Tambah ar-invoice-transaksi gagal'
SESS_EDIT_FAILED = 'Edit ar-invoice-transaksi gagal'

def deferred_sumber_id(node, kw):
    values = kw.get('sumber_id', [])
    return widget.SelectWidget(values=values)

SUMBER_ID = (
    (1, 'Manual'),
    (2, 'PBB'),
    (3, 'BPHTB'),
    (4, 'PADL'))


@colander.deferred
def deferred_unit_kd(node, kw):
    def validate_unit_kd(node, value):
        request = kw.get('request')
        unit_kd = request.session['unit_kd']
        if value != unit_kd:
            raise ValueError('Kode Error ')
    return validate_csrf

class AddSchema(colander.Schema):
    unit_kd_widget = widget.AutocompleteInputWidget(
            values = '/unit/headofkode/act',
            min_length=1)

    unit_nm_widget = widget.AutocompleteInputWidget(
            values = '/unit/headofnama/act',
            min_length=1)


    rekening_nm_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ak/rekening/headofnama/act',
            min_length=1)

    rekening_kd_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ak/rekening/headofkode/act',
            min_length=1)

    unit_id  = colander.SchemaNode(
                    colander.Integer(),
                    #widget = widget.HiddenWidget,
                    oid='unit_id',
                    title="SKPD")

    unit_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_kd',
                    title="SKPD",
                    widget = unit_kd_widget)

    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_nm',
                    title="SKPD",
                    widget = unit_nm_widget)


    rekening_id  = colander.SchemaNode(
                    colander.Integer(),
                    #widget = widget.HiddenWidget,
                    oid='rekening_id')
    kode  = colander.SchemaNode(
                    colander.String(),
                    widget = rekening_kd_widget,
                    oid='kode',
                    title='Rekening',
                    #javascript='test'
                    )

    nama = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=128),
                    widget = rekening_nm_widget,
                    oid = 'nama')
    ref_kode = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    title = "Referensi"
                    )
    ref_nama = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=64),
                    )

    tanggal = colander.SchemaNode(
                colander.Date(),
                widget = widget.DateInputWidget(),
                )

    amount = colander.SchemaNode(
                    colander.Integer(),
                    widget = widget.MoneyInputWidget(
                                      size=20, options={'allowZero':True, 'precision':0}),
                    #validator=colander.Length(max=32),
                    default = 0,
                    title = "Nilai"
                    )

    sumber_id  =  colander.SchemaNode(
                    colander.String(),
                    widget=widget.SelectWidget(values=SUMBER_ID),
                    title = "Sumber") # deferred_source_type)
    ############## DI DROP DULU
    kecamatan_kd = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    missing=colander.drop)
    kecamatan_nm = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=64),
                    missing=colander.drop)

    kelurahan_kd = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    missing=colander.drop
                    )
    kelurahan_nm = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=64),
                    missing=colander.drop)
    is_kota  = colander.SchemaNode(
                    colander.Boolean(),
                    missing = colander.drop
                    ) # deferred_source_type)

    disabled = colander.SchemaNode(
                    colander.Boolean(),
                    missing = colander.drop
                    ) # deferred_source_type)

class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))

class view_ar_invoice_transaksi(BaseViews):
    ########
    # List #
    ########
    @view_config(route_name='ar-invoice-transaksi', renderer='templates/ar-invoice-transaksi/list.pt',
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        row = {}
        row['kegiatan_kd']='0.00.00.10'
        row['kegiatan_nm']='PENDAPATAN'
        return dict(project='EIS', row=row)

    ##########
    # Action #
    ##########
    @view_config(route_name='ar-invoice-transaksi-act', renderer='json',
                 permission='read')
    def view_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('units.kode'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('ref_kode'))
            columns.append(ColumnDT('ref_nama'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('posted'))
            print '--------------------->', ses['unit_id'], ses['tanggal'], ses['tahun']
            query = DBSession.query(ARInvoiceTransaksi).filter(ARInvoiceTransaksi.tahun==ses['tahun'],
                      ARInvoiceTransaksi.unit_id==ses['unit_id'],
                      ARInvoiceTransaksi.tanggal == ses['tanggal'])
            rowTable = DataTables(req, ARInvoiceTransaksi, query, columns)
            return rowTable.output_result()

    #######
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(ARInvoiceTransaksi).filter_by(id=uid)
            row = q.first()
        else:
            row = None

    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(sumber_id=SUMBER_ID)
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))

    def save(self, values, user, row=None):
        if not row:
            row = ARInvoiceTransaksi()
            row.created    = datetime.now()
            row.create_uid = user.id
        row.from_dict(values)
        row.updated    = datetime.now()
        row.update_uid = user.id
        tanggal    = datetime.strptime(values['tanggal'], '%Y-%m-%d')
        row.tahun  = tanggal.year
        row.bulan  = tanggal.month
        row.hari   = tanggal.day
        row.minggu = tanggal.isocalendar()[1]
        row.disable   = 'disable' in values and values['disable'] and 1 or 0
        row.is_kota   = 'is_kota' in values and values['is_kota'] and 1 or 0

        DBSession.add(row)
        DBSession.flush()
        print '-----------------------------------------------------------------'
        #DBSession.commit()
        return row

    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        values['amount'] =  int(re.sub("[^0-9]", "", values['amount']))
        row = self.save(values, self.request.user, row)
        self.request.session.flash('Penetapan / Tagihan sudah disimpan.')

    def route_list(self):
        return HTTPFound(location=self.request.route_url('ar-invoice-transaksi') )

    def session_failed(self, session_name):

        #r = dict(form=self.session[session_name])
        del self.session[session_name]
        #return r

    @view_config(route_name='ar-invoice-transaksi-add', renderer='templates/ar-invoice-transaksi/add.pt',
                 permission='add')
    def view_add(self):
        req = self.request
        ses = self.session

        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    #req.session[SESS_ADD_FAILED] = e.render()
                    #form.set_appstruct(rowd)
                    return dict(form=form)
                    #return HTTPFound(location=req.route_url('ar-invoice-transaksi-add'))
                self.save_request(dict(controls))
            return self.route_list()
        elif SESS_ADD_FAILED in req.session:
            return dict(form=form)
        rowd={}
        rowd['unit_id']     = ses['unit_id']
        rowd['unit_nm']     = ses['unit_nm']
        rowd['unit_kd']     = ses['unit_kd']
        form.set_appstruct(rowd)
        return dict(form=form)


    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(ARInvoiceTransaksi).filter_by(id=self.request.matchdict['id'])

    def id_not_found(self):
        msg = 'Penetapan / Tagihan ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='ar-invoice-transaksi-edit', renderer='templates/ar-invoice-transaksi/add.pt',
                 permission='edit')
    def view_edit(self):
        request = self.request
        row     = self.query_id().first()

        if not row:
            return self.id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()

        form = self.get_form(EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                self.save_request(dict(controls), row)
            return self.route_list()
        #values = row.to_dict()
        rowd={}
        rowd['id']          = row.id
        rowd['unit_id']     = row.unit_id
        rowd['unit_nm']     = row.units.nama
        rowd['unit_kd']     = row.units.kode
        rowd['rekening_id'] = row.rekening_id
        rowd['kode']        = row.kode
        rowd['nama']        = row.nama
        rowd['ref_kode']    = row.ref_kode
        rowd['ref_nama']    = row.ref_nama
        rowd['tanggal']    = row.tanggal
        rowd['amount']     = row.amount
        rowd['kecamatan_kd']    = row.kecamatan_kd
        rowd['kecamatan_nm']    = row.kecamatan_nm
        rowd['kelurahan_kd']    = row.kelurahan_kd
        rowd['kelurahan_nm']    = row.kelurahan_nm
        rowd['is_kota']         = row.is_kota
        rowd['disabled']    = row.disabled
        rowd['sumber_id']    = row.sumber_id
        form.set_appstruct(rowd)
        return dict(form=form)

    ##########
    # Delete #
    ##########
    @view_config(route_name='ar-invoice-transaksi-delete', renderer='json',
                 permission='delete')
    def view_del(self):
        request = self.request
        q = self.query_id()
        row = q.first()

        if not row:
            return self.id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()

        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'Penetapan / Tagihan ID %d %s sudah dihapus.' % (row.id, row.nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'Penetapan / Tagihan ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())

    ###########
    # Posting #
    ###########
    @view_config(route_name='ar-invoice-transaksi-posting', renderer='json',
                 permission='posting')
    def view_posting(self):
        request = self.request
        row     = self.query_id().first()
        if not row:
            return {'success':False, 'msg':'Data tidak ditemukan'}
        if not row.amount:
            return {'success':False, 'msg':'Posting dibatalkan Nilai Transaksi = 0'}
            
        if row.posted:
            return {'success':False, 'msg':'Data sudah di posting'}
 
        #Tambah ke Jurnal SKPD
        jurnal = Jurnal()
        jurnal.tahun_id      = self.session['tahun']
        jurnal.unit_id       = self.session['unit_id']
        jurnal.nama          = "Jurnal Penetapan/Tagihan %s" % row.ref_nama
        jurnal.notes         = row.ref_nama
        jurnal.periode       = ARInvoiceTransaksi.get_periode(row.id)
        jurnal.posted        = 0
        jurnal.disabled      = 0
        jurnal.is_skpd       = 1
        jurnal.jv_type       = 7
        jurnal.source        = "ar_invoice_item"
        jurnal.source_no     = row.id
        jurnal.source_id     = row.id
        jurnal.tgl_source    = row.tanggal
        jurnal.tanggal       = datetime.now()
        jurnal.tgl_transaksi = row.tanggal 

        if not jurnal.kode:
            no_urut  = Jurnal.get_norut(jurnal.tahun_id, jurnal.unit_id)+1
            jurnal.kode = "{tahun}-{is_skpd}-{unit_kd}-{tipe}-{no_urut}".format(
                           tahun   = self.session['tahun'],
                           is_skpd = 1, 
                           unit_kd = self.session['unit_kd'], 
                           tipe    = JV_TYPE[jurnal.jv_type], 
                           no_urut = str(no_urut).rjust(5,'0'))
            #               
        DBSession.add(jurnal)
        DBSession.flush()

        #Tambah ke Item Jurnal SKPD
        ar_items = DBSession.query(ARInvoiceTransaksi.rekening_id,
                               ARInvoiceTransaksi.amount,
                               ARInvoiceTransaksi.tanggal,
                               RekeningSap.db_lo_sap_id,
                               RekeningSap.kr_lo_sap_id).\
                        filter(ARInvoiceTransaksi.id==row.id,
                               ARInvoiceTransaksi.rekening_id==RekeningSap.rekening_id).all()
                               
        if not ar_items:
            return {'success':False, 'msg':'Periksa ulang mapping SAP rekening'}
            
        #add debet item
        for ar_item in ar_items:
            ji = JurnalItem()
            ji.jurnal_id   = jurnal.id
            #ji.kegiatan_sub_id = row.kegiatan_sub_id1
            ji.rekening_id  = ar_item.rekening_id
            ji.sap_id       = ar_item.db_lo_sap_id
            ji.amount       = ar_item.amount
            DBSession.add(ji)
            DBSession.flush()
        #add kredit item    
        for ar_item in ar_items:
            ji2 = JurnalItem()
            ji2.jurnal_id   = jurnal.id
            #ji.kegiatan_sub_id = row.kegiatan_sub_id1
            ji2.rekening_id  = ar_item.rekening_id
            ji2.sap_id       = ar_item.kr_lo_sap_id
            ji2.amount       = ar_item.amount*-1
            DBSession.add(ji2)
            DBSession.flush()
            
        row.posted=1
        DBSession.add(row)
        DBSession.flush()
        
        return {'success':True, 'msg':'Data berhasil di posting'}


    #############
    # UnPosting #
    #############
    def save_request3(self, row=None):
        row = ARInvoiceTransaksi()
        self.request.session.flash('Penetapan/Tagihan sudah di Un-Jurnal.')
        return row

    @view_config(route_name='ar-invoice-transaksi-unposting', renderer='templates/ar-invoice-transaksi/unposting.pt',
                 permission='unposting')
    def view_unposting(self):
        request = self.request
        row     = self.query_id().first()

        if not row:
            return id_not_found(request)
        if not row.posted:
            self.request.session.flash('Data tidak dapat di Un-Jurnal, karena belum dibuat jurnal.', 'error')
            return self.route_list()
        if row.disabled:
            self.request.session.flash('Data jurnal Penetapan/Tagihan sudah diposting.', 'error')
            return self.route_list()

        form = Form(colander.Schema(), buttons=('un-jurnal','cancel'))

        if request.POST:
            if 'un-jurnal' in request.POST:

                #Update status posted pada PIUTANG
                row.posted=0
                self.save_request3(row)

                r = DBSession.query(Jurnal.id).filter(Jurnal.source_no==row.ref_kode,Jurnal.source=='Penetapan').first()
                #Menghapus Item Jurnal
                DBSession.query(JurnalItem).filter(JurnalItem.jurnal_id==r).delete()
                DBSession.flush()

                #Menghapus PIUTANG yang sudah menjadi jurnal
                DBSession.query(Jurnal).filter(Jurnal.source_no==row.ref_kode,Jurnal.source=='Penetapan').delete()
                DBSession.flush()

            return self.route_list()
        return dict(row=row, form=form.render())

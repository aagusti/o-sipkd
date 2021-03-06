import os
import uuid
from osipkd.tools import row2dict, xls_reader
from datetime import datetime
from sqlalchemy import not_, func
from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
import colander
from deform import (Form, widget, ValidationFailure, )
from osipkd.models import DBSession
from osipkd.models.ar import ARPaymentItem
from osipkd.models.pemda import Unit
from osipkd.models.ak import Rekening, Sap, RekeningSap
from osipkd.models.ak import Jurnal, JurnalItem
from osipkd.models.ag import Kegiatan, KegiatanSub, KegiatanItem
    
from datatables import ColumnDT, DataTables
from osipkd.views.base_view import BaseViews
    

SESS_ADD_FAILED = 'Tambah ar-payment-item gagal'
SESS_EDIT_FAILED = 'Edit ar-payment-item gagal'

def deferred_sumber_id(node, kw):
    values = kw.get('sumber_id', [])
    return widget.SelectWidget(values=values)
    
SUMBER_ID = (
    (1, 'Manual'),
    (2, 'PBB'),
    (3, 'BPHTB'),
    (4, 'PADL'))

def deferred_jenis(node, kw):
    values = kw.get('jenis', [])
    return widget.SelectWidget(values=values)
    
JENIS = (
    (1, 'Piutang'), 
    (2, 'Non Piutang'))
    
class AddSchema(colander.Schema):
    unit_kd_widget = widget.AutocompleteInputWidget(
            values = '/unit/headofkode/act',
            min_length=1)
  
    unit_nm_widget = widget.AutocompleteInputWidget(
            values = '/unit/act/headofnama',
            min_length=1)
            
                    
    kegiatan_nm_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ag-kegiatan-sub/headofnama/act',
            min_length=1)
  
    kegiatan_kd_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ag-kegiatan-sub/headofkode/act',
            min_length=1)

    rekening_nm_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ak/rekening/headofnama4/act',
            min_length=1)
  
    rekening_kd_widget = widget.AutocompleteInputWidget(
            size=60,
            values = '/ak/rekening/headofkode4/act',
            min_length=1,
            )
            
    unit_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='unit_id',
                    title="SKPD")

    unit_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_kd',
                    title="SKPD",
                    widget = unit_kd_widget,)

    unit_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='unit_nm',
                    title="SKPD",
                    widget = unit_nm_widget)

    """kegiatan_sub_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='kegiatan_sub_id',
                    title="SKPD")

    kegiatan_sub_kd  = colander.SchemaNode(
                    colander.String(),
                    oid='kegiatan_sub_kd',
                    title="Kegiatan",
                    widget = kegiatan_kd_widget,)

    kegiatan_sub_nm  = colander.SchemaNode(
                    colander.String(),
                    oid='kegiatan_sub_nm',
                    widget = kegiatan_nm_widget)
    """
    rekening_id  = colander.SchemaNode(
                    colander.Integer(),
                    oid='rekening_id')
    kode  = colander.SchemaNode(
                    colander.String(),
                    widget = rekening_kd_widget,                    
                    oid='kode',
                    title='Rekening',
                    )
    nama = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=128),
                    widget = rekening_nm_widget,
                    oid = 'nama')
    ref_kode = colander.SchemaNode(
                    colander.String(),
                    missing=colander.drop,
                    title = "No. Bukti"
                    )
    ref_nama = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=64),
                    missing = colander.drop,
                    title = "Uraian"
                    )
    tanggal = colander.SchemaNode(
                colander.Date(),
                )
    amount = colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    default = 0,
                    title = "Nilai"
                    )
    sumber_id  =  colander.SchemaNode(
                    colander.String(),
                    validator=colander.Length(max=32),
                    widget=widget.SelectWidget(values=SUMBER_ID),
                    title = "Sumber") 
                    # deferred_source_type)
    bud_uid    = colander.SchemaNode(
                          colander.Integer(),
                          oid="bud_uid",
                          missing=colander.drop,
                          title="Bendahara") 
    bud_nip    = colander.SchemaNode(
                          colander.String(),
                          oid="bud_nip",
                          missing=colander.drop,
                          title="Bendahara")                          
    bud_nama   = colander.SchemaNode(
                          colander.String(),
                          oid="bud_nama",
                          missing=colander.drop)
    
    jenis      =  colander.SchemaNode(
                    colander.String(),
                    widget=widget.SelectWidget(values=JENIS),
                    oid="jenis",
                    title = "Jenis",) 
                    
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
            
class view_ar_tbp_item(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ar-tbp', renderer='templates/ar-tbp/list.pt',
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        return dict(project='EIS')
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ar-tbp-act', renderer='json',
                 permission='read')
    def ar_tbp_item_act(self):
        ses = self.request.session
        req = self.request
        params   = req.params
        url_dict = req.matchdict
        
        kegiatan_sub_id = 'kegiatan_sub_id' in params and params['kegiatan_sub_id'] or 0
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('ref_kode'))
            columns.append(ColumnDT('ref_nama'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('posted'))   
            columns.append(ColumnDT('posted1'))   
            query = DBSession.query(ARPaymentItem).filter(ARPaymentItem.tahun == ses['tahun'],
                                                          ARPaymentItem.unit_id == ses['unit_id'],
                                                          ARPaymentItem.tanggal == ses['tanggal']
                                                          )
            rowTable = DataTables(req, ARPaymentItem, query, columns)
            return rowTable.output_result()
        
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
                # a = form.validate(controls)
                # b = a['ref_kode']
                # c = "%s" % b
                # cek = DBSession.query(ARPaymentItem).filter(ARPaymentItem.ref_kode==c).first()
                # if cek:
                    # kode1 = DBSession.query(ARPaymentItem).filter(ARPaymentItem.id==uid).first()
                    # d     = kode1.ref_kode
                    # if d!=c:
                        # self.request.session.flash('Nomor Bukti sudah ada', 'error')
                        # return HTTPFound(location=request.route_url('ar-tbp-edit',id=row.id))
        pass
        #print '--->',value['bud_uid']
        #if 'id' in form.request.matchdict:
        #    id = form.request.matchdict['id']
        #    q = DBSession.query(ARPaymentItem).filter_by(id=id)
        #    row = q.first()
        #else:
        #    row = None
                
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind(sumber_id=SUMBER_ID,jenis=JENIS)
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = ARPaymentItem()
            row.created    = datetime.now()
            row.create_uid = user.id
        if 'bud_uid' in values and not values['bud_uid']:
            values.pop('bud_uid',None)
        row.from_dict(values)
        row.updated    = datetime.now()
        row.update_uid = user.id
        tanggal     = datetime.strptime(values['tanggal'], '%Y-%m-%d')
        row.tahun   = tanggal.year
        row.bulan   = tanggal.month
        row.hari    = tanggal.day
        row.minggu  = tanggal.isocalendar()[1]
        row.disabled = 'disabled' in values and values['disabled'] and 1 or 0
        row.is_kota  = 'is_kota'  in values and values['is_kota']  and 1 or 0
        row.posted1  = 'posted1'  in values and values['posted1']  and 1 or 0
        
        tahun    = self.session['tahun']
        unit_id  = self.session['unit_id']
        if not row.no_urut:
            row.no_urut = ARPaymentItem.max_no_urut(tahun,unit_id)+1;
            
        if not row.ref_kode:
            tahun        = self.session['tahun']
            unit_kd      = self.session['unit_kd']
            unit_id      = self.session['unit_id']
            #no_urut      = ARPaymentItem.get_norut(tahun, unit_id)+1
            no_urut      = row.no_urut
            no           = "0000%d" % no_urut
            nomor        = no[-5:]
            row.ref_kode = "%s" % tahun + "-%s" % unit_kd + "-%s" % nomor
        
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        row = self.save(values, self.request.user, row)
        self.request.session.flash('TBP sudah disimpan.')
            
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ar-tbp') )
        
    def session_failed(self, session_name):
        del self.session[session_name]
        
    @view_config(route_name='ar-tbp-add', renderer='templates/ar-tbp/add.pt',
                 permission='add')
    def view_ar_tbp_item_add(self):
        req = self.request
        ses = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                controls_dicted = dict(controls)

                #Cek Kode Sama ato tidak
                if not controls_dicted['ref_kode']=='':
                    a = form.validate(controls)
                    b = a['ref_kode']
                    c = "%s" % b
                    cek  = DBSession.query(ARPaymentItem).filter(ARPaymentItem.ref_kode==c).first()
                    if cek :
                        self.request.session.flash('Nomor Bukti sudah ada.', 'error')
                        return HTTPFound(location=self.request.route_url('ar-tbp-add'))

                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                row = self.save_request(controls_dicted)
                #return HTTPFound(location=req.route_url('ar-tbp-edit',id=row.id))
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
        return DBSession.query(ARPaymentItem).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'TBP ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()

    @view_config(route_name='ar-tbp-edit', renderer='templates/ar-tbp/add.pt',
                 permission='edit')
    def view_ar_tbp_item_edit(self):
        request = self.request
        row     = self.query_id().first()
        uid     = row.id
        kode    = row.ref_kode
        
        if not row:
            return id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()
            
        form = self.get_form(EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                #Cek Kode Sama ato tidak
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)
                    #request.session[SESS_EDIT_FAILED] = e.render()               
                    #return HTTPFound(location=request.route_url('ar-payment-item-edit',
                    #                  id=row.id))
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        rowd = row.to_dict()
        rowd['unit_nm']     = row.units.nama
        rowd['unit_kd']     = row.units.kode
        rowd['bud_uid']     = 0 #rowd['bud_uid'] or rowd.pop('bud_uid', None)
        form.set_appstruct(rowd)
        return dict(form=form)

    ##########
    # Delete #
    ##########    
    @view_config(route_name='ar-tbp-delete', renderer='templates/ar-tbp/delete.pt',
                 permission='delete')
    def view_ar_tbp_item_delete(self):
        request = self.request
        q       = self.query_id()
        row     = q.first()
        
        if not row:
            return self.id_not_found(request)
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()
        if row.posted1:
            request.session.flash('Data sudah diposting rekap', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'TBP ID %d %s sudah dihapus.' % (row.id, row.ref_nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'TBP ID %d %s tidak dapat dihapus.' % (row.id, row.ref_nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row, form=form.render())

    ###########
    # Posting #
    ###########     
    def save_request2(self, row=None):
        row = ARPaymentItem()
        self.request.session.flash('TBP sudah diposting dan dibuat Jurnalnya.')
        return row
        
    @view_config(route_name='ar-tbp-posting', renderer='templates/ar-tbp/posting.pt',
                 permission='posting')
    def view_edit_posting(self):
        request = self.request
        row     = self.query_id().first()
        id_tbp  = row.id
        nama    = row.ref_nama
        kode    = row.ref_kode
        tanggal = row.tanggal
        
        if not row:
            return id_not_found(request)
        if not row.amount:
           request.session.flash('Data tidak dapat diposting, karena bernilai 0.', 'error')
           return route_list()
        if row.posted:
            request.session.flash('Data sudah diposting', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('posting','cancel'))
        
        if request.POST:
            if 'posting' in request.POST: 
                #Update posted pada TBP
                row.posted=1
                self.save_request2(row)
                
                #Tambah ke Jurnal SKPD
                periode = ARPaymentItem.get_periode(row.id)
                
                row = AkJurnal()
                row.created    = datetime.now()
                row.create_uid = self.request.user.id
                row.updated    = datetime.now()
                row.update_uid = self.request.user.id
                row.tahun_id   = self.session['tahun']
                row.unit_id    = self.session['unit_id']
                row.nama       = "Diterima TBP %s" % nama
                row.notes      = nama
                row.periode    = periode
                row.posted     = 0
                row.disabled   = 0
                row.is_skpd    = 0
                row.jv_type    = 1
                row.source     = "TBP"
                row.source_no  = kode
                row.tgl_source = tanggal
                row.tanggal    = datetime.now()
                row.tgl_transaksi = datetime.now()
                
                if not row.kode:
                    tahun    = self.session['tahun']
                    unit_kd  = self.session['unit_kd']
                    is_skpd  = row.is_skpd
                    tipe     = AkJurnal.get_tipe(row.jv_type)
                    no_urut  = AkJurnal.get_norut(row.id)+1
                    no       = "0000%d" % no_urut
                    nomor    = no[-5:]     
                    row.kode = "%d" % tahun + "-%s" % is_skpd + "-%s" % unit_kd + "-%s" % tipe + "-%s" % nomor
                
                DBSession.add(row)
                DBSession.flush()
                
                jui   = row.id
                rows = DBSession.query(KegiatanItem.rekening_id.label('rekening_id1'),
                                       KegiatanItem.nama.label('nama1'),
                                       KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                       ARPaymentItem.amount.label('nilai1'),
                                       RekeningSap.db_lo_sap_id.label('sap1'),
                                       RekeningSap.db_lra_sap_id.label('sap2'),
                                       RekeningSap.neraca_sap_id.label('sap3'),
                                ).join(Rekening
                                ).outerjoin(KegiatanItem,RekeningSap,KegiatanSub,
                                ).filter(ARPaymentItem.id==id_tbp,
                                         ARPaymentItem.rekening_id==KegiatanItem.rekening_id,
                                         KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                         KegiatanItem.rekening_id==Rekening.id,
                                         RekeningSap.rekening_id==Rekening.id,
                                ).group_by(KegiatanItem.rekening_id.label('rekening_id1'),
                                           KegiatanItem.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           ARPaymentItem.amount.label('nilai1'),
                                           RekeningSap.db_lo_sap_id.label('sap1'),
                                           RekeningSap.db_lra_sap_id.label('sap2'),
                                           RekeningSap.neraca_sap_id.label('sap3'),
                                ).all()
                
                n=0
                for row in rows:
                    ji = AkJurnalItem()
                    
                    ji.ak_jurnal_id = "%d" % jui
                    ji.kegiatan_sub_id = row.kegiatan_sub_id1
                    ji.rekening_id  = row.rekening_id1
                    ji.sap_id       = 3862
                    ji.amount       = row.nilai1
                    ji.notes        = row.nama1
                    n = n + 1
                    
                    DBSession.add(ji)
                    DBSession.flush()
                
            return self.route_list()
        return dict(row=row, form=form.render()) 

    #############
    # UnPosting #
    #############   
    def save_request4(self, row=None):
        row = ARPaymentItem()
        self.request.session.flash('TBP sudah di UnPosting.')
        return row
        
    @view_config(route_name='ar-tbp-unposting', renderer='templates/ar-tbp/unposting.pt',
                 permission='unposting') 
    def view_edit_unposting(self):
        request = self.request
        row     = self.query_id().first()
        kode    = row.ref_kode
        
        if not row:
            return id_not_found(request)
        if not row.posted:
            request.session.flash('Data tidak dapat di Unposting, karena belum diposting.', 'error')
            return self.route_list()
        if row.disabled:
            request.session.flash('Data jurnal TBP sudah diposting.', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('unposting','cancel'))
        
        if request.POST:
            if 'unposting' in request.POST: 
            
                #Update status posted pada TBP
                row.posted=0
                self.save_request4(row)
                
                r = DBSession.query(AkJurnal.id).filter(AkJurnal.source_no==row.ref_kode).first()
                #Menghapus Item Jurnal
                DBSession.query(AkJurnalItem).filter(AkJurnalItem.ak_jurnal_id==r).delete()
                DBSession.flush()
                
                #Menghapus TBP yang sudah menjadi jurnal
                DBSession.query(AkJurnal).filter(AkJurnal.source_no==kode).delete()
                DBSession.flush()
                
            return self.route_list()
        return dict(row=row, form=form.render())    


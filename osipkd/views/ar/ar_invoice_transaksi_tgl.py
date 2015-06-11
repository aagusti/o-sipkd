import os
import uuid
import colander
import operator
from datetime import datetime
from sqlalchemy import not_, func
from sqlalchemy.sql.expression import bindparam, literal_column

from pyramid.view import (view_config,)
from pyramid.httpexceptions import ( HTTPFound, )
from deform import (Form, widget, ValidationFailure, )
from datatables import ColumnDT, DataTables

from osipkd.models import DBSession
from osipkd.models.ar import ARInvoiceTransaksi
from osipkd.models.ak import Jurnal, JurnalItem, Sap, RekeningSap
from osipkd.models.pemda import (Unit)
from osipkd.models.ak import(Rekening)
from osipkd.views.base_view import BaseViews
from osipkd.tools import BULANS    

class view_ar_invoice_item_tgl(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ar-invoice-transaksi-tgl', renderer='templates/ar-invoice-transaksi-tgl/list.pt',
                 permission='read')
    def view_list(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        row = {}
        row['kegiatan_kd']='0.00.00.10'
        row['kegiatan_nm']='PENDAPATAN'
        print sorted(BULANS.items(), key=operator.itemgetter(0))
        return dict(project='EIS', row=row, bulans=sorted(BULANS.items(), key=operator.itemgetter(0)))
        
    ##########                    
    # Action #
    ##########    
    @view_config(route_name='ar-invoice-transaksi-tgl-act', renderer='json',
                 permission='read')
    def ar_invoice_item_tgl_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('tanggal', filter=self._DTstrftime))
            columns.append(ColumnDT('amount',  filter=self._number_format))
            columns.append(ColumnDT('posted'))
            query = DBSession.query(ARInvoiceTransaksi.tahun, ARInvoiceTransaksi.tanggal, ARInvoiceTransaksi.kode,
                                    ARInvoiceTransaksi.nama, func.sum(ARInvoiceTransaksi.amount).label('amount'),
                                    literal_column("0").label('posted')).\
                              outerjoin(Rekening).\
                              group_by(ARInvoiceTransaksi.tahun, ARInvoiceTransaksi.tanggal, ARInvoiceTransaksi.kode,
                                    ARInvoiceTransaksi.nama).\
                              filter(ARInvoiceTransaksi.tahun==ses['tahun'],
                                        ARInvoiceTransaksi.bulan==ses['bulan'])
                                    
            rowTable = DataTables(req, ARInvoiceTransaksi, query, columns)
            return rowTable.output_result()
        
    ###########
    # Posting #
    ###########     
    def save_request2(self, row=None):
        row = ARInvoiceTransaksi()
        self.request.session.flash('Penetapan/Tagihan sudah diposting dan dibuat Jurnalnya.')
        return row
        
    @view_config(route_name='ar-invoice-transaksi-tgl-post', renderer='templates/ar-invoice-transaksi-tgl/posting.pt',
                 permission='posting')
    def view_edit_posting(self):
        request = self.request
        row     = self.query_id().first()
        id_inv  = row.id
        
        if not row:
            return id_not_found(request)
        if not row.amount:
            self.request.session.flash('Data tidak dapat di jurnal, karena bernilai 0.', 'error')
            return self.route_list()
        if row.posted:
            self.request.session.flash('Data sudah dibuat jurnal', 'error')
            return self.route_list()
            
        form = Form(colander.Schema(), buttons=('jurnal','cancel'))
        
        if request.POST:
            if 'jurnal' in request.POST: 
                #Update posted pada ARInvoice
                row.posted=1
                self.save_request2(row)
                
                #Tambah ke Jurnal SKPD
                nama    = row.ref_nama
                kode    = row.ref_kode
                tanggal = row.tanggal
                #tipe    = ARInvoice.get_tipe(row.id)
                periode = ARInvoiceTransaksi.get_periode(row.id)
                
                row = Jurnal()
                row.created    = datetime.now()
                row.create_uid = self.request.user.id
                row.updated    = datetime.now()
                row.update_uid = self.request.user.id
                row.tahun_id   = self.session['tahun']
                row.unit_id    = self.session['unit_id']
                row.nama       = "Diterima Penetapan/Tagihan %s" % nama
                row.notes      = nama
                row.periode    = periode
                row.posted     = 0
                row.disabled   = 0
                row.is_skpd    = 1
                row.jv_type    = 1
                row.source     = "Penetapan"
                row.source_no  = kode
                row.tgl_source = tanggal
                row.tanggal    = datetime.now()
                row.tgl_transaksi = datetime.now()
                
                if not row.kode:
                    tahun    = self.session['tahun']
                    unit_kd  = self.session['unit_kd']
                    is_skpd  = row.is_skpd
                    tipe     = Jurnal.get_tipe(row.jv_type)
                    no_urut  = Jurnal.get_norut(row.tahun_id,row.unit_id)+1
                    no       = "0000%d" % no_urut
                    nomor    = no[-5:]     
                    row.kode = "%d" % tahun + "-%s" % is_skpd + "-%s" % unit_kd + "-%s" % tipe + "-%s" % nomor
                
                DBSession.add(row)
                DBSession.flush()
                
                #Tambah ke Item Jurnal SKPD
                jui   = row.id
                rows = DBSession.query(ARInvoiceTransaksi.rekening_id.label('rekening_id1'),
                                       Sap.nama.label('nama1'),
                                       KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                       ARInvoiceTransaksi.amount.label('nilai1'),
                                       RekeningSap.db_lo_sap_id.label('sap1'),
                                       RekeningSap.kr_lo_sap_id.label('sap2'),
                                       Rekening.id.label('rek'),
                                ).join(Rekening
                                #).outerjoin(KegiatanSub, KegiatanItem, RekeningSap 
                                ).filter(ARInvoiceTransaksi.id==id_inv,
                                         ARInvoiceTransaksi.rekening_id==KegiatanItem.rekening_id,
                                         KegiatanItem.kegiatan_sub_id==KegiatanSub.id,
                                         KegiatanItem.rekening_id==RekeningSap.rekening_id,
                                         RekeningSap.rekening_id==Rekening.id,
                                         RekeningSap.kr_lo_sap_id==Sap.id
                                ).group_by(ARInvoiceTransaksi.rekening_id.label('rekening_id1'),
                                           Sap.nama.label('nama1'),
                                           KegiatanItem.kegiatan_sub_id.label('kegiatan_sub_id1'),
                                           ARInvoiceTransaksi.amount.label('nilai1'),
                                           RekeningSap.db_lo_sap_id.label('sap1'),
                                           RekeningSap.kr_lo_sap_id.label('sap2'),
                                           Rekening.id.label('rek'),
                                ).all()
                
                for row in rows:
                    ji = JurnalItem()
                    
                    ji.jurnal_id = "%d" % jui
                    ji.kegiatan_sub_id = row.kegiatan_sub_id1
                    ji.rekening_id  = row.rek
                    ji.sap_id       = row.sap1
                    ji.notes        = ""
                    ji.amount       = row.nilai1
                    
                    DBSession.add(ji)
                    DBSession.flush()
                
                n=0
                for row in rows:
                    ji2 = JurnalItem()
                    
                    ji2.jurnal_id = "%d" % jui
                    ji2.kegiatan_sub_id = row.kegiatan_sub_id1
                    ji2.rekening_id  = row.rek
                    ji2.sap_id       = row.sap2
                    n = row.nilai1
                    ji2.amount       = n * -1
                    ji2.notes        = ""
                    n = n + 1
                    
                    DBSession.add(ji2)
                    DBSession.flush()
                
            return self.route_list()
        return dict(row=row, form=form.render())    

    #############
    # UnPosting #
    #############   
    def save_request3(self, row=None):
        row = ARInvoiceTransaksi()
        self.request.session.flash('Penetapan/Tagihan sudah di Un-Jurnal.')
        return row
        
    @view_config(route_name='ar-invoice-transaksi-tgl-unpost', 
                 renderer='templates/ar-invoice-transaksi-tgl/unposting.pt',
                 permission='read') 
    def view_edit_unposting(self):
        request = self.request
        row     = self.query_id().first()
        
        if not row:
            return id_not_found(request)
        if not row.posted:
            self.request.session.flash('Data tidak dapat di Un-Jurnal, karena belum dibuat jurnal.', 
                                       'error')
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
                
                r = DBSession.query(Jurnal.id).filter(Jurnal.source_no==row.ref_kode,
                                                      Jurnal.source=='Penetapan').first()
                #Menghapus Item Jurnal
                DBSession.query(JurnalItem).filter(JurnalItem.jurnal_id==r).delete()
                DBSession.flush()
                    
                #Menghapus PIUTANG yang sudah menjadi jurnal
                DBSession.query(Jurnal).filter(Jurnal.source_no==row.ref_kode,
                                               Jurnal.source=='Penetapan').delete()
                DBSession.flush()
                
            return self.route_list()
        return dict(row=row, form=form.render())
            
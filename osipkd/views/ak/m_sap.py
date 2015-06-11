import os
import uuid
import colander

from datetime import datetime

from sqlalchemy import not_, func, or_
from sqlalchemy.sql.expression import and_

from ziggurat_foundations.models import groupfinder
from pyramid.view import (view_config,)
from pyramid.httpexceptions import (HTTPFound,)
from osipkd.views.base_view import BaseViews

from deform import (Form, widget,ValidationFailure,)
from datatables import ColumnDT, DataTables

from osipkd.tools import row2dict, xls_reader
from osipkd.models import (DBSession,)
from osipkd.models.ak import Sap, Rekening, RekeningSap
#from osipkd.models.apbd_anggaran import Kegiatan, KegiatanSub, KegiatanItem


SESS_ADD_FAILED = 'Tambah sap gagal'
SESS_EDIT_FAILED = 'Edit sap gagal'

rek_widget = widget.AutocompleteInputWidget(
        size=60,
        values = '/ak/sap/headofnama/act',
        min_length=1)

            
class AddSchema(colander.Schema):
    parent_id  = colander.SchemaNode(
                    colander.String(),
                    #widget = widget.HiddenWidget(),
                    missing = colander.drop,
                    oid = "parent_id"
                    )
    parent_nm = colander.SchemaNode(
                    colander.String(),
                    #widget = rek_widget,
                    missing = colander.drop,
                    oid = "parent_nm",
                    title = "Header"
                    )
    tahun = colander.SchemaNode(
                    colander.Integer(),
                    oid = "tahun",
                    title = "Tahun")
    kode = colander.SchemaNode(
                    colander.String(),
                    oid = "kode",
                    title = "Kode")
    nama = colander.SchemaNode(
                    colander.String(),
                    oid = "nama",
                    title = "Nama")
    disabled = colander.SchemaNode(
                    colander.Boolean())
                    
class EditSchema(AddSchema):
    id = colander.SchemaNode(colander.String(),
            missing=colander.drop,
            widget=widget.HiddenWidget(readonly=True))
            
class view_rekening(BaseViews):
    ########                    
    # List #
    ########    
    @view_config(route_name='ak-sap', renderer='templates/sap/list.pt',
                 permission='read')
    def view_list(self):
        return dict(project="osipkd")
        
    ##########                    
    # Action #
    ########## 
    def get_nama_dict(self, term, prefix=''):
        q = DBSession.query(Sap.id, Sap.kode, Sap.nama
                  ).filter(Sap.kode.ilike('%s%%' % prefix),
                           Sap.nama.ilike('%%%s%%' % term))
        rows = q.all()
        r = []
        for k in rows:
            d={}
            d['id']          = k[0]
            d['value']       = k[2]
            d['kode']        = k[1]
            d['nama']        = k[2]
            r.append(d)    
        return r
        
    @view_config(route_name='ak-sap-act', renderer='json',
                 permission='view')
    def gaji_sap_act(self):
        ses = self.request.session
        req = self.request
        params = req.params
        url_dict = req.matchdict
        if url_dict['act']=='grid':
            columns = []
            columns.append(ColumnDT('id'))
            columns.append(ColumnDT('kode'))
            columns.append(ColumnDT('nama'))
            columns.append(ColumnDT('level_id'))
            columns.append(ColumnDT('disabled'))
 
            query = DBSession.query(Sap)
            
            rowTable = DataTables(req, Sap, query, columns)
            return rowTable.output_result()
         
        elif url_dict['act']=='headofnama':
            term = 'term' in params and params['term'] or '' 
            return self.get_nama_dict(term)
            
        elif url_dict['act']=='headofkode1':
            #LO dan Neraca
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(or_(Sap.kode.ilike('8%%%s%%' % term),
                                   Sap.kode.ilike('9%%%s%%' % term),
                                   Sap.kode.ilike('1%%%s%%' % term))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
            
        elif url_dict['act']=='headofnama1':
            #LO dan Neraca
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(Sap.nama.ilike('%%%s%%' % term),
                               or_(Sap.kode.ilike('8%%'),
                                   Sap.kode.ilike('9%%'),
                                   Sap.kode.ilike('1%%'))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
        
        elif url_dict['act']=='headofkode11':
            #LRA
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(or_(Sap.kode.ilike('8%%%s%%' % term),
                                   Sap.kode.ilike('9%%%s%%' % term),
                                   Sap.kode.ilike('2%%%s%%' % term))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
            
        elif url_dict['act']=='headofnama11':
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(Sap.nama.ilike('%%%s%%' % term),
                               or_(Sap.kode.ilike('8%%'),
                                   Sap.kode.ilike('9%%'),
                                   Sap.kode.ilike('2%%'))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
                
        elif url_dict['act']=='headofkode2':
            #LRA
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(or_(Sap.kode.ilike('4%%'),
                                   Sap.kode.ilike('5%%'),
                                   Sap.kode.ilike('6%%'),
                                   Sap.kode.ilike('7%%'),
                                   Sap.kode.ilike('0%%'),
                                  ),
                               Sap.kode.ilike('%s%%' % term)
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)

            return r
            
        elif url_dict['act']=='headofnama2':
            #APBD
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(Sap.nama.ilike('%%%s%%' % term),
                               or_(Sap.kode.ilike('4%%'),
                                   Sap.kode.ilike('5%%'),
                                   Sap.kode.ilike('6%%'),
                                   Sap.kode.ilike('7%%'),
                                   Sap.kode.ilike('0%%'))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            return r
            
        elif url_dict['act']=='headofkode3':
            #Neraca
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(or_(Sap.kode.ilike('1%%%s%%' % term),
                                   Sap.kode.ilike('2%%%s%%' % term),
                                   Sap.kode.ilike('3%%%s%%' % term))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)

            return r
            
        elif url_dict['act']=='headofnama3':
            #Neraca
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(Sap.nama.ilike('%%%s%%' % term),
                               or_(Sap.kode.ilike('1%%'),
                                   Sap.kode.ilike('2%%'),
                                   Sap.kode.ilike('3%%'))
                      )
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            print '****----****',r                
            return r
        
        elif url_dict['act']=='headofkode4':
            term = 'term' in params and params['term'] or ''
            rekening_id = 'rekening_id' in params and params['rekening_id'] or 0
                        
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(RekeningSap.rekening_id   == rekening_id,
                               RekeningSap.rekening_id   == Rekening.id,
                               RekeningSap.db_lo_sap_id  == Sap.id,
                               RekeningSap.kr_lo_sap_id  == Sap.id,
                               RekeningSap.db_lra_sap_id == Sap.id,
                               RekeningSap.kr_lra_sap_id == Sap.id,
                               RekeningSap.neraca_sap_id == Sap.id,
                               Sap.kode.ilike('%%%s%%' % term))
            rows = q.all()
            
            if not rows:
                return {'success':False, 'msg':'SAP tidak ditemukan'}
                
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            print '****----****',r                
            return r
        
        elif url_dict['act']=='headofnama4':
            term = 'term' in params and params['term'] or ''
            rekening_id = 'rekening_id' in params and params['rekening_id'] or 0
                        
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(RekeningSap.rekening_id   == rekening_id,
                               RekeningSap.rekening_id   == Rekening.id,
                               RekeningSap.db_lo_sap_id  == Sap.id,
                               RekeningSap.kr_lo_sap_id  == Sap.id,
                               RekeningSap.db_lra_sap_id == Sap.id,
                               RekeningSap.kr_lra_sap_id == Sap.id,
                               RekeningSap.neraca_sap_id == Sap.id,
                               Sap.nama.ilike('%%%s%%' % term))
            rows = q.all()
            
            if not rows:
                return {'success':False, 'msg':'SAP tidak ditemukan'}
                
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            print '****----****',r                
            return r
        
        elif url_dict['act']=='headofkode12':
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(Sap.kode.ilike('%%%s%%' % term))
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[1]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            print '****----****',r                
            return r
        
        elif url_dict['act']=='headofnama12':
            term = 'term' in params and params['term'] or ''            
            q = DBSession.query(Sap.id, 
                                Sap.kode, 
                                Sap.nama, 
                      ).filter(Sap.nama.ilike('%%%s%%' % term))
            rows = q.all()
            r = []
            for k in rows:
                d={}
                d['id']          = k[0]
                d['value']       = k[2]
                d['kode']        = k[1]
                d['nama']        = k[2]
                r.append(d)
            print '****----****',r                
            return r
            
    #######    
    # Add #
    #######
    def form_validator(self, form, value):
        if 'id' in form.request.matchdict:
            uid = form.request.matchdict['id']
            q = DBSession.query(Sap).filter_by(id=uid)
            sap = q.first()
        else:
            sap = None
            
    def get_form(self, class_form, row=None):
        schema = class_form(validator=self.form_validator)
        schema = schema.bind()
        schema.request = self.request
        if row:
          schema.deserialize(row)
        return Form(schema, buttons=('simpan','batal'))
        
    def save(self, values, user, row=None):
        if not row:
            row = Sap()
            row.created = datetime.now()
            row.create_uid = user.id
        row.from_dict(values)
        row.updated = datetime.now()
        row.update_uid = user.id
        row.disabled = 'disabled' in values and values['disabled'] and 1 or 0
        DBSession.add(row)
        DBSession.flush()
        return row
        
    def save_request(self, values, row=None):
        if 'id' in self.request.matchdict:
            values['id'] = self.request.matchdict['id']
        if 'parent_id' in values and values['parent_id']:
            values['level_id'] = Sap.get_next_level(values['parent_id'])
        else:
            values['level_id'] = 1
            values['parent_id'] = None
        row = self.save(values, self.request.user, row)
        self.request.session.flash('Rekening SAP sudah disimpan.')
        
    def route_list(self):
        return HTTPFound(location=self.request.route_url('ak-sap'))
        
    def session_failed(self, session_name):
        r = dict(form=self.session[session_name])
        del self.session[session_name]
        return r
        
    @view_config(route_name='ak-sap-add', renderer='templates/sap/add.pt',
                 permission='add')
    def view_sap_add(self):
        req = self.request
        ses = self.session
        form = self.get_form(AddSchema)
        if req.POST:
            if 'simpan' in req.POST:
                controls = req.POST.items()
                controls_dicted = dict(controls)
                
                #Cek Kode Sama ato tidak
                if not controls_dicted['kode']=='':
                    a = form.validate(controls)
                    b = a['kode']
                    c = "%s" % b
                    cek  = DBSession.query(Sap).filter(Sap.kode==c).first()
                    if cek :
                        self.request.session.flash('Kode sudah ada.', 'error')
                        return HTTPFound(location=self.request.route_url('ak-sap-add'))
                        
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    return dict(form=form)              
                    return HTTPFound(location=req.route_url('ak-sap-add'))
                self.save_request(dict(controls))
            return self.route_list()
        elif SESS_ADD_FAILED in req.session:
            return self.session_failed(SESS_ADD_FAILED)
        return dict(form=form)
        
    ########
    # Edit #
    ########
    def query_id(self):
        return DBSession.query(Sap).filter_by(id=self.request.matchdict['id'])
        
    def id_not_found(self):    
        msg = 'sap ID %s Tidak Ditemukan.' % self.request.matchdict['id']
        request.session.flash(msg, 'error')
        return route_list()
        
    @view_config(route_name='ak-sap-edit', renderer='templates/sap/add.pt',
                 permission='edit')
    def view_rekening_edit(self):
        request = self.request
        row     = self.query_id().first()
        uid     = row.id
        kode    = row.kode
        
        if not row:
            return id_not_found(request)
            
        form = self.get_form(EditSchema)
        if request.POST:
            if 'simpan' in request.POST:
                controls = request.POST.items()
                
                #Cek Kode Sama ato tidak
                a = form.validate(controls)
                b = a['kode']
                c = "%s" % b
                cek = DBSession.query(Sap).filter(Sap.kode==c).first()
                if cek:
                    kode1 = DBSession.query(Sap).filter(Sap.id==uid).first()
                    d     = kode1.kode
                    if d!=c:
                        self.request.session.flash('Data sudah ada', 'error')
                        return HTTPFound(location=request.route_url('ak-sap-edit',id=row.id))
                        
                try:
                    c = form.validate(controls)
                except ValidationFailure, e:
                    request.session[SESS_EDIT_FAILED] = e.render()               
                    return HTTPFound(location=request.route_url('ak-sap-edit',
                                      id=row.id))
                self.save_request(dict(controls), row)
            return self.route_list()
        elif SESS_EDIT_FAILED in request.session:
            return self.session_failed(SESS_EDIT_FAILED)
        values = row.to_dict()
        values['parent_nm']= row.parent.nama if values['parent_id'] else ""
        form.set_appstruct(values)
        return dict(form=form)
        
    ##########
    # Delete #
    ##########    
    @view_config(route_name='ak-sap-delete', renderer='templates/sap/delete.pt',
                 permission='delete')
    def view_sap_delete(self):
        request = self.request
        q = self.query_id()
        row = q.first()
        if not row:
            return self.id_not_found(request)
        form = Form(colander.Schema(), buttons=('hapus','batal'))
        if request.POST:
            if 'hapus' in request.POST:
                msg = 'SAP ID %d %s sudah dihapus.' % (row.id, row.nama)
                try:
                  q.delete()
                  DBSession.flush()
                except:
                  msg = 'SAP ID %d %s tidak dapat dihapus.' % (row.id, row.nama)
                request.session.flash(msg)
            return self.route_list()
        return dict(row=row,
                     form=form.render())
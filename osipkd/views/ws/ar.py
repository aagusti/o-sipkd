from sqlalchemy.sql.expression import text 
from pyramid.view import view_config
from pyramid_rpc.jsonrpc import jsonrpc_method
from hashlib import md5
from datetime import datetime
from osipkd.models import (
    DBSession, 
    User,
    )

import hmac
import hashlib
import base64
import json
import requests
from osipkd.tools import (
    get_settings,
    )
from osipkd.models.ar import ARInvoiceTransaksi, ARPaymentTransaksi
from osipkd.models.pemda import Unit
from osipkd.models.ak import Rekening

LIMIT = 1000
CODE_OK = 0
CODE_NOT_FOUND = -1
CODE_DATA_INVALID = -2
CODE_INVALID_LOGIN = -10
CODE_NETWORK_ERROR = -11

########        
# Auth #
########
def auth(username, signature, fkey):
    settings = get_settings()
    user = User.get_by_name(username)
    if not user:
        return
    
    value = "%s&%s" % (username,int(fkey)); 
    key = str(user.user_password)
    lsignature = hmac.new(key, msg=value, digestmod=hashlib.sha256).digest()
    encodedSignature = base64.encodestring(lsignature).replace('\n', '')
    if encodedSignature==signature:
       return user

def auth_from_rpc(request):
    user = auth(request.environ['HTTP_USERID'], request.environ['HTTP_SIGNATURE'], request.environ['HTTP_KEY'])
    if user:
        return dict(code=CODE_OK, message='OK')
    return dict(code=CODE_INVALID_LOGIN, message='Gagal login')
    
def get_rpc_header(userid,password):
    utc_date = datetime.utcnow()
    tStamp = int((utc_date-datetime.strptime('1970-01-01 00:00:00','%Y-%m-%d %H:%M:%S')).total_seconds())
    value = "%s&%s" % (str(userid),tStamp)
    key = str(password) 
    signature = hmac.new(key, msg=value, digestmod=hashlib.sha256).digest() 
    encodedSignature = base64.encodestring(signature).replace('\n', '')
    headers = {'userid':userid,
               'signature':encodedSignature,
               'key':tStamp}
    return headers
    
##############        
# AR-INVOICE #
##############
@jsonrpc_method(method='set_invoice', endpoint='ws')
def set_invoice(request, data):
    resp = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    unit_id = 0
    unit_kd = ""
    rekening_id = 0
    rekening_kd = ""
    try:
        for row in data:
            if row['unit_kd']!=unit_kd:
                unit_id = DBSession.query(Unit.id).filter_by(
                                    kode  = row['unit_kd']).scalar()
                unit_kd = unit_id and row['unit_kd']
                
            if row['rekening_kd']!=rekening_kd:
                rekening_id = DBSession.query(Rekening.id).filter_by(
                            kode  = row['rekening_kd']).scalar()
                rekening_kd = rekening_id and row['rekening_kd']
                    
            invoice = DBSession.query(ARInvoiceTransaksi).filter_by(
                            kode     = row['rekening_kd'],
                            tahun    = row['tahun'],
                            ref_kode = row['ref_kode']
                            ).first()
            if not invoice:
                invoice = ARInvoiceTransaksi()
                invoice.created = datetime.now()
                invoice.create_uid = 1
                
            invoice.kode         = row['rekening_kd']        
            invoice.nama         = row['nama']        
            invoice.tahun        = row['tahun']       
            invoice.amount       = row['amount']             
            invoice.ref_kode     = row['ref_kode']    
            invoice.ref_nama     = row['ref_nama']    
            invoice.tanggal      = row['tanggal']               
            invoice.kecamatan_kd = row['kecamatan_kd']          
            invoice.kecamatan_nm = row['kecamatan_nm']          
            invoice.kelurahan_kd = row['kelurahan_kd']          
            invoice.kelurahan_nm = row['kelurahan_nm']          
            invoice.is_kota      = row['is_kota']               
            invoice.sumber_data  = row['sumber_data']           
            invoice.sumber_id    = row['sumber_id']             
            invoice.unit_id      = unit_id             
            invoice.rekening_id  = rekening_id             
            #invoice.notes        = row['notes']             
            DBSession.add(invoice)
            DBSession.flush()
    except Exception e:
        print str(e)
        DBSession.rollback()
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
        
    try:
        DBSession.commit()
    except Exception e:
        print str(e)
    return dict(code=CODE_OK, message='Data Submitted')
    
##############        
# AR-PAYMENT #
##############
@jsonrpc_method(method='set_payment', endpoint='ws')
def set_payment(request, data):
    resp = auth_from_rpc(request)
    if resp['code'] != 0:
        return resp
    unit_id = 0
    unit_kd = ""
    rekening_id = 0
    rekening_kd = ""
    try:
        for row in data:
            if row['unit_kd']!=unit_kd:
                unit_id = DBSession.query(Unit.id).filter_by(
                                    kode  = row['unit_kd']).scalar()
                unit_kd = unit_id and row['unit_kd']
                
            if row['rekening_kd']!=rekening_kd:
                rekening_id = DBSession.query(Rekening.id).filter_by(
                            kode  = row['rekening_kd']).scalar()
                rekening_kd = rekening_id and row['rekening_kd']
                    
            payment = DBSession.query(ARPaymentTransaksi).filter_by(
                            kode     = row['rekening_kd'],
                            tahun    = row['tahun'],
                            ref_kode = row['ref_kode']
                            ).first()
            if not payment:
                payment = ARPaymentTransaksi()
                payment.created = datetime.now()
                payment.create_uid = 1
                
            payment.kode         = row['rekening_kd']        
            payment.nama         = row['nama']        
            payment.tahun        = row['tahun']       
            payment.amount       = row['amount']             
            payment.ref_kode     = row['ref_kode']    
            payment.ref_nama     = row['ref_nama']    
            payment.tanggal      = row['tanggal']               
            payment.kecamatan_kd = row['kecamatan_kd']          
            payment.kecamatan_nm = row['kecamatan_nm']          
            payment.kelurahan_kd = row['kelurahan_kd']          
            payment.kelurahan_nm = row['kelurahan_nm']          
            payment.is_kota      = row['is_kota']               
            payment.sumber_data  = row['sumber_data']           
            payment.sumber_id    = row['sumber_id']             
            payment.unit_id      = unit_id             
            payment.rekening_id  = rekening_id             
            #invoice.notes        = row['notes']             
            DBSession.add(payment)
            DBSession.flush()
    except:
        DBSession.rollback()
        return dict(code=CODE_DATA_INVALID, message='Data Invalid')
        
    try:
        DBSession.commit()
    except:
        pass
    return dict(code=CODE_OK, message='Data Submitted')

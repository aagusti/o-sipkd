from datetime import datetime
from sqlalchemy import (Column, Integer, String, SmallInteger, UniqueConstraint, 
                        Date, BigInteger, ForeignKey, func, extract, case)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship, backref
    )
from datetime import datetime
from zope.sqlalchemy import ZopeTransactionExtension
import transaction
from ..tools import as_timezone
from ..models import (DBSession, DefaultModel,Base,)
from ..models import (NamaModel)
from ..models.pemda import (Unit)
from ..models.ak import(Rekening)
#from ..models.apbd_anggaran import (KegiatanSub)

class ARInvoice(NamaModel, Base):
    __tablename__  ='ar_invoices'
    __table_args__ = {'extend_existing':True,'schema' :'apbd'}

    kegiatansubs   = relationship("KegiatanSub", backref="arinvoices")
    units          = relationship("Unit",        backref="arinvoices")

    tahun_id        = Column(BigInteger, ForeignKey("apbd.tahuns.id"),        nullable=False)
    unit_id         = Column(Integer,    ForeignKey("apbd.units.id"),        nullable=False) 
    kegiatan_sub_id = Column(BigInteger, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    no_urut         = Column(BigInteger, nullable=True)
    kode            = Column(String(50))
    nama            = Column(String(255))
    tgl_terima      = Column(Date)    
    tgl_validasi    = Column(Date)
    nilai           = Column(BigInteger, nullable=False)
    jenis           = Column(BigInteger, nullable=False, default=1) 
    sumber_id       = Column(SmallInteger, default=1)#1, 2, 3, 4
    bendahara_uid   = Column(Integer)
    bendahara_nm    = Column(String(64))
    bendahara_nip   = Column(String(64))
    penyetor        = Column(String(64))
    alamat          = Column(String(150))
    posted          = Column(SmallInteger, nullable=False, default=0)
    posted1         = Column(SmallInteger, nullable=True,  default=0)
    disabled        = Column(Integer,      nullable=False, default=0)

    UniqueConstraint('tahun_id', 'unit_id', 'kode',
                name = 'arinvoice_ukey')

    @classmethod
    def get_nilai(cls, ar_invoice_id):
        return DBSession.query(func.sum(ARInvoiceItem.nilai).label('nilai')
                             ).filter(ARInvoiceItem.ar_invoice_id==ar_invoice_id 
                                      ).first()
                    
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
    
    @classmethod
    def get_norut(cls, tahun, unit_id):
        return DBSession.query(func.count(cls.id).label('no_urut'))\
               .filter(cls.tahun_id==tahun,
                       cls.unit_id ==unit_id
               ).scalar() or 0
    
    @classmethod
    def get_periode(cls, id):
        return DBSession.query(extract('month',cls.tgl_terima).label('periode'))\
                .filter(cls.id==id,)\
                .group_by(extract('month',cls.tgl_terima)
                ).scalar() or 0
    
    @classmethod
    def get_tipe(cls, id):
        return DBSession.query(case([(Sts.jenis==1,"T"),(Sts.jenis==2,"P"),
                          (Sts.jenis==3,"K")], else_="").label('jenis'))\
                .filter(cls.id==id,
                ).scalar() or 0 
      
class ARInvoiceItem(DefaultModel, Base):
    __tablename__  = 'ar_invoice_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    
    kegiatanitems  =  relationship("KegiatanItem", backref="arinvoiceitems")
    arinvoices     =  relationship("ARInvoice",    backref="arinvoiceitems")

    ar_invoice_id    = Column(BigInteger, ForeignKey("apbd.ar_invoices.id"),    nullable=False)
    kegiatan_item_id = Column(BigInteger, ForeignKey("apbd.kegiatan_items.id"), nullable=False)  
    no_urut          = Column(Integer) 
    nama             = Column(String(64)) 
    vol_1            = Column(BigInteger,   nullable=False, default=0)
    vol_2            = Column(BigInteger,   nullable=False, default=0)
    harga            = Column(BigInteger,   nullable=False, default=0)
    nilai            = Column(BigInteger,   nullable=False, default=0)
    notes1           = Column(String(64))  
    unit_id          = Column(Integer)
    rekening_id      = Column(Integer)
    kode             = Column(String(32))
    ref_kode         = Column(String(32), unique=True)
    ref_nama         = Column(String(64))
    tanggal          = Column(Date)
    kecamatan_kd     = Column(String(32))
    kecamatan_nm     = Column(String(64))
    kelurahan_kd     = Column(String(32))
    kelurahan_nm     = Column(String(64))
    is_kota          = Column(SmallInteger, default=0)
    sumber_id        = Column(SmallInteger, default=1)#1, 2, 3, 4
    sumber_data      = Column(String(32)) #Manual, PBB, BPHTB, PADL
    tahun            = Column(Integer)
    bulan            = Column(Integer)
    minggu           = Column(Integer)
    hari             = Column(Integer)
    disabled         = Column(SmallInteger, default=0)
    posted           = Column(SmallInteger, default=0)
    posted1          = Column(SmallInteger, default=0)
    
    @classmethod
    def max_no_urut(cls, ar_invoice_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.ar_invoice_id==ar_invoice_id
                ).scalar() or 0 

class Sts(NamaModel, Base):
    __tablename__  = 'ar_sts'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    
    units          = relationship("Unit",        backref="sts")
   
    tahun_id        = Column(BigInteger, ForeignKey("apbd.tahuns.id"), nullable=False)
    unit_id         = Column(Integer,    ForeignKey("apbd.units.id"), nullable=False)
    
    no_urut        = Column(BigInteger, nullable=False)
    kode           = Column(String(64), nullable=False)
    nama           = Column(String(64), nullable=False)
    jenis          = Column(BigInteger, nullable=False)                 
    nominal        = Column(BigInteger, nullable=False)
    ttd_uid        = Column(Integer)
    ttd_nip        = Column(String(32))
    ttd_nama       = Column(String(64))
    ttd_jab        = Column(String(64))
    bank_nama      = Column(String(32), nullable=False)
    bank_account   = Column(String(64), nullable=False)
    tgl_sts        = Column(Date) 
    tgl_validasi   = Column(Date)
    posted         = Column(SmallInteger, nullable=False, default=0)
    posted1        = Column(SmallInteger, nullable=False, default=0)
    disabled       = Column(SmallInteger, nullable=False, default=0)
    no_validasi    = Column(String(64))
    
    UniqueConstraint('tahun_id', 'unit_id', 'kode',
            name = 'ar_sts_kode_ukey')
    
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun_id==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
                
    @classmethod
    def get_nilai(cls, ar_sts_id):
        return DBSession.query(func.sum(StsItem.amount).label('nilai')
                             ).filter(StsItem.ar_sts_id==ar_sts_id 
                                      ).first()   
    
    @classmethod
    def get_periode(cls, id):
        return DBSession.query(extract('month',cls.tgl_sts).label('periode'))\
                .filter(cls.id==id,)\
                .group_by(extract('month',cls.tgl_sts)
                ).scalar() or 0
                
    @classmethod
    def get_tipe(cls, id):
        return DBSession.query(case([(Sts.jenis==1,"BP"),(Sts.jenis==2,"P"),(Sts.jenis==3,"NP"),(Sts.jenis==4,"CP"),
                          (Sts.jenis==5,"L")], else_="").label('jenis'))\
                .filter(cls.id==id,
                ).scalar() or 0        
     
    
class StsItem(DefaultModel, Base):
    __tablename__      = 'ar_sts_items'
    __table_args__     = {'extend_existing':True,'schema' :'apbd'}

    sts                = relationship("Sts",          backref="sts_items")
    kegiatanitems      = relationship("KegiatanItem", backref="sts_items")
    ar_sts_id          = Column(BigInteger, ForeignKey("apbd.ar_sts.id"),         nullable=False)
    kegiatan_item_id   = Column(BigInteger, ForeignKey("apbd.kegiatan_items.id"), nullable=False)
    amount             = Column(BigInteger)
    
class ARPaymentItem(NamaModel, Base):
    __tablename__  = 'ar_payment_items'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    units         = relationship("Unit",        backref=backref("ar_payment_items"))
    #kegiatan_subs = relationship("KegiatanSub", backref=backref("ar_payment_items"))
    rekenings     = relationship("Rekening",    backref=backref("ar_payment_items"))

    unit_id         = Column(Integer, ForeignKey("apbd.units.id"),        nullable=False)
    kegiatan_sub_id = Column(Integer, ForeignKey("apbd.kegiatan_subs.id"), nullable=True)
    rekening_id     = Column(Integer, ForeignKey("apbd.rekenings.id"),    nullable=False)
    tahun           = Column(Integer)
    amount          = Column(BigInteger)
    no_urut         = Column(BigInteger, nullable=True)
    ref_kode        = Column(String(64))
    ref_nama        = Column(String(64))
    tanggal         = Column(Date, nullable=True)
    jenis           = Column(SmallInteger, default=1) #Piutang, Normal
    kecamatan_kd    = Column(String(32))
    kecamatan_nm    = Column(String(64))
    kelurahan_kd    = Column(String(32))
    kelurahan_nm    = Column(String(64))
    is_kota         = Column(SmallInteger, default=0)
    sumber_data     = Column(String(32)) #Manual, PBB, BPHTB, PAD
    sumber_id       = Column(SmallInteger)#1, 2, 3, 4
    bulan           = Column(Integer)
    minggu          = Column(Integer)
    hari            = Column(Integer)
    bud_uid         = Column(BigInteger,   nullable=True)
    bud_nip         = Column(String(50),   nullable=True)
    bud_nama        = Column(String(64),   nullable=True)
    disabled        = Column(SmallInteger, nullable=False, default=0)
    posted          = Column(SmallInteger, nullable=False, default=0)
    posted1         = Column(SmallInteger, nullable=True,  default=0)
    
    @classmethod
    def max_no_urut(cls, tahun, unit_id):
        return DBSession.query(func.max(cls.no_urut).label('no_urut'))\
                .filter(cls.tahun==tahun,
                        cls.unit_id==unit_id
                ).scalar() or 0
                
    @classmethod
    def get_periode(cls, id):
        return DBSession.query(extract('month',cls.tanggal).label('periode'))\
                .filter(cls.id==id,)\
                .group_by(extract('month',cls.tanggal)
                ).scalar() or 0
    
    @classmethod
    def get_periode2(cls, id_tbp):
        return DBSession.query(extract('month',cls.tanggal).label('periode'))\
                .filter(cls.id==id_tbp,)\
                .group_by(extract('month',cls.tanggal)
                ).scalar() or 0
    
    @classmethod
    def get_tipe(cls, id):
        return DBSession.query(case([(cls.jenis==1,"P"),(cls.jenis==2,"NP")], else_="").label('jenis'))\
                .filter(cls.id==id,
                ).scalar() or 0
    
    @classmethod
    def get_norut(cls, tahun, unit_id):
        return DBSession.query(func.count(cls.id).label('no_urut'))\
               .filter(cls.tahun==tahun,
                       cls.unit_id ==unit_id  
               ).scalar() or 0

               
class ARInvoiceTransaksi(NamaModel, Base):
    __tablename__  = 'ar_invoice_item'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    units     = relationship("Unit",     backref=backref("ar_invoice_item"))
    rekenings = relationship("Rekening", backref=backref("ar_invoice_item"))
    unit_id      = Column(Integer, ForeignKey("apbd.units.id"),     nullable=False)
    rekening_id  = Column(Integer, ForeignKey("apbd.rekenings.id"), nullable=False)
    ref_kode     = Column(String(32), unique=True)
    ref_nama     = Column(String(64))
    tanggal      = Column(Date, nullable=False)
    amount       = Column(BigInteger)
    kecamatan_kd = Column(String(32))
    kecamatan_nm = Column(String(64))
    kelurahan_kd = Column(String(32))
    kelurahan_nm = Column(String(64))
    is_kota      = Column(SmallInteger, default=0)
    sumber_id    = Column(SmallInteger)#1, 2, 3, 4
    sumber_data  = Column(String(32)) #Manual, PBB, BPHTB, PADL
    tahun        = Column(Integer)
    bulan        = Column(Integer)
    minggu       = Column(Integer)
    hari         = Column(Integer)
    posted       = Column(SmallInteger, nullable=False, default=0)
    
    @classmethod
    def get_periode(cls, id):
        return DBSession.query(extract('month',cls.tanggal).label('periode'))\
                .filter(cls.id==id,)\
                .group_by(extract('month',cls.tanggal)
                ).scalar() or 0
                
class ARPaymentTransaksi(NamaModel, Base):
    __tablename__  = 'ar_payment_item'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    unit_id         = Column(Integer, ForeignKey("apbd.units.id"),        nullable=False)
    rekening_id     = Column(Integer, ForeignKey("apbd.rekenings.id"),    nullable=False)
    units         = relationship("Unit",        backref=backref("ar_payment_item"))
    rekenings     = relationship("Rekening",    backref=backref("ar_payment_item"))

    #kegiatan_subs = relationship("KegiatanSub", backref=backref("ar_payment_items"))
    #kegiatan_sub_id = Column(Integer, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    tahun           = Column(Integer)
    amount          = Column(BigInteger)
    ref_kode        = Column(String(32))
    ref_nama        = Column(String(64))
    tanggal         = Column(Date, nullable=True)
    kecamatan_kd    = Column(String(32))
    kecamatan_nm    = Column(String(64))
    kelurahan_kd    = Column(String(32))
    kelurahan_nm    = Column(String(64))
    is_kota         = Column(SmallInteger, default=0)
    sumber_data     = Column(String(32)) #0Manual, PBB, BPHTB, PAD
    sumber_id       = Column(SmallInteger) #0->Self 1-PBB, 2-PBB, 3, 4
    is_piutang      = Column(Integer) #0 Self 1 Piutang
    bulan           = Column(Integer)
    minggu          = Column(Integer)
    hari            = Column(Integer)
    posted          = Column(SmallInteger, nullable=False, default=0)
    bud_uid         = Column(BigInteger,   nullable=False)
    bud_nip         = Column(String(50),   nullable=False)
    bud_nama        = Column(String(64),   nullable=False)
    
    @classmethod
    def get_periode(cls, id):
        return DBSession.query(extract('month',cls.tanggal).label('periode'))\
                .filter(cls.id==id,)\
                .group_by(extract('month',cls.tanggal)
                ).scalar() or 0
    
    @classmethod
    def get_periode2(cls, id_tbp):
        return DBSession.query(extract('month',cls.tanggal).label('periode'))\
                .filter(cls.id==id_tbp,)\
                .group_by(extract('month',cls.tanggal)
                ).scalar() or 0
                
class ARTargetItem(NamaModel, Base):
    __tablename__ = 'ar_target_item'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    units         = relationship("Unit",        backref=backref("ar_target_items"))
    #kegiatan_subs = relationship("KegiatanSub", backref=backref("ar_target_items"))
    rekenings     = relationship("Rekening",    backref=backref("ar_target_items"))

    unit_id         = Column(Integer, ForeignKey("apbd.units.id"),        nullable=False)
    #kegiatan_sub_id = Column(Integer, ForeignKey("apbd.kegiatan_subs.id"), nullable=False)
    rekening_id     = Column(Integer, ForeignKey("apbd.rekenings.id"),    nullable=False)
    tahun           = Column(Integer)
    amount_01       = Column(BigInteger)
    amount_02       = Column(BigInteger)
    amount_03       = Column(BigInteger)
    amount_04       = Column(BigInteger)
    amount_05       = Column(BigInteger)
    amount_06       = Column(BigInteger)
    amount_07       = Column(BigInteger)
    amount_08       = Column(BigInteger)
    amount_09       = Column(BigInteger)
    amount_10       = Column(BigInteger)
    amount_11       = Column(BigInteger)
    amount_12       = Column(BigInteger)

class ARKasdaItem(NamaModel, Base):
    __tablename__ = 'ar_kasda'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}
    units         = relationship("Unit",  backref=backref("ar_kasda_item"))
    unit_id         = Column(Integer, ForeignKey("apbd.units.id"), nullable=False)
    rekenings     = relationship("Rekening",    backref=backref("ar_kasda_item"))
    rekening_id     = Column(Integer, ForeignKey("apbd.rekenings.id"), nullable=False)
    tahun           = Column(Integer)
    amount          = Column(BigInteger)
    ref_kode        = Column(String(32))
    ref_nama        = Column(String(64))
    tanggal         = Column(Date, nullable=True)
    is_kota         = Column(SmallInteger, default=0)
    bulan           = Column(Integer)
    minggu          = Column(Integer)
    hari            = Column(Integer)
    posted          = Column(SmallInteger, nullable=False, default=0)
    
class ARApproval(NamaModel, Base):
    __tablename__   = 'ar_approval'
    __table_args__  = {'extend_existing':True, 'schema' : 'apbd',}
    units           = relationship("Unit", backref=backref("ar_approval"))
    unit_id         = Column(Integer, ForeignKey("apbd.units.id"), nullable=False)
    tahun           = Column(Integer)
    amtofkasda      = Column(BigInteger)
    amtofbendahara  = Column(BigInteger)
    ref_kode        = Column(String(32))
    ref_nama        = Column(String(64))
    tanggal         = Column(Date, nullable=True)
    pajak_approval  = Column(SmallInteger, nullable=False, default=0)
    kasda_uid       = Column(Integer)
    bendahara_uid   = Column(Integer)
    
class ARApprovalItem(DefaultModel, Base):
    __tablename__  = 'ar_approval_item'
    __table_args__ = {'extend_existing':True, 'schema' : 'apbd',}

    ar_approval_id     = Column(Integer, ForeignKey("apbd.rekenings.id"), nullable=False)
    ar_payment_item_id = Column(Integer, ForeignKey("apbd.rekenings.id"), nullable=False)
    amount             = Column(BigInteger, nullable=False, default=0)
    
    
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
#from ..models.apbd_anggaran import (KegiatanSub)
JV_TYPE = {1:"JT",
           2:"JK",
           3:"JU",
           4:"KR",
           5:"CL",
           6:"LO",
           7:"JP",
           }
        
class Rekening(NamaModel, Base):
    __tablename__ = 'rekenings'
    __table_args__= (UniqueConstraint('kode', 'tahun', name='rekening_uq'),
                      {'extend_existing':True, 
                      'schema' : 'apbd',})
    tahun = Column(Integer)
    nama  = Column(String(255))
    #created  = Column(DateTime, nullable=False, default=datetime.utcnow)
    level_id  = Column(SmallInteger)
    parent_id  = Column(BigInteger, ForeignKey('apbd.rekenings.id'))
    disabled = Column(SmallInteger, nullable=False, default=0)
    children   = relationship("Rekening", backref=backref('parent', remote_side='Rekening.id'))
    
    @classmethod
    def get_next_level(cls,id):
        return cls.query_id(id).first().level_id+1
        
        
############################################
###  JURNAL ANGGARAN    ###
###  KegiatanItem  ###
############################################        
class Jurnal(NamaModel, Base):
    __tablename__   = 'jurnals'
    __table_args__  = {'extend_existing':True, 'schema' : 'apbd',}
                    
    units           = relationship("Unit",  backref=backref("jurnals")) 
    unit_id         = Column(Integer,       ForeignKey("apbd.units.id"), nullable=False)  
    tahun_id        = Column(BigInteger, nullable=False)
    kode            = Column(String(32),    nullable=False)    
    nama            = Column(String(128),   nullable=False)
    jv_type         = Column(SmallInteger,  nullable=False, default=0)
    tanggal         = Column(Date) 
    tgl_transaksi   = Column(Date)
    periode         = Column(Integer,       nullable=False)
    source          = Column(String(32),    nullable=False)
    source_no       = Column(String(30),    nullable=False)
    source_id       = Column(BigInteger,    nullable=False)
    tgl_source      = Column(Date)           
    posted          = Column(SmallInteger,  nullable=False)
    posted_uid      = Column(Integer) 
    posted_date     = Column(Date) 
    notes           = Column(String(225),   nullable=False)
    is_skpd         = Column(SmallInteger,  nullable=False)
    disabled        = Column(SmallInteger,  nullable=False, default=0)

    @classmethod
    def get_norut(cls, tahun, unit_id):
        return DBSession.query(func.count(cls.id).label('no_urut'))\
               .filter(cls.tahun_id==tahun,
                       cls.unit_id ==unit_id
               ).scalar() or 0
               
    @classmethod
    def jv_type_nm(cls):
        return JV_TYPE[cls.jv_type]
                
class JurnalItem(DefaultModel, Base):
    __tablename__   ='jurnal_items'
    __table_args__  = {'extend_existing':True,'schema' :'apbd'}

    jurnals         = relationship("Jurnal", backref="jurnal_items")
    jurnal_id       = Column(BigInteger, ForeignKey("apbd.jurnals.id"), nullable=False)
    kegiatan_sub_id = Column(BigInteger, default=0, nullable=True) 
    rekening_id     = Column(BigInteger, default=0, nullable=True)
    sap_id          = Column(BigInteger, default=0, nullable=True)
    amount          = Column(BigInteger, default=0) 
    notes           = Column(String(225),nullable=True)

class Sap(NamaModel, Base):
    __tablename__ = 'saps'
    __table_args__= (UniqueConstraint('kode', 'tahun', name='sap_uq'),
                      {'extend_existing':True, 
                      'schema' : 'apbd',})
                      
    tahun     = Column(Integer)
    nama      = Column(String(256))
    level_id  = Column(SmallInteger, default=1)
    parent_id = Column(BigInteger,   ForeignKey('apbd.saps.id'))
    disabled  = Column(SmallInteger, default=0)
    defsign   = Column(SmallInteger, default=1)
    children  = relationship("Sap", backref=backref('parent', remote_side='Sap.id'))
    
    @classmethod
    def get_next_level(cls,id):
        return cls.query_id(id).first().level_id+1

class RekeningSap(DefaultModel, Base):
    __tablename__    = 'rekenings_saps'
    __table_args__   = {'extend_existing':True,'schema' : 'apbd'}
                     
    rekening_id      = Column(Integer, ForeignKey("apbd.rekenings.id"))        
    db_lo_sap_id     = Column(Integer, nullable=True)
    kr_lo_sap_id     = Column(Integer, nullable=True)
    db_lra_sap_id    = Column(Integer, nullable=True)
    kr_lra_sap_id    = Column(Integer, nullable=True)
    neraca_sap_id    = Column(Integer, nullable=True)
    pph_id           = Column(String(64))
    
    rekenings   = relationship("Rekening", backref="rekenings_saps")
        
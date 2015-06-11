from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    BigInteger,
    SmallInteger,
    Text,
    DateTime,
    Date,
    String,
    ForeignKey,
    text,
    UniqueConstraint,
    
    )
    
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,backref    )
from ..models import Base, DBSession, CommonModel, NamaModel, DefaultModel

def unitfinder(userid, request):
    if userid and hasattr(request, 'user') and request.user:
        units = [('%s,%s' % (u.kode,u.sub_unit)) for u in request.user.units]
        return units
    return []
    
class Urusan(Base, NamaModel):
    __tablename__  = 'urusans'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}

class Unit(Base, NamaModel):
    __tablename__  = 'units'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'apbd',}
                       
    urusan_id = Column(Integer, ForeignKey('apbd.urusans.id'))
    kategori = Column(String(32))
    singkat  = Column(String(32))
    level_id  = Column(SmallInteger)
    header_id = Column(SmallInteger)
    urusan_id = Column(Integer, ForeignKey('apbd.urusans.id'))
    units     = relationship("Urusan", backref="units")

class UserUnit(Base, CommonModel):
    __tablename__  = 'user_units'
    __table_args__ = {'extend_existing':True, 
                      'schema' : 'public',}
                       
    user_id = Column(Integer, ForeignKey('users.id'), primary_key=True)
    unit_id = Column(Integer, ForeignKey('apbd.units.id'), primary_key=True)
    sub_unit = Column(SmallInteger, nullable=False)
    units     = relationship("Unit", backref="users")
    users     = relationship("User", backref="units")
    
    @classmethod
    def query_user_id(cls, user_id):
        return DBSession.query(cls).filter_by(user_id = user_id)

    @classmethod
    def ids(cls, user_id):
        r = ()
        units = DBSession.query(cls.unit_id,cls.sub_unit, Unit.kode
                     ).join(Unit).filter(cls.unit_id==Unit.id,
                            cls.user_id==user_id).all() 
        for unit in units:
            if unit.sub_unit:
                rows = DBSession.query(Unit.id).filter(Unit.kode.ilike('%s%%' % unit.kode)).all()
            else:
                rows = DBSession.query(Unit.id).filter(Unit.kode==unit.kode).all()
            for i in range(len(rows)):
                print '***', rows[i]
                r = r + (rows[i])
        return r
        
    @classmethod
    def unit_granted(cls, user_id, unit_id):
        
        print 'A*******',  user_id, unit_id
        units = DBSession.query(cls.unit_id,cls.sub_unit, Unit.kode
                     ).join(Unit).filter(cls.unit_id==Unit.id,
                            cls.user_id==user_id).all() 
        for unit in units:
            print 'B*******',  unit_id, unit
            if unit.sub_unit:
                rows = DBSession.query(Unit.id).filter(Unit.kode.ilike('%s%%' % unit.kode)).all()
            else:
                rows = DBSession.query(Unit.id).filter(Unit.kode==unit.kode).all()
            for i in range(len(rows)):
                if int(rows[i][0])  == int(unit_id):
                    return True
        return False
        
    @classmethod
    def get_filtered(cls, request):
        filter = "'%s' LIKE public.units.kode||'%%'" % request.session['unit_kd']
        q1 = DBSession.query(Unit.kode, UserUnit.sub_unit).join(UserUnit).\
                       filter(UserUnit.user_id==request.user.id,
                              UserUnit.unit_id==Unit.id,
                              text(filter))
        return q1.first()
        
class Pegawai(NamaModel, Base):
    __tablename__  = 'pegawais'
    __table_args__ = {'extend_existing':True,'schema' : 'apbd'}

class Jabatan(NamaModel, Base):
    __tablename__  = 'jabatans'
    __table_args__ = {'extend_existing':True,'schema' : 'apbd'}
        
class Pejabat(DefaultModel, Base):
    __tablename__  = 'pejabats'
    __table_args__ = {'extend_existing':True,'schema' : 'apbd'}
    unit_id    = Column(Integer, ForeignKey("apbd.units.id"))
    units      = relationship("Unit", backref=backref('pejabats'))
    pegawai_id = Column(Integer, ForeignKey("apbd.pegawais.id"))
    pegawais   = relationship("Pegawai", backref=backref('pejabats'))
    jabatan_id = Column(Integer, ForeignKey("apbd.jabatans.id"))
    jabatans   = relationship("Jabatan", backref=backref('pejabats'))
    uraian     = Column(String(200))
    mulai      = Column(Date)
    selesai    = Column(Date)


"""class Tapd(NamaModel, Base):
    __tablename__  = 'tapds'
    __table_args__ = {'extend_existing':True,'schema' : 'apbd'}
    jabatans       = relationship("Jabatan", backref="tapds")
    pegawais       = relationship("Pegawai", backref="tapds")
    jabatan_id     = Column(Integer, ForeignKey("apbd.jabatans.id"))
    pegawai_id     = Column(Integer, ForeignKey("apbd.pegawais.id"))
    mulai          = Column(Date)
    selesai        = Column(Date)

    def __init__(self, data):
        NamaModel.__init__(self,data) 
        self.jabatan_id  = data['jabatan_id'] 
        self.pegawai_id  = data['pegawai_id'] 
        self.mulai       = data['mulai'] 
        self.selesai     = data['selesai'] 
     
    @classmethod
    def update(cls, data):
        data['updated'] = datetime.now()	 
        data['mulai']   = data['mulai'] and datetime.strptime(data['mulai'],'%d-%m-%Y') or None
        data['selesai'] = data['selesai'] and datetime.strptime(data['selesai'],'%d-%m-%Y') or None
        return DBSession.query(cls).filter(cls.id==data['id']).update(data)

class TapdUnit(NamaModel, Base):
    __tablename__  = 'pegawai_jabatans'
    __table_args__ = {'extend_existing':True,'schema' : 'apbd'}
    unit_id = Column(Integer, ForeignKey("apbd.pegawais.id"))
    tapd_id = Column(Integer, ForeignKey("apbd.jabatans.id"))
    mulai   = Column(Date)
    selesai = Column(Date)
    def __init__(self, data):
        NamaModel.__init__(self,data)
        self.unit_id   = data['unit_id']
        self.tapd_id   = data['tapd_id']
        self.mulai     = data['mulai']
        self.selesai   = data['selesai']
"""
    
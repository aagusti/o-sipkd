from pyramid.view import (
    view_config,
    )
from pyramid.httpexceptions import (
    HTTPFound,
    )
#from osipkd.models.apbd_anggaran import Tahun    
from osipkd.models import App    
#from osipkd.views.base_view import BaseViews
    
########
# APP Home #
########
@view_config(route_name='ar', renderer='templates/home.pt', permission='view')
def view_app(request):
    session = request.session
    tahun = App.get_by_kode('ar').tahun or datetime.strftime('%Y')
    session['tahun'] = tahun
    #tahun  = Tahun.get_by_tahun(session['tahun'])
    #if not tahun:
    #    session.flash('Tahun Anggaran Belum di Set')
    #    return HTTPFound('ag-tahun') 
    #session['ag_step_id'] = tahun.status_apbd
    #session['ag_step_nm'] = self._StatusAPBD(session['ag_step_id'])
    return dict(project='akuntansi')
            
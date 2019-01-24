from io import StringIO

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View

from neslter.parsing.files import FILENAME
from neslter.parsing.ctd import Ctd
from neslter.parsing.underway import Underway
from neslter.parsing.elog import EventLog

def datatable_response(dt, extension='json'):
    try:
        getattr(dt, 'metadata')
    except KeyError:
        raise Http404('cannot construct filename')
    filename = '{}.{}'.format(dt.metadata[FILENAME], extension)
    if extension == 'json':
        return HttpResponse(dt.to_json(), content_type='application/json')
    elif extension == 'csv':
        sio = StringIO()
        dt.to_csv(sio, index=None)
        csv = sio.getvalue()
        resp = HttpResponse(csv, content_type='text/csv')
        if filename is not None:
            resp['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return resp
    else:
        raise Http404('unsupported file type .{}'.format(extension))

class CtdView(View):
    """abstract view for handling CTD data"""
    def ctd(self, cruise):
        try:
            ctd = Ctd(cruise.lower())
        except KeyError as exc:
            # cruise not found
            raise Http404(str(exc))
        return ctd

class CtdCastsView(CtdView):
    def get(self, request, cruise): # JSON only
        casts = self.ctd(cruise).casts()
        return JsonResponse({
            'casts': casts
        })

class CtdMetadataView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        md = self.ctd(cruise).metadata()
        return datatable_response(md, extension)

class CtdBottlesView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        btl = self.ctd(cruise).bottles()
        return datatable_response(btl, extension)

class CtdBottleSummaryView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        btl_summary = self.ctd(cruise).bottle_summary()
        return datatable_response(btl_summary, extension)

class CtdCastView(CtdView):
    def get(self, request, cruise, cast, extension=None):
        if extension is None: extension = 'json'
        cast = self.ctd(cruise).cast(cast)
        return datatable_response(cast, extension)

class UnderwayView(View):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename = '{}_underway.{}'.format(cruise, extension)
        try:
            uw = Underway(cruise)
        except KeyError as exc:
            raise Http404(str(exc))
        df = uw.to_dataframe()
        return datatable_response(df, extension)

class EventLogView(View):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        try:
            elog = EventLog(cruise)
        except KeyError as exc:
            raise Http404(str(exc))
        df = elog.to_dataframe()
        return datatable_response(df, extension)
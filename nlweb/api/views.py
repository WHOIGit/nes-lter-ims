from io import StringIO

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse
from django.views import View

from neslter.parsing.ctd import Ctd

def index(request):
    return HttpResponse("Hello, world. You're at the api index.")

def dataframe_response(df, extension='json', filename=None):
    if extension == 'json':
        return HttpResponse(df.to_json(), content_type='application/json')
    elif extension == 'csv':
        sio = StringIO()
        df.to_csv(sio, index=None)
        csv = sio.getvalue()
        resp = HttpResponse(csv, content_type='text/csv')
        if filename is not None:
            resp['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return resp

class CtdView(View):
    """abstract view for handling CTD data"""
    def ctd(self, cruise):
        ctd = Ctd(cruise.lower())
        return ctd

class CtdMetadataView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename = '{}_ctd_metadata.{}'.format(cruise, extension)
        md = self.ctd(cruise).metadata()
        return dataframe_response(md, extension, filename=filename)

class CtdBottlesView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename = '{}_ctd_bottles.{}'.format(cruise, extension)
        btl = self.ctd(cruise).bottles()
        return dataframe_response(btl, extension, filename=filename)

class CtdBottleSummaryView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename = '{}_ctd_bottle_summary.{}'.format(cruise, extension)
        btl_summary = self.ctd(cruise).bottle_summary()
        return dataframe_response(btl_summary, extension, filename=filename)

class CtdCastView(CtdView):
    def get(self, request, cruise, cast, extension=None):
        if extension is None: extension = 'json'
        filename = '{}_ctd_cast{}.{}'.format(cruise, cast, extension)
        cast = self.ctd(cruise).cast(cast)
        return dataframe_response(cast, extension, filename=filename)

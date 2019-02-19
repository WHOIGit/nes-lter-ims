from io import StringIO

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View

import pandas as pd

from neslter.parsing.files import Resolver, FILENAME
from neslter.parsing.ctd import Ctd
from neslter.parsing.underway import Underway
from neslter.parsing.elog import EventLog
from neslter.parsing.stations import Stations, StationLocator

from neslter.workflow.ctd import CtdResolver
from neslter.workflow.underway import UnderwayResolver
from neslter.workflow.elog import EventLogResolver
from neslter.workflow.stations import StationsResolver

def dataframe_response(df, filename, extension='json'):
    filename = '{}.{}'.format(filename, extension)
    if extension == 'json':
        return HttpResponse(df.to_json(), content_type='application/json')
    elif extension == 'csv':
        sio = StringIO()
        df.to_csv(sio, index=None, encoding='utf-8')
        csv = sio.getvalue()
        resp = HttpResponse(csv, content_type='text/csv')
        if filename is not None:
            resp['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
        return resp
    else:
        raise Http404('unsupported file type .{}'.format(extension))   

def read_product_csv(path):
    """file must exist and be a CSV file"""
    return pd.read_csv(path, index_col=None, encoding='utf-8')

class CruisesView(View):
    """list cruises. JSON only"""
    def get(self, request):
        cruises = Resolver().cruises()
        return JsonResponse({
            'cruises': cruises
            })

class CtdView(View):
    """abstract view for handling CTD data"""
    def parser(self, cruise):
        try:
            parser = Ctd(cruise.lower())
        except KeyError as exc:
            # cruise not found
            raise Http404(str(exc))
        return parser
    def resolver(self, cruise):
        return CtdResolver(cruise)

class CtdCastsView(CtdView):
    def get(self, request, cruise): # JSON only
        filename, path = self.resolver(cruise).metadata()
        if path is not None:
            md = read_product_csv(path)
        else:
            md = self.parser(cruise).metadata()
        casts = [int(i) for i in sorted(md['cast'].unique())]
        return JsonResponse({'casts': casts})

class CtdMetadataView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        # read ctd metadata
        filename, path = self.resolver(cruise).metadata()
        if path is not None:
            md = read_product_csv(path)
        else:
            md = self.parser(cruise).metadata()
        if 'nearest_station' in md.columns:
            return dataframe_response(md, filename, extension)
        # now merge with nearest station
        smd = None
        _, path = StationsResolver(cruise).find_file()
        if path is not None:
            smd = read_product_csv(path)
        else:
            try:
                stations = Stations(cruise)
                smd = stations.to_dataframe()
            except KeyError:
                pass
        if smd is not None:
            station_locator = StationLocator(smd)
            md = station_locator.cast_to_station(md)
        return dataframe_response(md, filename, extension)

class CtdBottlesView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename, path = self.resolver(cruise).bottles()
        if path is not None:
            btl = read_product_csv(path)
        else:
            btl = self.parser(cruise).bottles()
        return dataframe_response(btl, filename, extension)

class CtdBottleSummaryView(CtdView):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename, path = self.resolver(cruise).bottle_summary()
        if path is not None:
            btl_summary = read_product_csv(path)
        else:
            btl_summary = self.parser(cruise).bottle_summary()
        return dataframe_response(btl_summary, filename, extension)

class CtdCastView(CtdView):
    def get(self, request, cruise, cast, extension=None):
        if extension is None: extension = 'json'
        filename, path = self.resolver(cruise).cast(cast)
        if path is not None:
            df = read_product_csv(path)
        else:
            df = self.parser(cruise).cast(cast)
        return dataframe_response(df, filename, extension)

class UnderwayView(View):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename, path = UnderwayResolver(cruise).find_file()
        if path is not None:
            uw = read_product_csv(path)
        else:
            try:
                uw = Underway(cruise).to_dataframe()
            except KeyError as exc:
                raise Http404(str(exc))
        return dataframe_response(uw, filename, extension)

class EventLogView(View):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename, path = EventLogResolver(cruise).find_file()
        if path is not None:
            df = read_product_csv(path)
        else:
            try:
                elog = EventLog(cruise)
            except KeyError as exc:
                raise Http404(str(exc))
            df = elog.to_dataframe()
        return dataframe_response(df, filename, extension)

class StationsView(View):
    def get(self, request, cruise, extension=None):
        if extension is None: extension = 'json'
        filename, path = StationsResolver(cruise).find_file()
        if path is not None:
            df = read_product_csv(path)
        else:
            try:
                stations = Stations(cruise)
            except KeyError as exc:
                raise Http404(str(exc))
            df = stations.to_dataframe()
        return dataframe_response(df, filename, extension)

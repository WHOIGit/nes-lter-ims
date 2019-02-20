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

from neslter.workflow.ctd import CtdCastWorkflow, CtdBottlesWorkflow, \
        CtdBottleSummaryWorkflow, CtdMetadataWorkflow
from neslter.workflow.stations import StationsWorkflow
from neslter.workflow.elog import EventLogWorkflow
from neslter.workflow.underway import UnderwayWorkflow

def dataframe_response(df, filename, extension='json'):
    if extension is None:
        extension = 'json'
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

def workflow_response(workflow, extension=None):
    filename = workflow.filename()
    df = workflow.get_product()
    return dataframe_response(df, filename, extension)

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

class CtdCastsView(View):
    def get(self, request, cruise): # JSON only
        wf = CtdMetadataWorkflow(cruise)
        md = wf.get_product()
        casts = [int(i) for i in sorted(md['cast'].unique())]
        return JsonResponse({'casts': casts})

class CtdMetadataView(View):
    def get(self, request, cruise, extension=None):
        ctd_wf = CtdMetadataWorkflow(cruise)
        md = ctd_wf.get_product()
        # get station metadata to add nearest_station
        # FIXME do this in workflow
        st_wf = StationsWorkflow(cruise)
        smd = st_wf.get_product()
        station_locator = StationLocator(smd)
        md = station_locator.cast_to_station(md)
        filename = ctd_wf.filename()
        return dataframe_response(md, filename, extension)

class CtdBottlesView(View):
    def get(self, request, cruise, extension=None):
        wf = CtdBottlesWorkflow(cruise)
        return workflow_response(wf, extension)

class CtdBottleSummaryView(View):
    def get(self, request, cruise, extension=None):
        wf = CtdBottleSummaryWorkflow(cruise)
        return workflow_response(wf, extension)

class CtdCastView(View):
    def get(self, request, cruise, cast, extension=None):
        wf = CtdCastWorkflow(cruise, cast)
        return workflow_response(wf, extension)

class UnderwayView(View):
    def get(self, request, cruise, extension=None):
        wf = UnderwayWorkflow(cruise)
        return workflow_response(wf, extension)

class EventLogView(View):
    def get(self, request, cruise, extension=None):
        wf = EventLogWorkflow(cruise)
        return workflow_response(wf, extension)

class StationsView(View):
    def get(self, request, cruise, extension=None):
        wf = StationsWorkflow(cruise)
        return workflow_response(wf, extension)

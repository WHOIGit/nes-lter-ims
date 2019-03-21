from io import StringIO

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View

import pandas as pd

from neslter.parsing.files import Resolver

from neslter.workflow.ctd import CtdCastWorkflow, CtdBottlesWorkflow, \
        CtdBottleSummaryWorkflow, CtdMetadataWorkflow
from neslter.workflow.stations import StationsWorkflow
from neslter.workflow.elog import EventLogWorkflow
from neslter.workflow.underway import UnderwayWorkflow
from neslter.workflow.nut import NutPlusBottlesWorkflow
from neslter.workflow.chl import ChlWorkflow

def dataframe_response(df, filename, extension='json'):
    if extension is None:
        extension = 'json'
    if extension == 'json':
        return HttpResponse(df.to_json(), content_type='application/json')
    elif extension == 'csv':
        sio = StringIO()
        df.to_csv(sio, index=None, encoding='utf-8')
        csv = sio.getvalue()
        resp = HttpResponse(csv, content_type='text/csv')
        if filename is not None:
            csv_filename = '{}.csv'.format(filename)
            resp['Content-Disposition'] = 'attachment; filename="{}"'.format(csv_filename)
        return resp
    else:
        raise Http404('unsupported file type .{}'.format(extension))   

def workflow_response(workflow, extension=None):
    filename = workflow.filename()
    try:
        df = workflow.get_product()
    except:
        raise
    #except KeyError:
    #    raise Http404('data not found')
    #except IndexError:
    #    raise Http404('data not found')
    return dataframe_response(df, filename, extension)

class CruisesView(View):
    """list cruises. JSON only"""
    def get(self, request):
        cruises = Resolver().cruises()
        return JsonResponse({ 'cruises': cruises })

class CtdCastsView(View):
    def get(self, request, cruise): # JSON only
        wf = CtdMetadataWorkflow(cruise)
        try:
            md = wf.get_product()
        except KeyError:
            raise Http404()
        casts = [int(i) for i in sorted(md['cast'].unique())]
        return JsonResponse({'casts': casts})

class CtdMetadataView(View):
    def get(self, request, cruise, extension=None):
        wf = CtdMetadataWorkflow(cruise)
        return workflow_response(wf, extension)

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

class NutPlusBottlesView(View):
    def get(self, request, cruise, extension=None):
        wf = NutPlusBottlesWorkflow(cruise)
        return workflow_response(wf, extension)

class ChlView(View):
    def get(self, request, cruise, extension=None):
        wf = ChlWorkflow(cruise)
        return workflow_response(wf, extension)
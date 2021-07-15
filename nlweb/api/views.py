from io import StringIO, BytesIO
import os
import glob

from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse, Http404
from django.views import View

import pandas as pd

from config import DATA_ROOT

from neslter.parsing.files import Resolver

from neslter.workflow.ctd import CtdCastWorkflow, CtdBottlesWorkflow, \
        CtdBottleSummaryWorkflow, CtdMetadataWorkflow
from neslter.workflow.stations import StationsWorkflow
from neslter.workflow.elog import EventLogWorkflow
from neslter.workflow.underway import UnderwayWorkflow
from neslter.workflow.nut import NutPlusBottlesWorkflow
from neslter.workflow.chl import ChlWorkflow
from neslter.workflow.hplc import HplcWorkflow

from .utils import df_to_mat

def as_attachment(response, filename):
    response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
    return response

def dataframe_response(df, filename, extension='json'):
    if extension is None:
        extension = 'json'
    if extension == 'json':
        return HttpResponse(df.to_json(), content_type='application/json')
    elif extension == 'csv':
        sio = StringIO()
        df.to_csv(sio, index=None, encoding='utf-8')
        csv = sio.getvalue()
        response = HttpResponse(csv, content_type='text/csv')
        if filename is not None:
            csv_filename = '{}.csv'.format(filename)
            response = as_attachment(response, csv_filename)
        return response
    elif extension == 'mat':
        bio = BytesIO()
        df_to_mat(df, bio, convert_dates=True)
        mat_data = bio.getvalue()
        response = HttpResponse(mat_data, content_type='application/octet-stream')
        if filename is not None:
            mat_filename = '{}.mat'.format(filename)
            response = as_attachment(response, mat_filename)
        return response
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

def cruises(request):
    cruises = Resolver().cruises()
    return JsonResponse({ 'cruises': cruises })

def ctd_casts(request, cruise):
    wf = CtdMetadataWorkflow(cruise)
    try:
        md = wf.get_product()
    except KeyError:
        raise Http404()
    casts = [int(i) for i in sorted(md['cast'].unique())]
    return JsonResponse({'casts': casts})

def ctd_metadata(request, cruise, extension=None):
    wf = CtdMetadataWorkflow(cruise)
    return workflow_response(wf, extension)

def ctd_bottles(request, cruise, extension=None):
    wf = CtdBottlesWorkflow(cruise)
    return workflow_response(wf, extension)

def ctd_bottle_summary(request, cruise, extension=None):
    wf = CtdBottleSummaryWorkflow(cruise)
    return workflow_response(wf, extension)

def ctd_cast(request, cruise, cast, extension=None):
    wf = CtdCastWorkflow(cruise, cast)
    return workflow_response(wf, extension)

def underway(request, cruise, extension=None):
    wf = UnderwayWorkflow(cruise)
    return workflow_response(wf, extension)

def event_log(request, cruise, extension=None):
    wf = EventLogWorkflow(cruise)
    return workflow_response(wf, extension)

def stations(request, cruise, extension=None):
    wf = StationsWorkflow(cruise)
    return workflow_response(wf, extension)

def nut_plus_bottles(request, cruise, extension=None):
    wf = NutPlusBottlesWorkflow(cruise)
    return workflow_response(wf, extension)

def chl(request, cruise, extension=None):
    wf = ChlWorkflow(cruise)
    return workflow_response(wf, extension)

def hplc(request, cruise, extension=None):
    wf = HplcWorkflow(cruise)
    return workflow_response(wf, extension)


def path_exists_or_404(path):
    if not os.path.exists(path):
        raise Http404


def find_readme(basepath):
    for fn in glob.glob(os.path.join(DATA_ROOT, 'corrected', basepath, 'README*')):
        return fn
    for fn in glob.glob(os.path.join(DATA_ROOT, 'raw', basepath, 'README*')):
        return fn
    raise Http404


def readme(*basepath_components):
    basepath = os.path.join(*basepath_components)
    path = find_readme(basepath)
    with open(path, 'r') as fin:
        content = fin.read()
    return HttpResponse(content, content_type="text/plain")


# READMES
def all_readme(request):
    return readme('all')


def nut_readme(request):
    return readme('all', 'nut')


def chl_readme(request):
    return readme('all', 'chl')


def hplc_readme(request):
    return readme('all', 'hplc')


def metadata_readme(request, cruise):
    return readme(cruise, 'metadata')


def ctd_readme(request, cruise):
    return readme(cruise, 'ctd')


def underway_readme(request, cruise):
    return readme(cruise, 'underway')


def events_readme(request, cruise):
    return readme(cruise, 'elog')

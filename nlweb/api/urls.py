from django.urls import path

from . import views

urlpatterns = [
    # READMEs
    path('README', views.all_readme),
    path('nut/README', views.nut_readme),
    path('chl/README', views.chl_readme),
    path('hplc/README', views.hplc_readme),
    path('metadata/<cruise>/README', views.metadata_readme),
    path('ctd/<cruise>/README', views.ctd_readme),
    path('underway/<cruise>/README', views.underway_readme),
    path('events/<cruise>/README', views.events_readme),

    path('cruises', views.cruises, name='cruises'),

    path('ctd/<cruise>/metadata.<extension>', views.ctd_metadata, name='ctd_metadata'),
    path('ctd/<cruise>/metadata', views.ctd_metadata, name='ctd_metadata_json'),

    path('ctd/<cruise>/bottles.<extension>', views.ctd_bottles, name='ctd_bottles'),
    path('ctd/<cruise>/bottles', views.ctd_bottles, name='ctd_bottles_json'),

    path('ctd/<cruise>/bottle_summary.<extension>', views.ctd_bottle_summary, name='ctd_bottlesum'),
    path('ctd/<cruise>/bottle_summary', views.ctd_bottle_summary, name='ctd_bottlesum_json'),

    path('ctd/<cruise>/casts', views.ctd_casts, name='ctd_casts'),

    path('ctd/<cruise>/cast_<int:cast>.<extension>', views.ctd_cast, name='ctd_cast'),
    path('ctd/<cruise>/cast_<int:cast>', views.ctd_cast, name='ctd_cast_json'),

    path('underway/<cruise>.<extension>', views.underway, name='underway'),
    path('underway/<cruise>', views.underway, name='underway_json'),

    path('events/<cruise>.<extension>', views.event_log, name='elog'),
    path('events/<cruise>', views.event_log, name='elog_json'),

    path('stations/<cruise>.<extension>', views.stations, name='stations'),
    path('stations/<cruise>', views.stations, name='stations_json'),

    path('nut/<cruise>.<extension>', views.nut_plus_bottles, name='nut'),
    path('nut/<cruise>', views.nut_plus_bottles, name='nut_json'),

    path('chl/<cruise>.<extension>', views.chl, name='chl'),
    path('chl/<cruise>', views.chl, name='chl_json'),

    path('hplc/<cruise>.<extension>', views.hplc, name='hplc'),
    path('hplc/<cruise>', views.hplc, name='hplc_json'),
]

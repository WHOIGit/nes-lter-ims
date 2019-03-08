from django.urls import path

from . import views

urlpatterns = [
    path('cruises', views.CruisesView.as_view(), name='cruises'),
    path('ctd/<cruise>/metadata.<extension>', views.CtdMetadataView.as_view(), name='ctd_metadata'),
    path('ctd/<cruise>/metadata', views.CtdMetadataView.as_view(), name='ctd_metadata_json'),
    path('ctd/<cruise>/bottles.<extension>', views.CtdBottlesView.as_view(), name='ctd_bottles'),
    path('ctd/<cruise>/bottles', views.CtdBottlesView.as_view(), name='ctd_bottles_json'),
    path('ctd/<cruise>/bottle_summary.<extension>', views.CtdBottleSummaryView.as_view(), name='ctd_bottlesum'),
    path('ctd/<cruise>/bottle_summary', views.CtdBottleSummaryView.as_view(), name='ctd_bottlesum_json'),
    path('ctd/<cruise>/casts', views.CtdCastsView.as_view(), name='ctd_casts'),
    path('ctd/<cruise>/cast_<int:cast>.<extension>', views.CtdCastView.as_view(), name='ctd_cast'),
    path('ctd/<cruise>/cast_<int:cast>', views.CtdCastView.as_view(), name='ctd_cast_json'),
    path('underway/<cruise>.<extension>', views.UnderwayView.as_view(), name='underway'),
    path('underway/<cruise>', views.UnderwayView.as_view(), name='underway_json'),
    path('events/<cruise>.<extension>', views.EventLogView.as_view(), name='elog'),
    path('events/<cruise>', views.EventLogView.as_view(), name='elog_json'),
    path('stations/<cruise>.<extension>', views.StationsView.as_view(), name='stations'),
    path('stations/<cruise>', views.StationsView.as_view(), name='stations_json'),
    path('nut/<cruise>.<extension>', views.NutPlusBottlesView.as_view(), name='nut'),
    path('nut/<cruise>', views.NutPlusBottlesView.as_view(), name='nut_json'),
]

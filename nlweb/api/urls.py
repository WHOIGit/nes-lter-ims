from django.urls import path

from . import views

urlpatterns = [
    path('ctd/<cruise>/metadata.<extension>', views.CtdMetadataView.as_view(), name='ctd_metadata'),
    path('ctd/<cruise>/metadata', views.CtdMetadataView.as_view(), name='ctd_metadata_json'),
    path('ctd/<cruise>/bottles.<extension>', views.CtdBottlesView.as_view(), name='ctd_bottles'),
    path('ctd/<cruise>/bottles', views.CtdBottlesView.as_view(), name='ctd_bottles_json'),
    path('ctd/<cruise>/bottle_summary.<extension>', views.CtdBottleSummaryView.as_view(), name='ctd_bottlesum'),
    path('ctd/<cruise>/bottle_summary', views.CtdBottleSummaryView.as_view(), name='ctd_bottlesum_json'),
    path('ctd/<cruise>/casts', views.CtdCastsView.as_view(), name='ctd_casts'),
    path('ctd/<cruise>/cast<int:cast>.<extension>', views.CtdCastView.as_view(), name='ctd_cast'),
    path('ctd/<cruise>/cast<int:cast>', views.CtdCastView.as_view(), name='ctd_cast_json'),
    path('underway/<cruise>.<extension>', views.UnderwayView.as_view(), name='underway'),
    path('underway/<cruise>', views.UnderwayView.as_view(), name='underway_json'),
]
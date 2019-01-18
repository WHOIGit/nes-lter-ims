from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('ctd/<cruise>/metadata', views.CtdMetadataView.as_view(), name='ctd_metadata_json'),
    path('ctd/<cruise>/metadata.<extension>', views.CtdMetadataView.as_view(), name='ctd_metadata'),
    path('ctd/<cruise>/bottles', views.CtdBottlesView.as_view(), name='ctd_bottles_json'),
    path('ctd/<cruise>/bottles.<extension>', views.CtdBottlesView.as_view(), name='ctd_bottles'),
    path('ctd/<cruise>/bottle_summary', views.CtdBottleSummaryView.as_view(), name='ctd_bottlesum_json'),
    path('ctd/<cruise>/bottle_summary.<extension>', views.CtdBottleSummaryView.as_view(), name='ctd_bottlesum'),
    path('ctd/<cruise>/cast/<int:cast>', views.CtdCastView.as_view(), name='ctd_cast_json'),
    path('ctd/<cruise>/cast/<int:cast>.<extension>', views.CtdCastView.as_view(), name='ctd_cast'),
]
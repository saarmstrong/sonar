from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^$', views.dashboard, name='dashboard'),
    url(r'^report/$', views.report, name='report'),
    url(r'^signage/$', views.signage, name='signage'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/(?P<day>[0-9]{2})/$', views.day_view, name='day_view'),
    url(r'^(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/$', views.month_view, name='month_view'),

    # Login demo for PoC
    #url(r'^login/$', views.login_demo_view, name='login_demo')
]

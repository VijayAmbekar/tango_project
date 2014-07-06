from django.conf.urls import patterns, include, url
import views

urlpatterns = patterns('',
	url(r'^$', views.index),
	url(r'^about/$', views.about),
	url(r'^add_category/$', views.add_category),
	url(r'^category/(?P<category_name_url>\w+)/$', views.category),
	url(r'^category/(?P<category_name_url>\w+)/add_page/$',views.add_page),
	url(r'^register/$', views.register),
	url(r'^login/$', views.user_login),
	url(r'^restricted/$', views.restricted),
	url(r'^logout/$', views.user_logout),
	url(r'^profile/$', views.profile),
	url(r'^goto/$', views.track_url),
	url(r'^like_category/$', views.like_category),
	url(r'^suggest_category/$',views.suggest_category),
	url(r'^auto_add_page/$', views.auto_add_page),
)
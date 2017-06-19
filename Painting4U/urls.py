from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'Application.views.home'),
    
 
    
    url(r'^cuadrosTitle/', 'Application.views.buscaCuadroPorTitulo'),
    url(r'^cuadrosAuthor/', 'Application.views.buscaCuadroPorAutor'),
    url(r'^cuadrosDescription/', 'Application.views.buscaCuadroPorDescripcion'),
    url(r'^cuadrosKeyword/(?P<descripcion>.*)/', 'Application.views.buscaCuadroPorPalabraClave'),
    
    url(r'^cuadro/(?P<autor>.*)/(?P<titulo>.*)/', 'Application.views.getCuadro'),
    url(r'^autor/(?P<autor>.*)/', 'Application.views.getAutor'),


    # Examples:
    # url(r'^$', 'Painting4U.views.home', name='home'),
    # url(r'^Painting4U/', include('Painting4U.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)

#encoding:utf-8
# Create your views here.
from django.shortcuts import render_to_response
from django.template.context import RequestContext

from Application import util
from forms import CuadroForm, DescripcionForm
from Application.forms import AutorForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
def home(request):
    
    return render_to_response('index.html',RequestContext(request,{"agenda":util.getAgendaCultural()}))


def buscaCuadroPorTitulo(request):
    if request.method=='POST' or request.GET.get('busqueda') is not None:
        
        formulario=CuadroForm(request.POST)
        if formulario.is_valid():
            titulo=formulario.cleaned_data['titulo']
        elif request.GET.get('busqueda') is not None:
            print "meh"
            titulo = request.GET.get('busqueda')
        else:
            return render_to_response('cuadro_form.html',RequestContext(request,{'formulario':formulario}))
        print titulo
        cuadros = util.buscaCuadroPorTitulo(titulo)
        page=request.GET.get('page', 1)
        paginator=Paginator(cuadros, 6)
        try:
            cuadrosPaginados=paginator.page(page)
        except PageNotAnInteger:
            cuadrosPaginados=paginator.page(1)
        except EmptyPage:
            cuadrosPaginados=paginator.page(paginator.num_pages)
        print cuadros
        return render_to_response('cuadros.html',{'lista':cuadrosPaginados,'busqueda':titulo,'por':'título'})
    else:
        formulario=CuadroForm()

    return render_to_response('cuadro_form.html',RequestContext(request,{'formulario':formulario}))    

def buscaCuadroPorAutor(request):
    if request.method=='POST'  or request.GET.get('busqueda') is not None:
        
        formulario=AutorForm(request.POST)
        if formulario.is_valid():
            autor=formulario.cleaned_data['autor']
        elif request.GET.get('busqueda') is not None:
            print "meh"
            autor = request.GET.get('busqueda')
        else:
            return render_to_response('cuadro_form.html',RequestContext(request,{'formulario':formulario}))
        print autor
        cuadros = util.buscaCuadroPorAutor(autor)
        page=request.GET.get('page', 1)
        paginator=Paginator(cuadros, 6)
        try:
            cuadrosPaginados=paginator.page(page)
        except PageNotAnInteger:
            cuadrosPaginados=paginator.page(1)
        except EmptyPage:
            cuadrosPaginados=paginator.page(paginator.num_pages)
        print cuadros
        return render_to_response('cuadros.html',{'lista':cuadrosPaginados,'busqueda':autor,'por':'autor'})
    else:
        formulario=AutorForm()

    return render_to_response('cuadro_form.html',RequestContext(request,{'formulario':formulario}))

def getCuadro(request,autor,titulo):
    cuadro = util.getCuadroPorTituloYAutor(titulo,autor)
    more=util.buscarMasParecidos(titulo,autor)
    return render_to_response('cuadro.html', {'dict': cuadro,'more':more})

def getAutor(request,autor):
    cuadros = util.buscaCuadroPorAutor(autor,numResultados=3)
    wiki=util.getWikiAutor(autor)
    keywords=util.palabrasClave(autor)
    return render_to_response('autor.html', {'lista': cuadros,'wiki':wiki,'autor':autor,'keywords':keywords})


def buscaCuadroPorDescripcion(request):
    if request.method=='POST'  or request.GET.get('busqueda') is not None:
        
        formulario=DescripcionForm(request.POST)
        if formulario.is_valid():
            descripcion=formulario.cleaned_data['descripcion']
        elif request.GET.get('busqueda') is not None:
            print "meh"
            descripcion = request.GET.get('busqueda')
        else:
            return render_to_response('cuadro_form.html',RequestContext(request,{'formulario':formulario}))
        print descripcion
        cuadros = util.highlights(descripcion)
        page=request.GET.get('page', 1)
        paginator=Paginator(cuadros, 6)
        try:
            cuadrosPaginados=paginator.page(page)
        except PageNotAnInteger:
            cuadrosPaginados=paginator.page(1)
        except EmptyPage:
            cuadrosPaginados=paginator.page(paginator.num_pages)
        print cuadros
        return render_to_response('cuadro_descripcion.html',{'lista':cuadrosPaginados,'busqueda':descripcion,'por':'descripcion'})
    else:
        formulario=DescripcionForm()

    return render_to_response('cuadro_form.html',RequestContext(request,{'formulario':formulario}))

def buscaCuadroPorPalabraClave(request,descripcion):
    cuadros = util.highlights(descripcion)
    return render_to_response('cuadro_descripcion.html',{'lista':cuadros,'busqueda':descripcion,'por':'descripción'})

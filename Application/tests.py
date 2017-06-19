#encoding:utf-8
"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from pattern.web import Wikipedia
from bs4 import BeautifulSoup
from Application import util
import whoosh
from whoosh.qparser import QueryParser
import os
import urllib2
import pickle
from whoosh.analysis.analyzers import StemmingAnalyzer
from whoosh.highlight import UppercaseFormatter
import feedparser
from datetime import datetime

baseUrl="https://www.wikiart.org"


def testWikipedia(palabra):
    """
    Obtiene el articulo de la wikipedia
    """    
    engine=Wikipedia(license=None, throttle=5.0)
    resultados=engine.search(palabra)

    print resultados.plaintext()
    return resultados
    
def testBS():
    """
    Abre la pagina principal y obtiene todas las urls de los estilos en una lista
    """    
    util.abrir_url_recarga(baseUrl+"/en/paintings-by-style","ficheros/wikiart.txt",True)
    f = open ("ficheros/wikiart.txt", "r")
    s = f.read()
    f.close()
    bp=BeautifulSoup(s,"html.parser")
    
    menu=bp.find("ul","dictionaries-list")
    estilos=menu.find_all("li","dottedItem")
    urls=[]
    for estilo in estilos:
        link=estilo.a.get("href")
        if link is not None:
            link=baseUrl+link
        else:
            continue
        print link
        urls.append(link)
    return urls
    
def testCorriente(linkCorriente):
    """
    Recibe un link de la corriente/estilo y devuelve una lista con los cuadros de ese estilo
    """   
    util.abrir_url_recarga(linkCorriente,"ficheros/corriente.txt",True)
    f = open ("ficheros/corriente.txt", "r")
    s = f.read()
    f.close()
    bp=BeautifulSoup(s,"html.parser")
    cuadros=bp.find_all("ul","title")
    enlacesCuadros=[]
    print cuadros
    for cuadro in cuadros:
        enlace=baseUrl+cuadro.find_next("a").get("href")
        print enlace
        enlacesCuadros.append(enlace)
    return enlacesCuadros  

def testCuadro(linkCuadro):
    """
    Dado el link de un cuadro, devuelve un diccionario con su info
    """
    util.abrir_url_recarga(linkCuadro,"ficheros/cuadro.txt",True)
    f = open ("ficheros/cuadro.txt", "r")
    s = f.read()
    f.close()
    bs=BeautifulSoup(s,"html.parser")
    cuadro={}
    info=bs.find("div","info")
    cuadro["titulo"]=info.find("h1").string.strip()
    cuadro["autor"]=info.find("a","artist-name").string.strip()
    cuadro["autorLink"]=baseUrl+info.find("a","artist-name").get("href").strip()
    cuadro["link"]=linkCuadro.strip()
    cuadro["imagen"]=info.find_previous("img",itemprop="image").get("src").strip()
    infos=info.find_all("div","info-line")
    for i in infos:
        span=i.find("span")
        if span is None:
            continue
        if span.string=="Style:":
            cuadro["corriente"]=i.find("a").string.strip()
        elif span.string=="Location:":
            cuadro["localizacion"]=i.text.replace("Location:","").strip()
        
    cuadro["descripcion"]=bs.find("span",itemprop="description")
    if cuadro.get("descripcion") is not None:
        cuadro["descripcion"]=cuadro["descripcion"].string.strip()
    #cuadro["autorLink"]=testBuscaAutorLink(linkCuadro)
    print cuadro
    return cuadro  
    
def testWhooshCrearIndice():
    """
    Crea el índice de whoosh
    """
    stem=StemmingAnalyzer()
    schema = whoosh.fields.Schema(titulo=whoosh.fields.TEXT(stored=True), 
                                  autor=whoosh.fields.TEXT(stored=True),
                                  autorLink=whoosh.fields.ID(stored=True),
                                  imagen=whoosh.fields.ID(stored=True), 
                                  link=whoosh.fields.ID(stored=True), 
                                  descripcion=whoosh.fields.TEXT(stored=True,analyzer=stem),
                                  localizacion=whoosh.fields.ID(stored=True),
                                  corriente=whoosh.fields.ID(stored=True))
    if not os.path.exists("ficheros/index"):
        os.mkdir("ficheros/index")
    whoosh.index.create_in("ficheros/index", schema)
    
def testBuscaAutorLink(cadena):
    try:    
        f = urllib2.urlopen(cadena)
        #urllib.urlretrieve(url,file)
        #<item>\s*<title>(.*)\s*<link>(.*)</link>\s*<description>.*</description>...</author>\s*(<category>.*</category>)?\s*<guid.*</guid>\s*<pubdate>...
        soup = BeautifulSoup(f, 'html.parser')
        
        tds=soup.find_all('a','artist-name')
        link1=baseUrl+tds[0]["href"]
        #enlace a wikiart
        return link1
    
        f2 = urllib2.urlopen(link1)
        soup2 = BeautifulSoup(f2, 'html.parser')
        tds2=soup2.find_all('a','truncate external')
        #print res
        f.close() 
        #enlace a wikipedia
        return tds2[0]["href"]
         
    except urllib2.HTTPError, e:    
        print "Ocurrio un error"    
        print e.code 
    except urllib2.URLError, e:    
        print "Ocurrio un error"    
        print e.reason
    return
def testWhooshGuardarCuadro(writer,cuadro):
    """
    Dado el diccionario de un cuadro, lo carga en el indice
    """    
    writer.add_document(titulo=cuadro.get("titulo"), 
                              autor=cuadro.get("autor"),
                              autorLink=cuadro.get("autorLink"),
                              imagen=cuadro.get("imagen"),
                              link=cuadro.get("link"),
                              descripcion=cuadro.get("descripcion") if cuadro.get("descripcion") is not None else u'',
                              localizacion=cuadro.get("localizacion"), 
                              corriente=cuadro.get("corriente"))
    
def testWhooshGuardarDatos(cuadros):
    """
    Dado una lista de diccionarios de cuadros, lo guarda en el indice
    """    
    ix = whoosh.index.open_dir("ficheros/index")
    writer = ix.writer()
    for cuadro in cuadros:
        testWhooshGuardarCuadro(writer, cuadro)
    writer.commit()
    
def buscaCuadroPorTitulo(cadena): 
    ix=whoosh.index.open_dir("ficheros/index")
    parser=QueryParser("titulo", ix.schema)
    myquery=parser.parse(cadena)
    resultados=[]
    with ix.searcher() as searcher:
        results=searcher.search(myquery)
        for r in results:
            resultados.append({"titulo":r.get("titulo"), "autor":r.get("autor"),"autorLink":r.get("autorLink"),"imagen":r.get("imagen"),"link":r.get("link"),"descripcion":r.get("descripcion"),"localizacion":r.get("localizacion"),"corriente":r.get("corriente")})
    for r in resultados:
        print "["+r["titulo"]+", "+r["link"]+"]"
    return results

def buscaCuadroPorAutor(cadena):
    ix=whoosh.index.open_dir("ficheros/index")
    parser=QueryParser("autor", ix.schema)
    myquery=parser.parse(cadena)
    resultados=[]
    with ix.searcher() as searcher:
        results=searcher.search(myquery)
        for r in results:
            resultados.append({"titulo":r.get("titulo"), "autor":r.get("autor"),"autorLink":r.get("autorLink"),"imagen":r.get("imagen"),"link":r.get("link"),"descripcion":r.get("descripcion"),"localizacion":r.get("localizacion"),"corriente":r.get("corriente")})
    for r in resultados:
        print "["+r["titulo"]+", "+r["link"]+"]"
    return results

def testBuscarMasParecidos(autor):
    """
    Busca resultados más parecidos a los buscados(ahora mismo busca por el autor)
    """
    ix=whoosh.index.open_dir("ficheros/index")
    parser=QueryParser("autor", ix.schema)
    myquery=parser.parse(autor)
    with ix.searcher() as searcher:
        results=searcher.search(myquery)
        first_hit = results[0]
        print first_hit
        more_results = first_hit.more_like_this("autor")
        print more_results

def testBuscarPalabrasClave(autor):
    """
    Busca las palabras clave del texto que acompaña al cuadro

    """
    ix=whoosh.index.open_dir("ficheros/index")
    parser=QueryParser("autor", ix.schema)
    myquery=parser.parse(autor)
    with ix.searcher() as searcher:
        results=searcher.search(myquery)
        print results
        keywords = [keyword for keyword, score
                in results.key_terms("descripcion", numterms=4)]
    return keywords

def testHighlights(autor): 
    """
    Busca los fragmentos resaltados a los que pertenecen los términos buscados
    """
    ix=whoosh.index.open_dir("ficheros/index")
    parser=QueryParser("descripcion", ix.schema)
    myquery=parser.parse(autor)
    highs=[]
    with ix.searcher() as searcher:
        results=searcher.search(myquery)
        results.formatter=UppercaseFormatter()
        for hit in results:
            if hit["descripcion"] is not None:
                resalto=hit.highlights("descripcion")
                highs.append(resalto)
            else:
                print "No hay descripcion del cuadro"
    return highs
def testGuardarDatosEnFichero():
    """
    Guarda los cuadros en un fichero, para no tener que pedir las urls cada vez
    """
    todo=[]
    linkCorrientes=util.getCorrientes()
    for linkCorriente in linkCorrientes:
        linkCuadros=util.getCuadrosCorrientes(linkCorriente)
        for linkCuadro in linkCuadros:
            cuadro=util.getCuadro(linkCuadro)
            todo.append(cuadro)

    with open('ficheros/dump.txt', 'wb') as fp:
        pickle.dump(todo, fp)
        
        
def testWhooshGuardarDatosFichero():
    """
    Coge una lista de diccionarios de cuadros de un fichero, lo guarda en el indice
    """    
    ix = whoosh.index.open_dir("ficheros/index")
    writer = ix.writer()
    with open ('ficheros/dump.txt', 'rb') as fp:
        cuadros = pickle.load(fp)
        for cuadro in cuadros:
            testWhooshGuardarCuadro(writer, cuadro)
    writer.commit()


def testCultural():
    """
    Coge un rss y lo muestra
    """
    url="http://elpais.com/tag/rss/arte/a/"
    feed=feedparser.parse(url)
    for entrada in feed.entries:
        print entrada["title"]
        print entrada["link"]
        print entrada["description"]
        print datetime.strptime(entrada["published"], "%a, %d %b %Y %H:%M:%S +0100")
    return feed



def testAgenda():
    print util.getAgendaCultural()
if __name__=="__main__":
    #print testWikipedia('Cervantes').media
    #No usar este!! Ya estan guardados los datos en el fichero, con esto vuelve a cargarlo con bs
    #testGuardarDatosEnFichero()
    #testBS()
    #testCorriente("https://www.wikiart.org/en/paintings-by-style/metaphysical-art")
    #testCuadro("https://www.wikiart.org/en/alphonse-allais/first-communion-of-anaemic-young-girls-in-the-snow")
    #testCuadro("https://www.wikiart.org/en/leonardo-da-vinci/mona-lisa")
    #testCuadro("https://www.wikiart.org/en/claude-monet/madame-monet-and-child")
    #testBuscaAutorLink("https://www.wikiart.org/en/alphonse-allais/first-communion-of-anaemic-young-girls-in-the-snow")

    #testWhooshCrearIndice()
    
    #testWhooshGuardarDatosFichero()
    #testBuscarMasParecidos("Francisco")
    #print testBuscarPalabrasClave("vinci")
    #print testHighlights("portrait")

    #buscaCuadroPorAutor("First")
    #testCultural()
    testAgenda()
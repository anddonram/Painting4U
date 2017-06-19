#encoding:utf-8
'''
Created on 31 dic. 2016

@author: Andres
'''
from pattern.web import Wikipedia
from os.path import join,dirname,exists
from os import mkdir
import urllib
from bs4 import BeautifulSoup
import whoosh.fields
import whoosh.index
from whoosh.qparser import QueryParser,MultifieldParser
from whoosh.analysis.analyzers import StemmingAnalyzer
from whoosh.highlight import UppercaseFormatter
import random
from datetime import datetime
import feedparser
import pickle


PROJECT_DIR = dirname(__file__).decode('latin1')
baseUrl="https://www.wikiart.org"
indexPath=join(PROJECT_DIR,"ficheros/index")

def getWikiAutor(nombre):
    engine=Wikipedia(license=None, throttle=5.0, language='en')
    return engine.search(nombre)


def abrir_url_recarga(url,fichero,recarga=False):
    try:
        if os.path.exists(fichero):
            if recarga == True:
                urllib.urlretrieve(url,fichero)
        else:
            urllib.urlretrieve(url,fichero)
        return fichero
    except:
        print  "Error al conectarse a la página"
        return None


def getCorrientes():
    """
    Abre la pagina principal y obtiene todas las urls de los estilos en una lista
    """    
    abrir_url_recarga(baseUrl+"/en/paintings-by-style","ficheros/wikiart.txt",True)
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

def getCuadrosCorrientes(linkCorriente):
    """
    Recibe un link de la corriente/estilo y devuelve una lista con los cuadros de ese estilo
    """   
    abrir_url_recarga(linkCorriente,"ficheros/corriente.txt",True)
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

def getCuadro(linkCuadro):
    """
    Dado el link de un cuadro, devuelve un diccionario con su info
    """
    abrir_url_recarga(linkCuadro,"ficheros/cuadro.txt",True)
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

    print cuadro
    return cuadro  

def crearIndice():
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

    if not exists(indexPath):
        mkdir(indexPath)
    whoosh.index.create_in(indexPath, schema)
    
def guardarCuadrosEnIndice():
    """
    Dado una lista de diccionarios de cuadros, lo guarda en el indice
    """    
    ix = whoosh.index.open_dir(indexPath)
    writer = ix.writer()
    linkCorrientes=getCorrientes()
    for linkCorriente in linkCorrientes:
        linkCuadros=getCuadrosCorrientes(linkCorriente)
        for linkCuadro in linkCuadros:
            cuadro=getCuadro(linkCuadro)
            writer.add_document(titulo=cuadro.get("titulo"), 
                              autor=cuadro.get("autor"),
                              autorLink=cuadro.get("autorLink"),
                              imagen=cuadro.get("imagen"),
                              link=cuadro.get("link"),
                              descripcion=cuadro.get("descripcion") if cuadro.get("descripcion") is not None else u'',
                              localizacion=cuadro.get("localizacion"), 
                              corriente=cuadro.get("corriente"))
    writer.commit()
def guardarDatosEnFichero():
    """
    Guarda los cuadros en un fichero, para no tener que pedir las urls cada vez
    """
    todo=[]
    linkCorrientes=getCorrientes()
    for linkCorriente in linkCorrientes:
        linkCuadros=getCuadrosCorrientes(linkCorriente)
        for linkCuadro in linkCuadros:
            cuadro=getCuadro(linkCuadro)
            todo.append(cuadro)

    with open('ficheros/dump.txt', 'wb') as fp:
        pickle.dump(todo, fp)
        
def whooshGuardarCuadro(writer,cuadro):
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
        
def whooshGuardarDatosFichero():
    """
    Coge una lista de diccionarios de cuadros de un fichero, lo guarda en el indice
    """    
    ix = whoosh.index.open_dir(indexPath)
    writer = ix.writer()
    with open ('ficheros/dump.txt', 'rb') as fp:
        cuadros = pickle.load(fp)
        for cuadro in cuadros:
            whooshGuardarCuadro(writer, cuadro)
    writer.commit()
    
def buscaCuadroPorTitulo(cadena,numResultados=None): 
    ix=whoosh.index.open_dir(indexPath)
    parser=QueryParser("titulo", ix.schema)
    myquery=parser.parse(cadena)
    resultados=[]
    with ix.searcher() as searcher:
        results=searcher.search(myquery, limit=numResultados)
        for r in results:
            resultados.append(hitToDict(r))
    return resultados

def buscaCuadroPorAutor(cadena,numResultados=None):
    ix=whoosh.index.open_dir(indexPath)
    parser=QueryParser("autor", ix.schema)
    myquery=parser.parse(cadena)
    resultados=[]
    with ix.searcher() as searcher:
        results=searcher.search(myquery, limit=numResultados)
        for r in results:
            resultados.append(hitToDict(r))
    return resultados

def getCuadroPorTituloYAutor(titulo,autor,numResultados=None):
    ix=whoosh.index.open_dir(indexPath)
    parser=MultifieldParser(["titulo","autor"], ix.schema)
    myquery=parser.parse('titulo:'+titulo+' AND autor:'+autor)

    results = ix.searcher().search(myquery, limit=numResultados)
    if len(results)>0:
        r = results[0]
    else:
        r={"titulo":"No se encontró el cuadro"}
    return hitToDict(r)

def highlights(palabra,numResultados=None):
    """
    Busca los fragmentos resaltados a los que pertenecen los términos buscados
    """
    ix=whoosh.index.open_dir(indexPath)
    parser=QueryParser("descripcion", ix.schema)
    myquery=parser.parse(palabra)
    highs=[]
    with ix.searcher() as searcher:
        results=searcher.search(myquery, limit=numResultados)
        results.formatter=UppercaseFormatter()
        for hit in results:
            print hit
            if hit["descripcion"] is not None:
                resalto=hit.highlights("descripcion")
                cuadro=hitToDict(hit)
                cuadro["highlight"]=resalto
                highs.append(cuadro)
                #print resalto
            else:
                print "No hay descripcion del cuadro"
    return highs

def hitToDict(r):
    """
    Pasa un resultado (hit) de una búsqueda a un diccionario
    """
    return {"titulo":r.get("titulo"), "autor":r.get("autor"),
            "autorLink":r.get("autorLink"),"imagen":r.get("imagen"),
            "link":r.get("link"),"descripcion":r.get("descripcion"),
            "localizacion":r.get("localizacion"),"corriente":r.get("corriente")}
    
def palabrasClave(autor):
    """
    Busca las palabras clave que definen al autor, en función de las descripciones de sus cuadros
    """
    ix=whoosh.index.open_dir(indexPath)
    parser=QueryParser("autor", ix.schema)
    myquery=parser.parse(autor)
    with ix.searcher() as searcher:
        results=searcher.search(myquery)
        print results
        keywords = [keyword for keyword, score
                in results.key_terms("descripcion", numterms=4)]
    return keywords

def buscarMasParecidos(titulo,autor,numResultados=None):
    """
    Busca resultados más parecidos a los buscados(ahora mismo busca por el autor)
    De los 10 más parecidos, coge 3 al azar
    """
    ix=whoosh.index.open_dir(indexPath)
    parser=MultifieldParser(["titulo","autor"], ix.schema)
    myquery=parser.parse('titulo:'+titulo+' AND autor:'+autor)

    results = ix.searcher().search(myquery, limit=numResultados)
    resultados=[]
    if len(results)>0:
        first_hit = results[0]
        more_results = first_hit.more_like_this("autor")
        for r in more_results:
            resultados.append(hitToDict(r))
        return random.sample(resultados,3)
    else:
        return []
    

def getAgendaCultural():
    """
    Coge un rss y lo devuelve como list de dict
    """
    url="http://elpais.com/tag/rss/arte/a/"
    
    resultados=[]
    try:
        feed=feedparser.parse(url)
        for entrada in feed.entries:
            resultados.append(feedToDict(entrada))
    finally:
        print "agenda cargada"
    return resultados
    
def feedToDict(entrada):
    """
    Coge un feed y lo pasa a un diccionario
    """
    result={}
    result["title"]=entrada["title"]
    result["link"]=entrada["link"]
    result["description"]= entrada["description"]
    result["date"]=datetime.strptime(entrada["published"], "%a, %d %b %Y %H:%M:%S +0100")
    return result
if __name__=="__main__":
    #crearIndice()
    #guardarCuadrosEnIndice()
    #getCuadro("https://www.wikiart.org/en/leonardo-da-vinci/mona-lisa")
    #print getCuadroPorTituloYAutor("Last Judgment","Fra Angelico")
    print highlights("lisa")
    #whooshGuardarDatosFichero()
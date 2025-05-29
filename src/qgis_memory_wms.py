# -*- coding: utf-8 -*-
"""
Created on 2025.03.07

@author: Peter Szutor - szppaks@gmail.com
"""
from qgis.core import *
# Supply path to qgis install location
QgsApplication.setPrefixPath("/path/to/qgis/installation", True)
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from urllib.parse import urlparse, parse_qs
import os.path
import tempfile
import time
from qgis.core import QgsProject, QgsMapRendererParallelJob, QgsMapSettings
from qgis.PyQt.QtGui import QImage, QPainter,QColor
from qgis.PyQt.QtCore import QSize,QBuffer,QIODevice
import os
import http.server
import socketserver
import os
import threading
import shutil
import psutil
import sys
process = psutil.Process(os.getpid())
from lxml import etree

from qgis.core import QgsProject, QgsRectangle

verbosemode=0
def vprint(*args):
    if verbosemode>0:
        print(*args)

def extent_layers(ml):
    combined_extent = None
    
    # Iterálunk az összes betöltött rétegen
    for layer in ml.values():
        # Ellenőrizzük, hogy a réteg rendelkezik-e érvényes kiterjedéssel
        if layer.isValid():
            layer_extent = layer.extent()
            if combined_extent is None:
                # Az első érvényes réteg kiterjedésével inicializáljuk
                combined_extent = QgsRectangle(layer_extent)
            else:
                # Egyesítjük a jelenlegi réteg kiterjedését a combined_extent-tel
                combined_extent.combineExtentWith(layer_extent)
    
    # Kiírjuk az eredményt, ha van érvényes kiterjedés
    if combined_extent is not None:
        vprint(f"Összesített kiterjedés: {combined_extent.toString()}")
    else:
        vprint("Nincs érvényes réteg a projektben.")
    return combindex_extent.toString()


def generate_wms_111_getcapabilities(layer_name, layer_title, bbox, srs="EPSG:4326"):
    nsmap = {
        None: "http://www.opengis.net/wms",
    'xlink': "http://www.w3.org/1999/xlink"
    }
    base_url='http://127.0.0.1:'+str(port).strip()+'/wms'
    root = etree.Element("WMT_MS_Capabilities", version="1.1.1", nsmap=nsmap)

    # Service section
    service = etree.SubElement(root, "Service")
    etree.SubElement(service, "Name").text = "WMS"
    etree.SubElement(service, "Title").text = "My WMS 1.1.1 Service"
    online_resource = etree.SubElement(service, "OnlineResource")
    online_resource.set("{http://www.w3.org/1999/xlink}href", base_url)


    # Capability section
    capability = etree.SubElement(root, "Capability")

    # Request section
    request = etree.SubElement(capability, "Request")
    for name, mime in [("GetCapabilities", "application/vnd.ogc.wms_xml"), ("GetMap", "image/png"),("GetStyles","application/vnd.ogc.sld+xml")]:
        req = etree.SubElement(request, name)
        etree.SubElement(req, "Format").text = mime
        dcp = etree.SubElement(req, "DCPType")
        http = etree.SubElement(dcp, "HTTP")
        get = etree.SubElement(http, "Get")

        online_resource = etree.SubElement(get, "OnlineResource")
        online_resource.set("{http://www.w3.org/1999/xlink}href", base_url)
    for lactual in list(maplayers.values()):
        layer_name=lactual.name()
        layer_title=lactual.name()
        layer1 = etree.SubElement(capability, "Layer")
        # layer1 = etree.SubElement(layer, "Layer")
        etree.SubElement(layer1, "Name").text = layer_name
        etree.SubElement(layer1, "Title").text = layer_title
        crs = project.crs()
        auth_id = crs.authid()
        if auth_id and len(auth_id)>0:
            etree.SubElement(layer1, "SRS").text = auth_id

    # BoundingBox in 1.1.1 style
    crs = project.crs()
    auth_id = crs.authid()
    if len(auth_id)>0:
        bbox_tag = etree.SubElement(capability, "BoundingBox", SRS=auth_id,
                                minx=str(total_extent.split(',')[0]), miny=str(total_extent.split(',')[1]),
                                maxx=str(total_extent.split(',')[2]), maxy=str(total_extent.split(',')[3]))
    else:
        bbox_tag = etree.SubElement(capability, "BoundingBox", 
                                minx=str(total_extent.split(',')[0]), miny=str(total_extent.split(',')[1]),
                                maxx=str(total_extent.split(',')[2]), maxy=str(total_extent.split(',')[3]))

    return etree.tostring(root, pretty_print=True, xml_declaration=True, encoding="UTF-8")

def get_sld_from_layer(layer):
    # buffer = QBuffer()
    # buffer.open(QIODevice.ReadWrite)
    try:
        with tempfile.NamedTemporaryFile(suffix=".sld", delete=False) as tmp_file:
            temp_path = tmp_file.name
            layer.saveSldStyle(temp_path)
            with open(temp_path, "r", encoding="utf-8") as f:
                sld_xml = f.read()
    except:
        try:
            os.remove(temp_path)
        except:
            print('Warning: TMP file removing unsuccessfull')
    # buffer.seek(0)
    # sld_xml = buffer.readAll().data().decode("utf-8")
    # buffer.close()
    return sld_xml


def maprender(layer_names,width,height,bbox,crs_param):
    # Write your code here to load some layers, use processing
    # algorithms, etc.
    try:
        kezdes=time.time()
        map_settings = QgsMapSettings()

        vprint('Rétegnevek',layer_names)
        layers = []
        if len(layer_names)>0 and layer_names[0]=='all':
            layers=maplayers.values()
        elif len(layer_names)>0:
            for name in layer_names:
                found_layers = project.mapLayersByName(name)
                if found_layers:
                    layers.append(found_layers[0])
        if len(layers)==0:
            img_data=None
        print('BBOX,CRS:',bbox,type(bbox),crs_param)
        # Térkép beállítások
        map_settings.setLayers(layers)
        map_settings.setOutputSize(QSize(width, height))
        if crs_param and len(crs_param)>0:
            map_settings.setDestinationCrs(QgsCoordinateReferenceSystem(crs_param))
            
        bbox1=str(bbox).replace('[','').replace(']','')
        bbox_values = [float(coord) for coord in bbox1.split(',')]
        rect = QgsRectangle(*bbox_values)
        map_settings.setExtent(rect)
        print('Rendering map: (bbox,width,height)',bbox_values,width,height)
        #     print(extent)
        #     # Nagyítás a réteg terjedelmére
        # map_settings.setExtent(total_extent)

        job = QgsMapRendererParallelJob(map_settings)
        job.start()
        image=job.renderedImage()
        job.waitForFinished()
        image=job.renderedImage()
        # job.renderingFinished.connect(lambda: painter.end())
        buffer = QBuffer()
        buffer.open(QIODevice.ReadWrite)        
        # image.save(image_path)        
        image.save(buffer,'PNG')   
        image.save('lastmap.png')
        buffer.seek(0)
        img_data = buffer.readAll().data()
        print('rendering time:',time.time()-kezdes)
    except Exception as e:
        print('Rendering fault:')
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
    return img_data

class MyTCPServer(socketserver.TCPServer):
    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.timeout = 20

    def handle_timeout(self):
        print("A szerver időkorlátja lejárt, nincs bejövő kapcsolat.")

class SimpleHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        try:
            if  self.path == '/leall':
                self.server.server_close()
                self.server.shutdown()
            if self.path == '/favicon.ico':
                # Válasz küldése 204 No Content státuszkóddal
                self.send_response(204)
                self.end_headers()
            else:
                vprint('selfpath',self.path)
                parsed_url = urlparse(self.path)
                query_params = parse_qs(parsed_url.query)
                query_params = {k.upper(): v for k, v in query_params.items()}
                # Ellenőrizzük, hogy WMS GetMap kérést kapunk-e
                service = query_params.get("SERVICE", [None])[0]
                vprint('QUERY PARAMS',query_params)
                request_param = query_params.get("REQUEST", [None])[0]
                vprint(request_param)
                if service is not None and service.upper() == "WMS" and \
                   request_param is not None and request_param.upper() == "GETMAP":
                    # Ide jön a WMS GetMap feldolgozás
                    try:
                        params = { key.upper(): values[0] for key, values in query_params.items() }
                        if params.get("LAYERS"):
                            layer_names = params.get("LAYERS").split(",")
                        else:
                            layer_names=None
                        if params.get('CRS') or params.get('SRS'):
                            crs_param = params.get("CRS", params.get("SRS", ["EPSG:4326"]))
                        else:
                            crs_param = None
                        if params.get('BBOX'):
                            bbox = list(map(float, params["BBOX"].split(",")))
                        else:
                            bbox=total_extent
                        if params.get('WIDTH'):
                            width = int(params["WIDTH"])
                        else:
                            width=800
                        if params.get('HEIGHT'):
                            height = int(params["HEIGHT"])
                        else:
                            height=600
                        if params.get("FORMAT"):
                            format_param = params.get("FORMAT", ["image/png"])
                        else:
                            format_param="image/png"
    
                        
                        # Map render függvény meghívása a kapott paraméterekkel
                        # rendered_image = maprender(params)
                        map_result=maprender(layer_names,width,height,bbox,crs_param)
                        if map_result==None:
                            self.send_response(400)
                            self.end_headers()
                            self.wfile.write(b"Nincs megadva ervenyes reteg.")
                            return
                            
                        self.send_response(200)
                        self.send_header("Content-type", format_param)
                        self.end_headers()
                        self.wfile.write(map_result)                    
                        memory_usage = process.memory_info().rss
                        print(f"Memóriahasználat hívásnál: {memory_usage / 1024 ** 2:.2f} MB")
                    except Exception as e:
                        self.send_error(500, f"Internal Server Error: {str(e)}")                        
                elif request_param is not None and request_param.upper() == "GETSTYLES":
                    params = { key.upper(): values[0] for key, values in query_params.items() }
                    layer_names = query_params.get("LAYER", params.get("LAYERS", [""])).split(",")
                    layers=[]
                    for name in layer_names:
                        ll=project.mapLayersByName(name)[0]
                        if ll:
                            layers.append(ll)            
                    if not layers or len(layers)==0:
                        self.send_response(404)
                        self.end_headers()
                        self.wfile.write("Nem találhatók a megadott rétegek".encode("utf-8"))
                        return
                
                    # Gyűjtsük a NamedLayer XML-eket
                    named_layers_xml = ""
                    for layer in layers:
                        sld_part = get_sld_from_layer(layer)
                        # SLD rész kivonása (a <NamedLayer>...</NamedLayer> rész)
                        try:
                            import xml.etree.ElementTree as ET
                            tree = ET.fromstring(sld_part)
                            for nl in tree.findall("{http://www.opengis.net/sld}NamedLayer"):
                                named_layers_xml += ET.tostring(nl, encoding="unicode")
                        except Exception as e:
                            print(f"Hiba SLD feldolgozásánál: {e}")
                
                    # Komplett válasz SLD létrehozása
                    sld_full = f"""<?xml version="1.0"?>
                <StyledLayerDescriptor version="1.1.0"
                    xsi:schemaLocation="http://www.opengis.net/sld StyledLayerDescriptor.xsd"
                    xmlns="http://www.opengis.net/sld"
                    xmlns:ogc="http://www.opengis.net/ogc"
                    xmlns:xlink="http://www.w3.org/1999/xlink"
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
                    {named_layers_xml}
                </StyledLayerDescriptor>"""
                
                    self.send_response(200)
                    self.send_header("Content-type", "application/vnd.ogc.sld+xml")
                    self.end_headers()
                    self.wfile.write(sld_full)    
                    # self.wfile.write(sld_full.encode("utf-8"))    
                if request_param is not None and request_param.lower() == "getcapabilities":
                    self.send_response(200)
                    self.send_header("Content-type", "text/xml")
                    self.end_headers()
                    xml=generate_wms_111_getcapabilities(list(maplayers.values())[0].name() , list(maplayers.values())[0].name(), '')
                    self.wfile.write(xml)                
        except Exception as e:
            print(f"General error on http: {e}")
        return

# Kiszolgáló indítása
def start_server():
    global port
    c=0
    while c<20:
        port=port+c
        try:
            with MyTCPServer(("", port), SimpleHTTPRequestHandler) as httpd:
                print(f"Serving on port {port}")
                while True:
                    httpd.handle_request()
                # httpd.serve_forever()
        except:
            c+=1

def save_symbol_image(symbol, output_path,layername="",rulename=""):
    """Generál egy képet egy adott szimbólum alapján, vagy 'Üres' feliratot, ha a szimbólum üres."""
    # Ellenőrizzük, hogy van-e szimbólum
    if symbol is None or symbol.symbolLayerCount() == 0:
        # Üres szimbólum esetén
        image_size = QSize(64, 64)
        image = QImage(image_size, QImage.Format_ARGB32)
        image.fill(QColor(255, 255, 255, 255))  # Fehér háttér

        # Felirat rajzolása
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(QColor(0, 0, 0))  # Fekete szín
        font = QFont("Arial", 10, QFont.Bold)
        painter.setFont(font)
        painter.drawText(image.rect(), Qt.AlignCenter, "Üres")  # Középre igazított felirat
        painter.end()

        # Kép mentése
        if image.save(output_path):
            vprint(f"Üres szimbólum mentve: {output_path}")
        else:
            print("Hiba történt az üres szimbólum mentésekor.")
        return
    else:        
        """Generál egy képet egy adott szimbólum alapján."""
        if not isinstance(symbol, QgsSymbol):
            print("Érvénytelen szimbólum típus.")
            return
    
        # Kép méretének beállítása (pl. 64x64 pixel)
        image_size = QSize(64, 64)
        image = QImage(image_size, QImage.Format_ARGB32)
        image.fill(0)  # Átlátszó háttér
        image.fill(QColor(255, 255, 255, 0))
        # Szimbólum rajzolása
        painter = QPainter(image)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(0, 0, image_size.width(), image_size.height(), QColor("white"))
    
        symbol.drawPreviewIcon(painter, image_size)
        painter.end()
    
        # Kép mentése
        if image.save(output_path):
            vprint(f"Szimbólum mentve: {output_path}")
            fleir=open(output_path.lower().replace('.png','.ldesc'),'wt')
            print(layername,file=fleir)
            if rulename:
                print(rulename,file=fleir)
            fleir.close()
        else:
            print("Hiba történt a kép mentésekor.")  

def save_symbol_images_for_layer(layer, output_dir):
    if not layer:
        print("Érvénytelen réteg.")
        return
    lname=layer.name()[:20].replace(' ','').replace('.','')
    # Ellenőrizni kell a renderelő típusát
    renderer = layer.renderer()
    if isinstance(renderer, QgsRuleBasedRenderer):
        vprint("Feldolgozás: Szabályalapú renderelés")
        rules = renderer.rootRule().children()
        for i, rule in enumerate(rules):
            symbol = rule.symbol()
            if symbol:
                save_symbol_image(symbol, os.path.join(output_dir, f"rule{lname}_{i}.png"),layer.name(),rule.label())

    elif isinstance(renderer, QgsCategorizedSymbolRenderer):
        vprint("Feldolgozás: Kategorizált renderelés")
        for i, category in enumerate(renderer.categories()):
            if isinstance(category, QgsRendererCategory):
                symbol = category.symbol()
                if symbol:
                    save_symbol_image(symbol, os.path.join(output_dir, f"category{lname}_{i}.png"),layer.name())

    elif isinstance(renderer, QgsGraduatedSymbolRenderer):
        vprint("Feldolgozás: Osztályozott renderelés")
        for i, range_ in enumerate(renderer.ranges()):
            if isinstance(range_, QgsRendererRange):
                symbol = range_.symbol()
                if symbol:
                    save_symbol_image(symbol, os.path.join(output_dir, f"range{lname}_{i}.png"),layer.name())
    elif isinstance(renderer, QgsSingleSymbolRenderer):
        # Egyszerű szimbólum
        symbol = renderer.symbol()
        save_symbol_image(symbol, os.path.join(output_dir, f"single_"+lname+".png"))
        vprint("Mentve: egyszerű szimbólum.")
    else:
        
        vprint("Ismeretlen vagy nem támogatott renderelő típus.")    

def retegszimbelment(layers):
    for layer in layers.values():
        save_symbol_images_for_layer(layer,r'd:\OSGeo4W\qgis_web_app\images'+'\\')

    
starttime=time.time()   
image_path = "current_map.jpg"
port = 5000       
QgsApplication.setPrefixPath(r'd:\OSGeo4W\apps\qgis\bin'+'\\', True)
qgs = QgsApplication([], True)
# Load providers
memory_usage = process.memory_info().rss
print(f"Memory using only QGIS: {memory_usage / 1024 ** 2:.2f} MB")

qgs.initQgis()            
project = QgsProject.instance()

# project.read("offline_szotarnelkuili_qgis_Server_teszt_projekt_ingrid_pordp2_teszt.qgz")
prfilename='osgeo.qgz'
if len(sys.argv)>1:
    prfilename=sys.argv[1]
project.read(prfilename)
print('Project loading time:',time.time()-starttime)

# project.read("tesztvez.qgz")
maplayers = project.mapLayers()
vprint('A QGZ layers:',maplayers)
print('Calculating extent:')
total_extent = None
layer_list = list(maplayers.values())    
for layer in layer_list:
    if layer.type() == QgsMapLayer.VectorLayer:
        extent = layer.extent()
        if total_extent is None:
            total_extent = QgsRectangle(extent)
        else:
            total_extent.combineExtentWith(extent)
total_extent=total_extent.toString().replace(':',',')
print('QGZ full extent:',total_extent)   
         
if len(sys.argv)>2 and sys.argv[2]=='--savesymb':
    print('Saving symbols')
    retegszimbelment(maplayers)

memory_usage = process.memory_info().rss
print(f"Memory user with project: {memory_usage / 1024 ** 2:.2f} MB")
print()

      
start_server()        
# server_thread = threading.Thread(target=start_server)
# server_thread.daemon = True  # A szál leállítása, ha a fő program befejeződik
# server_thread.start()
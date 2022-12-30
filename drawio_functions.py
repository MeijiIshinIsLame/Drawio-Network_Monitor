import base64
import xml.etree.ElementTree as ET
import zlib
from urllib.parse import quote, unquote
import re

#don't entirely understand, but got this from stack overflow
class DrawioDecoder:
    def __init__(self, filename):
        self.data = None
        self.decoded_data = None
        self.filename = filename
        self.load_drawio_diagram()

    def js_encode_uri_component(self, data):
        return quote(data, safe='~()*!.\'')
    
    def js_decode_uri_component(self, data):
        return unquote(data)
    
    def js_string_to_byte(self, data):
        return bytes(data, 'iso-8859-1')
    
    def js_bytes_to_string(self, data):
        return data.decode('iso-8859-1')
    
    def js_btoa(self, data):
        return base64.b64encode(data)
    
    def js_atob(self, data):
        return base64.b64decode(data)
    
    def pako_inflate_raw(self, data):
        decompress = zlib.decompressobj(-15)
        decompressed_data = decompress.decompress(data)
        decompressed_data += decompress.flush()
        return decompressed_data
    

    def load_drawio_diagram(self):
        # Open the file in binary mode
        with open(self.filename, 'r') as file:
            # Read the contents of the file
            self.data = file.read()

        m = re.search("<diagram.*>([^<]+)</diagram>", self.data)
        if m:
            b64 = m.groups()[0]
        a = base64.b64decode(b64)
        b = self.pako_inflate_raw(a)
        c = self.js_decode_uri_component(b.decode())
        self.decoded_data = c
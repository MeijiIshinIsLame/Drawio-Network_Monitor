import base64
import xml.etree.ElementTree as ET
import zlib
from urllib.parse import quote, unquote

class DrawioDecoder:
    def __init__(self, data):
        self.data = data

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
    
    def decode(self):
        uri_decoded_data = self.js_decode_uri_component(self.data)
        byte_data = self.js_string_to_byte(uri_decoded_data)
        inflated_data = self.pako_inflate_raw(byte_data)
        xml_string = self.js_bytes_to_string(inflated_data)
        xml_root = ET.fromstring(xml_string)
        return xml_root
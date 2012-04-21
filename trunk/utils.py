from xml.dom import minidom
from xml import sax
import os.path

def find_element(doc, parent_element, tag_name, attrs=None):
    child_element = None
    for node in parent_element.childNodes:
        if node.nodeType != minidom.Node.ELEMENT_NODE:
            continue
        element = node
        if element.tagName == tag_name:
            conform = True
            if attrs:
                for (key, value) in attrs.iteritems():
                    if element.getAttribute(key) != value:
                        conform = False
                        break
            if conform:
                child_element = element
                break
    return child_element

def find_or_create_element(doc, parent_element, tag_name, attrs=None):
    child_element = find_element(doc, parent_element, tag_name, attrs)
    created = False
    if child_element is None:
        created = True
        child_element = doc.createElement(tag_name)
        if attrs:
            for (key, value) in attrs.iteritems():
                child_element.setAttribute(key, value)
        parent_element.appendChild(child_element)
    return child_element, created

def set_text(doc, element, text):
    if len(element.childNodes) == 1 and \
            element.childNodes[0].nodeType == minidom.Node.TEXT_NODE and \
            element.childNodes[0].data.strip() == text.strip():
        return False
    for node in element.childNodes:
        element.removeChild(node)
    element.appendChild(doc.createTextNode(text))
    return True

class BaseContentHandler(sax.handler.ContentHandler):
    def startDocument(self):
        self.elements = []
            
    def endDocument(self):
        pass
        
    def startElement(self, name, attrs):
        self.elements.append(name)
        for handler in self.handlers:
            if handler[0] == self.elements:
                handler[1](attrs)

    def endElement(self, name):
        for handler in self.handlers:
            if handler[0] == self.elements:
                if len(handler) > 3:
                    if not handler[3] is None:
                        handler[3]()
        self.elements.pop()
            
    def characters(self, data):
        for handler in self.handlers:
            if handler[0] == self.elements:
                if len(handler) > 2:
                    if not handler[2] is None:
                        handler[2](data)

def path_components(path):
    components = []
    while path:
        (path, tail) = os.path.split(path)
        components.insert(0, tail)
    return components

def extract_lang_code(file_name):
    lang_code = None
    file_name_parts = file_name.split('.')
    if len(file_name_parts) > 2:
        lang_code = file_name_parts[-2]
        file_name_without_lang_code = file_name_parts[0]
        for file_name_part in file_name_parts[1:-2]:
            file_name_without_lang_code += '.' + file_name_part
        file_name_without_lang_code += '.' + file_name_parts[-1]
    else:
        file_name_without_lang_code = file_name
    return (lang_code, file_name_without_lang_code)

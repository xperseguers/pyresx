from xml.dom import minidom
from xml import sax

def find_or_create_element(doc, parent_element, tag_name, attrs=None):
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
    if child_element is None:
        child_element = doc.createElement(tag_name)
        if attrs:
            for (key, value) in attrs.iteritems():
                child_element.setAttribute(key, value)
        parent_element.appendChild(child_element)
    
    return child_element

def set_text(doc, element, text):
    for node in element.childNodes:
        element.removeChild(node)
    element.appendChild(doc.createTextNode(text))

class BaseContentHandler(sax.handler.ContentHandler):
    def startDocument(self):
        self.elements = []
        self.current_text_handler = None
        self.current_end_handler = None
            
    def endDocument(self):
        pass
        
    def startElement(self, name, attrs):
        self.elements.append(name)
        for handler in self.handlers:
            if handler[0] == self.elements:
                handler[1](attrs)
                if len(handler) > 2:
                    self.current_text_handler = handler[2]
                if len(handler) > 3:
                    self.current_end_handler = handler[3]

    def endElement(self, name):
        if not self.current_end_handler is None:
            self.current_end_handler()
        self.elements.pop()
        self.current_text_handler = None
        self.current_end_handler = None
            
    def characters(self, data):
        if not self.current_text_handler is None:
            self.current_text_handler(data)

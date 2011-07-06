from xml.dom import minidom

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

import os
from xml.parsers import expat 
from xml import sax
from xml.dom import minidom
from domext import PrettyPrint
from optparse import OptionParser

from utils import find_or_create_element, set_text

class ResxConverter:
    class ContentHandler(sax.handler.ContentHandler):
        def __init__(self):
            self.handlers = [
                ([u'root', u'data'], self.rootDataHandler, 
                 None, self.rootDataEndHandler),
                ([u'root', u'data', u'value'], self.rootDataValueHandler, 
                 self.rootDataValueTextHandler),
                ([u'root', u'data', u'comment'], self.rootDataCommentHandler, 
                 self.rootDataCommentTextHandler)
                ]
            self.text_data = []
            
        def startDocument(self):
            self.elements = []
            self.current_text_handler = None
            self.current_end_handler = None
            
        def endDocument(self):
            pass
        
        def startElement(self, name, attrs):
            self.elements.append(name)
            # print self.elements
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
            #if self.elements == [u'root', u'data', u'value']:
            #    print data
            
        def rootDataHandler(self, attrs):
            mimetype = None
            if attrs.has_key('mimetype'):
                mimetype = attrs['mimetype']
            self.current_text = None
            if mimetype in [None, 'text/plain']:
                self.current_text = {}
                
            name = None
            if attrs.has_key('name'):
                name = attrs['name']
            if type(self.current_text) is dict:
                self.current_text['name'] = name
            
        def rootDataEndHandler(self):
            if self.current_text:
                self.text_data.append(self.current_text)

        def rootDataValueHandler(self, args):
            pass
        
        def rootDataValueTextHandler(self, data):
            if type(self.current_text) is dict:
                self.current_text['value'] = data

        def rootDataCommentHandler(self, args):
            pass
        
        def rootDataCommentTextHandler(self, data):
            if type(self.current_text) is dict:
                self.current_text['comment'] = data

    def __init__(self, dir, target_dir, default_lang_code):
        self.dir = dir
        self.target_dir = target_dir
        self.default_lang_code = default_lang_code
        self.parser = sax.make_parser()
        self.translations = {}

    def parse_resx(self, path):
        relative_path = os.path.relpath(path, self.dir)
        print relative_path
        (relative_dir, file_name) = os.path.split(relative_path)
        lang_code = None
        file_name_parts = file_name.split('.')
        if len(file_name_parts) > 2:
            lang_code = file_name_parts[-2]
            file_name_without_lang_code = file_name_parts[0]
            for file_name_part in file_name_parts[1:-3]:
                file_name_without_lang_code += '.' + file_name_part
            file_name_without_lang_code += '.' + file_name_parts[-1]
        else:
            file_name_without_lang_code = file_name
        print lang_code
        if not lang_code in self.translations:
            self.translations[lang_code] = {}
        
        # Parse source file
        h = ResxConverter.ContentHandler()
        self.parser.setContentHandler(h)
        self.parser.parse(path)
        
        self.translations[lang_code]\
            [relative_dir + '/' 
             + file_name_without_lang_code] = {'source_file': relative_path, 
                                               'data': h.text_data}

    def visit_dir(self, arg, current_dir, dir_content):
        for dir_item in dir_content:
            if os.path.isfile(current_dir + '/' + dir_item) \
                    and dir_item.lower().endswith('.resx'):
                self.parse_resx(current_dir + '/' + dir_item)

    def scan_dir(self):
        os.path.walk(self.dir, self.visit_dir, [])

    def update_translation(self, lang_code, file, source_file, data):
        print file
        print lang_code
        if lang_code is None:
            target_lang_dir = self.target_dir + '/' + self.default_lang_code
        else:
            target_lang_dir = self.target_dir + '/' + lang_code
        
        (relative_dir, file_name) = os.path.split(file)
        
        #Make target directory
        try:
            os.makedirs(target_lang_dir + '/' + relative_dir)
        except OSError:
            pass

        target_file_name = target_lang_dir + '/' + file + '.xlf'
        
        new_doc = False
        try:
            doc = minidom.parse(target_file_name)
        except (IOError, expat.ExpatError):
            impl = minidom.getDOMImplementation()
            doc = impl.createDocument(None, 'xliff', None)
            new_doc = True

        xliff = doc.documentElement
        if xliff.tagName != 'xliff':
            raise Exception('Invalid root element')

        file_element = find_or_create_element(doc, xliff, 
                                              'file', {'original': source_file})

        body_element = find_or_create_element(doc, file_element, 'body')

        for item in data:
            tu_element = find_or_create_element(doc, body_element, 
                                                'trans-unit', {'id': item['name']})
            source_text = self.translations[None][file]['data']
            source_element = find_or_create_element(doc, tu_element, 'source')
            set_text(doc, source_element, 
                     self.find_source_text(file, item['name']))
            target_element = find_or_create_element(doc, tu_element, 'target')
            target_text = u''
            if 'value' in item:
                target_text = item['value']
            set_text(doc, target_element, target_text)

        with open(target_file_name, 'w') as f:
            if new_doc:
                PrettyPrint(doc, f)
            else:
                f.write('<?xml version="1.0" encoding="%s"?>\n' % doc.encoding)
                f.write(xliff.toxml('utf-8'))
                f.write('\n')
        
    def update_translations(self):
        for lang_code in self.translations:
            for file in self.translations[lang_code]:
                source_file = self.translations[lang_code][file]['source_file']
                data = self.translations[lang_code][file]['data']
                self.update_translation(lang_code, file, source_file, data)

    def find_source_text(self, file, id):
        data = self.translations[None][file]['data']
        for item in data:
            if item['name'] == id:
                if 'value' in item:
                    return item['value']
                else:
                    return u''
        return u''
                
        
    def run(self):
        self.scan_dir()
        self.update_translations()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-s', '--source', 
                      help='root directory with source files (.resx)',
                      default='.',
                      metavar='SOURCE')
    parser.add_option('-t', '--target',
                      help='root directory for generated files (.xlf)', 
                      default='.',
                      metavar='TARGET')
    (options, args) = parser.parse_args()
    
    default_lang_code = 'en'
    converter = ResxConverter(options.source, 
                              options.target, default_lang_code)
    converter.run()

import os, io
from xml.parsers import expat 
from xml import sax
from xml.dom import minidom
from domext import PrettyPrint, Print
from optparse import OptionParser

from utils import find_or_create_element, set_text, BaseContentHandler, \
    path_components, extract_lang_code

class XLIFFConverter:
    class ContentHandler(BaseContentHandler):
        def __init__(self):
            self.handlers = [
                ([u'xliff', u'file'], 
                 self.xliffFileHandler, 
                 None, 
                 self.xliffFileEndHandler),
                ([u'xliff', u'file', u'body', u'trans-unit'], 
                 self.xliffFileBodyTUHandler, 
                 None,
                 self.xliffFileBodyTUEndHandler),
                ([u'xliff', u'file', u'body', u'trans-unit', u'source'], 
                 self.xliffFileBodyTUSourceHandler, 
                 self.xliffFileBodyTUSourceTextHandler),
                ([u'xliff', u'file', u'body', u'trans-unit', u'target'], 
                 self.xliffFileBodyTUTargetHandler, 
                 self.xliffFileBodyTUTargetTextHandler)
                ]
            self.files = {}
            
        def xliffFileHandler(self, attrs):
            self.current_file = None
            if attrs.has_key('original'):
                self.current_file = attrs['original']

            self.files[self.current_file] = []
            
        def xliffFileEndHandler(self):
            pass

        def xliffFileBodyTUHandler(self, args):
            self.current_tu = {'id': args['id']}
        
        def xliffFileBodyTUEndHandler(self):
            self.files[self.current_file].append(self.current_tu)
            self.current_tu = None 
        
        def xliffFileBodyTUSourceHandler(self, args):
            pass
        
        def xliffFileBodyTUSourceTextHandler(self, data):
            if type(self.current_tu) is dict:
                self.current_tu['source'] = data

        def xliffFileBodyTUTargetHandler(self, args):
            pass
        
        def xliffFileBodyTUTargetTextHandler(self, data):
            if type(self.current_tu) is dict:
                self.current_tu['target'] = data

    def __init__(self, dir, target_dir, default_lang_code):
        self.dir = dir
        self.target_dir = os.path.normpath(target_dir)
        self.default_lang_code = default_lang_code
        self.parser = sax.make_parser()
        self.translations = {}

    def parse_xliff(self, path):
        relative_path = os.path.relpath(path, self.dir)
        
        # Parse source file
        h = XLIFFConverter.ContentHandler()
        self.parser.setContentHandler(h)
        self.parser.parse(path)
        self.translations[relative_path] = h.files

    def visit_dir(self, arg, current_dir, dir_content):
        for dir_item in dir_content:
            if os.path.isfile(current_dir + '/' + dir_item) \
                    and dir_item.lower().endswith('.xlf'):
                self.parse_xliff(current_dir + '/' + dir_item)

    def scan_dir(self):
        os.path.walk(self.dir, self.visit_dir, [])

    def update_translation(self, lang_code, data):
        print lang_code
        for (source_file, items) in data.iteritems():
            # Skip file if no items
            if len(items) == 0:
                continue

            print source_file
            (source_dir, source_fn) = os.path.split(source_file)
            (source_file_lang_code, 
             source_fn_wo_lang_code) = extract_lang_code(source_fn)
            
            target_file_name = self.target_dir + '/' + source_file
            if source_file_lang_code != lang_code:
                if source_file_lang_code is None:
                    if lang_code and lang_code != self.default_lang_code:
                        (fn, ext) = source_fn.rsplit('.')
                        target_file_name = self.target_dir + '/' + source_dir \
                            + '/' + fn + '.' + lang_code + '.' + ext
                    
            new_doc = False
            try:
                doc = minidom.parse(target_file_name)
            except (IOError, expat.ExpatError):
                impl = minidom.getDOMImplementation()
                doc = impl.createDocument(None, 'root', None)
                new_doc = True

            root_element = doc.documentElement
            if root_element.tagName != 'root':
                raise Exception('Invalid root element')

            no_changes = True

            for item in items:
                if not 'target' in item:
                    continue
                target_text = item['target']
                if not target_text:
                    continue
                if target_text == item['source']:
                    continue
                data_element = find_or_create_element(doc, root_element, 'data',
                                                      {'name': item['id']})
                value_element = find_or_create_element(doc, data_element, 'value')
                res = set_text(doc, value_element, target_text)
                if res:
                    no_changes = False

            if no_changes:
                continue

            # Make target directory
            try:
                os.makedirs(self.target_dir + '/' + source_dir)
            except OSError:
                pass

            # Create of overwrite xml file
            with io.open(target_file_name, 'w', newline='\r\n') as f:
                if new_doc:
                    PrettyPrint(doc, f)
                else:
                    f.write(u'\ufeff')
                    f.write(u'<?xml version="1.0" encoding="%s"?>\n' % doc.encoding)
                    Print(root_element, f)

    def update_translations(self):
        for (file_name, file_content) in self.translations.iteritems():
            pcs = path_components(file_name)
            lang_code = None
            if len(pcs) > 1:
                lang_code = pcs[0]
            self.update_translation(lang_code, file_content)
                
    def run(self):
        self.scan_dir()
        self.update_translations()

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-s', '--source', 
                      help='root directory for generated files (.xlf)', 
                      default='.',
                      metavar='SOURCE')
    parser.add_option('-t', '--target',
                      help='root directory with source files (.resx)',
                      default='.',
                      metavar='TARGET')
    (options, args) = parser.parse_args()
    
    default_lang_code = 'en'
    converter = XLIFFConverter(options.source, 
                               options.target, default_lang_code)
    converter.run()

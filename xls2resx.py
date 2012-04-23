import os
from optparse import OptionParser
import xlrd
from xml.dom import minidom
from xml.parsers import expat 

from utils import find_element, find_or_create_element, set_text

class ExcelConverter(object):
    def __init__(self, source, target, lang_codes):
        self.source = source
        self.target = target
        self.lang_codes = lang_codes

    def run(self):
        wb = xlrd.open_workbook(self.source)
        sheet = wb.sheet_by_index(0)
        row_index = -1
        source_filename = None
        trans_items = []
        for cell in sheet.col(0):
            row_index += 1
            if cell.value:
                if source_filename:
                    self.update_translations(source_filename, trans_items)
                source_filename = cell.value
                trans_items = []
                continue
            row = sheet.row(row_index)
            translations = {}
            for i, lang_code in enumerate(self.lang_codes):
                translations[lang_code] = row[3 + i].value
            trans_items.append({
                    'id': row[1].value,
                    'source': row[2].value,
                    'translations': translations})
        self.update_translations(source_filename, trans_items)

    def update_translations(self, source_filename, trans_items):
        print source_filename
        self.update_source_file(source_filename, trans_items)
        (d, f) = os.path.split(source_filename)
        (n, e) = os.path.splitext(f)
        for lang_code in self.lang_codes:
            filename = os.path.join(d, n + '.' + lang_code + e)
            self.update_translation_file(filename, trans_items, lang_code)

    def update_source_file(self, source_filename, trans_items):
        fullpath = os.path.join(self.target, source_filename)
        try:
            doc = minidom.parse(fullpath)
        except (IOError, expat.ExpatError):
            raise

        root = doc.documentElement
        for trans_item in trans_items:
            data = find_element(doc, root, 'data', {'name': trans_item['id']})
            if data:
                comment, created = find_or_create_element(doc, data, 'comment')
                for n in comment.childNodes:
                    comment.removeChild(n)
                comment.appendChild(doc.createTextNode('t'))

        with open(fullpath, 'w') as f:
            f.write(doc.toxml().encode('utf-8'))

    def update_translation_file(self, filename, trans_items, lang_code):
        fullpath = os.path.join(self.target, filename)
        try:
            doc = minidom.parse(fullpath)
        except (IOError, expat.ExpatError):
            # FIXME: New file needs to be created
            '''
            impl = minidom.getDOMImplementation()
            doc = impl.createDocument(None, 'root', None)
            '''
            return

        root = doc.documentElement
        for trans_item in trans_items:
            translation = trans_item['translations'][lang_code]
            if not translation:
                data = find_element(doc, root, 'data',
                                    {'name': trans_item['id']})
                if data:
                    root.removeChild(data)
                continue
            data, created = find_or_create_element(doc, root, 'data',
                                                   {'name': trans_item['id']})
            if created:
                data.setAttribute('xml:space', 'preserve')
            value, created = find_or_create_element(doc, data, 'value')
            if not created:
                for n in value.childNodes:
                    value.removeChild(n)
            value.appendChild(doc.createTextNode(translation))

        with open(fullpath, 'w') as f:
            f.write(doc.toxml().encode('utf-8'))

if __name__ == '__main__':
    parser = OptionParser()
    parser.add_option('-s', '--source', 
                      help='Excel file contating translations (.xls)', 
                      metavar='SOURCE')
    parser.add_option('-t', '--target',
                      help='root directory with source files (.resx)',
                      default='.',
                      metavar='TARGET')
    (options, args) = parser.parse_args()

    converter = ExcelConverter(options.source, options.target, args)
    converter.run()

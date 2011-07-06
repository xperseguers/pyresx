import os
from xml.parsers import expat 
from xml import sax
from xml.dom import minidom
from domext import PrettyPrint
from optparse import OptionParser

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

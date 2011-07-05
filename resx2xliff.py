import os
from xml import sax

class ResxConverter:
	class ContentHandler(sax.handler.ContentHandler):
		def __init__(self):
			self.handlers = [
				([u'root', u'data'], self.rootDataHandler, None, self.rootDataEndHandler),
				([u'root', u'data', u'value'], self.rootDataValueHandler, self.rootDataValueTextHandler),
				([u'root', u'data', u'comment'], self.rootDataCommentHandler, self.rootDataCommentTextHandler)
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
			#	print data
			
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

	def __init__(self, dir):
		self.dir = dir
		self.parser = sax.make_parser()

	def parse_resx(self, file_name):
		print file_name
		h = ResxConverter.ContentHandler()
		self.parser.setContentHandler(h)
		self.parser.parse(file_name)
		print h.text_data

	def visit(self, arg, current_dir, dir_content):
		for dir_item in dir_content:
			if os.path.isfile(current_dir + '/' + dir_item) and dir_item.lower().endswith('.resx'):
				self.parse_resx(current_dir + '/' + dir_item)

	def scan_dir(self):
		os.path.walk(self.dir, self.visit, [])

dir = 'c:/Users/fifedtyu/Documents/Projects/YIT/stage-2.0/YITMIS/GUI.Materials/Properties'
converter = ResxConverter(dir)
converter.scan_dir()

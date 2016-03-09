Utilities:
  * resx2xliff.py - converts .resx files (textual data) to XLIFF format. It scans source directory (--source option) and updates .xlf file(s) in the target directory (--target option) or creates new file(s) if it doesn't exist.
  * xls2resx.py - converts Microsoft Excel sheet containing translations into .resx files.
> > python xls2resx.py -s source-workbook.xls -t target/directory language codes
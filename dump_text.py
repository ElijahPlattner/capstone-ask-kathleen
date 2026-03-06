from pypdf import PdfReader
path='documents/2026 US Statutory Holiday Policy - Human Resources.pdf'
reader=PdfReader(path)
print('num pages',len(reader.pages))
for i,page in enumerate(reader.pages[:5]):
    print('page',i,repr(page.extract_text()[:500]))

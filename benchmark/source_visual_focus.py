"""Focus encrypted review on source-located target tables, never parser-derived gold."""
import re
import fitz
from benchmark import source_visual_export as export
from benchmark import table_shadow

Original=table_shadow.StorageSource
class FocusSource(Original):
    def get_pdf(self,spec):
        result=super().get_pdf(spec)
        hint=export.PAGES[spec['id']][1]
        choices=[]
        with fitz.open(stream=result[0],filetype='pdf') as doc:
            for i,page in enumerate(doc,1):
                hits=page.search_for(hint)
                captions=[x for x in export.source_lines(page) if re.match(r'^\s*Table\s+(?:\d+|[A-Z]\d+)[.:]',x['text'])]
                if hits and any(c['bbox'][1]<hits[0].y0 for c in captions):choices.append(i)
        if not choices:raise ValueError('No source-located table target')
        export.PAGES[spec['id']]=(choices[0],hint)
        return result

original_emit=export.emit
def emit(label,data):
    words=data.pop('words',None)
    original_emit(label,data)
    if words is not None:
        original_emit(label+'-words',{'id':data['id'],'page':data['page'],'source_sha256':data['source_sha256'],'words':[[round(x,2) for x in w[:4]]+[w[4]] for w in words]})

if __name__=='__main__':
    export.emit=emit
    table_shadow.StorageSource=FocusSource
    raise SystemExit(export.main())

"""Package only explicitly listed source and owned demonstration artifacts."""
import zipfile
from pathlib import Path
root=Path(__file__).resolve().parents[1]
output=root/'web'/'public'/'downloads';output.mkdir(exist_ok=True)
files=[]
for directory in ('engine','service','scripts','tests','docs','web/app','web/lib','web/components','web/hooks','web/public/demo'):
    files.extend(p for p in (root/directory).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for pattern in ('*.md','*.txt','*.ps1','LICENSE','.gitignore','web/*.json','web/*.ts','web/public/*.svg','web/.gitignore','web/.oxlintrc.json','web/.oxfmtrc.json'):
    files.extend(root.glob(pattern))
with zipfile.ZipFile(output/'editdna-source.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(files)):
        z.write(p,Path('EditDNA')/p.relative_to(root))
    z.writestr('EditDNA/web/.openai/hosting.json','{"d1":null,"r2":null}\n')
print('Packaged source bundle:',len(set(files)),'files')

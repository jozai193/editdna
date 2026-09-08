import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
# Honor the Windows trust store when a corporate proxy is installed.
try:
    import pip._vendor.truststore as truststore
    truststore.inject_into_ssl()
except ImportError:pass
from service import store
from service.main import execute
recipes=json.loads((store.ROOT/'demo'/'ground-truth.json').read_text())
for r in recipes:
    print('Transcribing',r['title'],flush=True)
    execute({'task':'transcribe','payload':{'asset_id':r['raw_id']}})
    for ref in r['references'].values():
        if ref.get('asset_id'):execute({'task':'transcribe','payload':{'asset_id':ref['asset_id']}})
print('Transcripts complete',flush=True)

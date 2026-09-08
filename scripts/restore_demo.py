"""Restore the shipped demonstration into an empty local workspace."""
import json
import shutil
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from service import store

def main():
    if store.all('asset'):
        print('Existing workspace retained.');return
    source=Path(__file__).resolve().parents[1]/'web'/'public'/'demo'
    state=json.loads((source/'state.json').read_text())
    kinds={'assets':'asset','profiles':'profile','pairs':'pair','versions':'version','plans':'plan','exports':'export'}
    for name,kind in kinds.items():
        for item in state[name]:store.save(kind,item)
    for a in state['assets']:shutil.copyfile(source/'media'/(a['id']+'.mp4'),store.ROOT/'assets'/a['id'])
    for e in state['exports']:shutil.copytree(source/'exports'/e['id'],store.ROOT/'exports'/e['id'],dirs_exist_ok=True)
    shutil.copyfile(source/'evaluation.json',store.ROOT/'demo'/'evaluation.json')
    shutil.copyfile(source/'trial-tasks.json',store.ROOT/'demo'/'trial-tasks.json')
    print('Restored demonstration: 5 sessions, 2 profiles, 6 exports.')

if __name__=='__main__':main()

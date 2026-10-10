"""Read-only, verified Development artifacts; no master data or storage queries."""
import json,hashlib
from fastapi import APIRouter,HTTPException
from fastapi.responses import FileResponse
from engine.legacy import ROOT
P=ROOT/'work/simple-strategy-unrestricted-v1'
router=APIRouter(prefix='/api/research/simple-search',tags=['research'])

def manifest():
    p=P/'reproducibility_manifest.json'
    if not p.exists():raise HTTPException(409,'Verification pending')
    m=json.loads(p.read_text())
    if m.get('status')!='PASS' or m.get('segment')!='development':raise HTTPException(409,'Verified Development study required')
    return m

@router.get('')
def status():
    try:m=manifest()
    except HTTPException:return dict(ready=False)
    return dict(ready=True,events=m['raw_signals'])

@router.get('/files/{name:path}')
def file(name:str):
    m=manifest()
    if name not in m['artifacts']:raise HTTPException(404,'Unknown artifact')
    p=(P/name).resolve()
    if not p.is_relative_to(P.resolve()) or not p.is_file():raise HTTPException(404,'Artifact unavailable')
    with p.open('rb') as f:actual=hashlib.file_digest(f,'sha256').hexdigest()
    if actual!=m['artifacts'][name]['sha256']:raise HTTPException(409,'Artifact changed')
    return FileResponse(p,media_type='text/html' if name.endswith('.html') else None,filename=None if name.endswith('.html') else p.name,headers={'Cache-Control':'no-store','X-Content-Type-Options':'nosniff'})

@router.get('/view')
def view():
    """Readable view over the immutable verified summary; original exports unchanged."""
    from html import escape
    from fastapi.responses import HTMLResponse
    file('summary.json')
    data=json.loads((P/'summary.json').read_text())
    def table(rows,columns):
        result='<div class="scroll"><table><thead><tr>'+''.join('<th>'+escape(label)+'</th>' for key,label in columns)+'</tr></thead><tbody>'
        for row in rows:
            result+='<tr>'
            for key,label in columns:
                value=row.get(key)
                text='Unavailable' if value is None else f'{value:,.3f}' if isinstance(value,float) else f'{value:,}' if isinstance(value,int) else str(value)
                result+='<td>'+escape(text)+'</td>'
            result+='</tr>'
        return result+'</tbody></table></div>'
    columns=[('hypothesis','Policy'),('trades','Completed trades'),('known_trade_net','Known trade net ($)'),('net_usd','Complete net ($)'),('pf','PF*'),('avg_net_r','Average R*'),('max_dd','Complete drawdown ($)'),('unknown_days','Unresolved days')]
    body='<h1>Simple MNQ research — unrestricted</h1><p>Development 2020–2023 · One micro · $0.73 per side · One adverse tick per side · Fixed 2R</p><p class="notice">No policy passed the complete registered screen. These are research results, not validated strategies.</p>'
    body+='<nav>'+ ' · '.join(f'<a download href="/api/research/simple-search/files/{f}">{label}</a>' for f,label in [('summary.csv','Summary CSV'),('trades.csv','All trades CSV'),('summary.json','Complete summary JSON'),('yearly.csv','Yearly CSV'),('REPORT.md','Full report')])+'</nav>'
    body+='<h2>All twelve policies</h2><p>* PF and average R describe completed trades only. Where a day is unresolved, they are partial figures. “Unavailable” does not mean zero.</p>'+table(data['primary'],columns)
    body+='<details><summary>Every Development year</summary>'+table([r for r in data['yearly'] if r['ticks']==1],[('hypothesis','Policy'),('year','Year')]+columns[1:])+'</details>'
    body+='<details><summary>All cost scenarios</summary>'+table(data['scenarios'],[('hypothesis','Policy'),('ticks','Slippage ticks per side')]+columns[1:])+'</details>'
    body+='<details><summary>Registered statistical evidence — 18-policy initial family</summary>'+table(data['evidence'],[('policy','Policy'),('ci_low','Daily mean 95% CI lower'),('ci_high','Upper'),('p_value','Raw p'),('holm_p_18','Adjusted p'),('evidence_status','Coverage')])+'</details>'
    body+='<p>The separate timing follow-up increases the combined trial ledger to 20 policies. It is documented in the repository’s SIMPLE_TIMING_FOLLOWUP_REPORT.md. Validation and OOS were not queried.</p>'
    return HTMLResponse('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Simple MNQ research</title><style>body{background:#101923;color:#e6edf4;font:15px system-ui;margin:28px}a{color:#85c9ff}h1{font-size:26px}p{max-width:1100px;line-height:1.6}.notice{background:#293747;padding:12px;border-left:3px solid #eab665}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px;min-width:900px}td,th{padding:10px;border:1px solid #384b5c;text-align:right}td:first-child,th:first-child{text-align:left}th{background:#203041}details{margin:24px 0}summary{cursor:pointer;font-size:18px;margin:14px 0}</style>'+body,headers={'Cache-Control':'no-store'})

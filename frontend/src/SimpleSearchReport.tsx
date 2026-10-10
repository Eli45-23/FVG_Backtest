import {useState,useEffect} from 'react';
import {api} from './api';
export default function SimpleSearchReport(){
 const [data,setData]=useState<{ready:boolean;events?:number}|null>(null);const [error,setError]=useState('');
 useEffect(()=>{api('/research/simple-search').then(setData).catch(e=>setError(e.message))},[]);
 return <section className="panel" aria-label="Unrestricted simple strategy search"><h2>Simple MNQ strategies · Unrestricted research</h2><p>Twelve policies · One micro · Repeated entries, one position at a time · Fixed 2R · Development 2020–2023</p><p>No account-size or dollar-risk eligibility cap. Research findings are not validated trading strategies.</p>{error?<p role="alert">{error}</p>:!data?<p>Checking study…</p>:data.ready?<><p>{Number(data.events).toLocaleString()} raw signals. All results, including failed policies, are retained.</p><a href="/api/research/simple-search/view" target="_blank" rel="noreferrer">Open unrestricted strategy research</a></>:<p>Verification pending.</p>}</section>
}

import {useState,useEffect} from 'react';
import {api} from './api';
export default function SimpleDiscoveryReport(){
 const [data,setData]=useState<any>(null);const [error,setError]=useState('');
 useEffect(()=>{api('/research/simple-discovery').then(setData).catch(e=>setError(e.message))},[]);
 return <section className="panel" aria-label="Simple strategy search"><h2>Simple MNQ strategy search · $500 account</h2><p>Three candle-only patterns · One trade daily · $75 planned risk · Development 2020–2023 · Margin scenarios</p>{error?<p role="alert">{error}</p>:!data?<p>Checking study…</p>:data.ready?<><p>{Number(data.events).toLocaleString()} raw signals. Every tested hypothesis is retained.</p><a href="/api/research/simple-discovery/files/study.html" target="_blank" rel="noreferrer">Open simple strategy search results</a></>:<p>Verification pending.</p>}</section>
}

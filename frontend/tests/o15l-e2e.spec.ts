import {test,expect} from '@playwright/test';
import fs from 'node:fs';
test('sequential O15L results, all entries, five audited charts and exports',async({page,context})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/api/**',async route=>{
  if(route.request().url().includes('/api/research/o15l-clear-hold')) await route.continue();
  else await route.fulfill({json:route.request().url().endsWith('/data')?{datasets:[]}:[]});
 });
 await page.goto('/');await page.getByRole('button',{name:'Research',exact:true}).click();
 await expect(page.getByText(/280 causal confirmations/)).toBeVisible();
 const popup=context.waitForEvent('page');await page.getByRole('link',{name:'Open clearance-and-hold results and trades'}).click();
 const result=await popup;result.on('pageerror',e=>errors.push(e.message));
 await expect(result.locator('#costs tbody tr')).toHaveCount(3);
 await expect(result.locator('#years tbody tr')).toHaveCount(4);
 await expect(result.locator('#count')).toContainText('273 matching trades');
 await result.locator('#year').selectOption('2022');
 await expect(result.locator('#count')).toContainText('68 matching trades');
 await result.locator('#trades button').first().click();
 await expect(result.locator('#chart svg')).toBeVisible();
 await result.getByRole('button',{name:'Clear filters',exact:true}).click();
 await expect(result.locator('#count')).toContainText('273 matching trades');
 const audit=fs.readFileSync('../work/o15l-clear-hold-sequential-v1/chart_audit.csv','utf8').trim().split('\n').slice(1);
 expect(audit).toHaveLength(5);
 for(let i=0;i<audit.length;i++){
   const id=audit[i].split(',')[0];
   await result.evaluate(async id=>{await (window as any).chart(id)},id);
   await expect(result.locator('#chart')).toContainText('Frozen clearance barrier');
   await expect(result.locator('#chart')).toContainText('Hold / Entry');
   await result.locator('#chart').screenshot({path:`../work/o15l-chart-${i}.png`});
 }
 for(const name of ['All primary trades CSV','Summary JSON','Report bundle']){
  const promise=result.waitForEvent('download');await result.getByRole('link',{name,exact:true}).click();expect(await(await promise).failure()).toBeNull();
 }
 await result.evaluate(()=>window.scrollTo(0,0));await result.screenshot({path:'../work/o15l-viewer.png'});
 expect(errors).toEqual([]);
});

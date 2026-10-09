import {test,expect} from '@playwright/test';
test('opening range breakout results, trade filters, chart and exports',async({page,context})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/api/**',async route=>{
  if(route.request().url().includes('/api/research/opening15-breakout')) await route.continue();
  else await route.fulfill({json:route.request().url().endsWith('/data')?{datasets:[]}:[]});
 });
 await page.goto('/');await page.getByRole('button',{name:'Research',exact:true}).click();
 await expect(page.getByText(/3,745 causal breakouts/)).toBeVisible();
 const popup=context.waitForEvent('page');await page.getByRole('link',{name:'Open breakout results, times and trades'}).click();
 const result=await popup;result.on('pageerror',e=>errors.push(e.message));
 await expect(result.locator('#costs tbody tr')).toHaveCount(3);
 await expect(result.locator('#years tbody tr')).toHaveCount(4);
 await expect(result.locator('#timing tbody tr')).toHaveCount(6);
 await expect(result.locator('#count')).toContainText('2534 matching trades');
 await result.locator('#side').selectOption('SHORT');
 await expect(result.locator('#timing')).toContainText('Entry time NY');
 await result.locator('#year').selectOption('2022');await result.locator('#tradeSide').selectOption('LONG');
 await expect(result.locator('#count')).not.toContainText('2534 matching trades');
 await result.locator('#trades button').first().click();
 await expect(result.getByRole('img',{name:'Five-minute trade chart with opening range, entry, stop, target and exit'})).toBeVisible();
 await result.getByRole('button',{name:'Clear filters',exact:true}).click();
 await expect(result.locator('#count')).toContainText('2534 matching trades');
 for(const name of ['All primary trades CSV','Summary JSON','Report bundle']){
  const promise=result.waitForEvent('download');await result.getByRole('link',{name,exact:true}).click();expect(await(await promise).failure()).toBeNull();
 }
 const filtered=result.waitForEvent('download');await result.getByRole('button',{name:'Export filtered trades'}).click();expect(await(await filtered).failure()).toBeNull();
 await result.evaluate(()=>window.scrollTo(0,0));await result.screenshot({path:'../work/opening15-viewer.png',fullPage:true});
 expect(errors).toEqual([]);
});

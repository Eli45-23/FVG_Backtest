import {test,expect} from '@playwright/test';
import {readFile} from 'node:fs/promises';
test('verified unrestricted study and complete exports',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/api/research/simple-search/view');
 await expect(page.getByRole('heading',{name:'Simple MNQ research — unrestricted'})).toBeVisible();
 for(const name of ['OPEN_MOMENTUM_15','OPEN_FADE_15','EMA20_CROSS','EMA20_PULLBACK','CHANNEL12_BREAK','CHANNEL12_RECLAIM']){
  await expect(page.locator('table').first().getByText(name,{exact:true})).toBeVisible();
 }
 for(const name of ['Summary CSV','Complete summary JSON']){
  const wait=page.waitForEvent('download');await page.getByRole('link',{name,exact:true}).click();
  const download=await wait;expect(await download.failure()).toBeNull();
  const content=await readFile((await download.path())!, 'utf8');
  if(name==='Complete summary JSON'){const data=JSON.parse(content);expect(data.primary).toHaveLength(12);expect(data.gates).toHaveLength(12)}else expect(content).toContain('hypothesis,ticks');
 }
 expect(errors).toEqual([]);
 await page.screenshot({path:'../work/simple-strategy-unrestricted-v1/browser.png',fullPage:false});
});

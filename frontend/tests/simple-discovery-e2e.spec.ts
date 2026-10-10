import {test,expect} from '@playwright/test';
test('simple study all hypotheses, account selection, chart and exports',async({page,context})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/api/**',async r=>{if(r.request().url().includes('/api/research/simple-discovery'))await r.continue();else await r.fulfill({json:r.request().url().endsWith('/data')?{datasets:[]}:[]})});
 await page.goto('/');await page.getByRole('button',{name:'Research',exact:true}).click();await expect(page.getByText(/18,931 raw signals/)).toBeVisible();
 const pop=context.waitForEvent('page');await page.getByRole('link',{name:'Open simple strategy search results'}).click();const r=await pop;r.on('pageerror',e=>errors.push(e.message));
 await expect(r.locator('#primary tbody tr')).toHaveCount(3);await expect(r.locator('#evidence tbody tr')).toHaveCount(3);await expect(r.locator('#years tbody tr')).toHaveCount(4);
 await r.locator('#hyp').selectOption('TWO_PUSH');await r.locator('#mode').selectOption('ONE_MICRO_200');await expect(r.locator('#count')).toContainText('950 executed trades');
 await r.locator('#trades button').first().click();await expect(r.getByRole('img',{name:'Candle pattern trade chart'})).toBeVisible();
 await r.locator('#mode').selectOption('RISK_SIZED_4763');await expect(r.locator('#count')).toContainText('0 executed trades');await r.locator('#mode').selectOption('RISK_SIZED_200');
 for(const name of ['Summary JSON','Every daily outcome CSV']){const download=r.waitForEvent('download');await r.getByRole('link',{name,exact:true}).click();expect(await(await download).failure()).toBeNull()}
 await r.screenshot({path:'../work/simple-discovery-browser.png',fullPage:false});expect(errors).toEqual([]);
});

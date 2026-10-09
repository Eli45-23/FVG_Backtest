import {test,expect} from '@playwright/test';
test('Validation gate failure is visible with complete trade inspection and exports',async({page,context})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await context.route('**/api/**',async route=>{
   if(route.request().url().includes('/api/research/o15l-validation'))await route.continue();
   else await route.fulfill({json:route.request().url().endsWith('/data')?{datasets:[]}:[]});
 });
 await page.goto('/');await page.getByRole('button',{name:'Research',exact:true}).click();
 await expect(page.getByText(/71 causal confirmations/)).toBeVisible();
 const pop=context.waitForEvent('page');await page.getByRole('link',{name:'Open 2024 Validation results and trades'}).click();
 const result=await pop;result.on('pageerror',e=>errors.push(e.message));
 await expect(result.locator('#gate')).toContainText('VALIDATION_GATE_FAILED');
 await expect(result.locator('#count')).toContainText('69 matching trades');
 await expect(result.locator('#costs tbody tr')).toHaveCount(3);
 await result.locator('#outcome').selectOption('LOSS');await expect(result.locator('#count')).toContainText('41 matching trades');
 await result.getByRole('button',{name:'Clear filters',exact:true}).click();
 await expect(result.locator('#count')).toContainText('69 matching trades');
 await result.locator('#trades button').first().click();await expect(result.locator('#chart svg')).toBeVisible();
 await result.locator('#chart').screenshot({path:'../work/o15l-validation-chart.png'});
 for(const name of ['All primary trades CSV','Summary JSON','Report bundle']){
   const d=result.waitForEvent('download');await result.getByRole('link',{name,exact:true}).click();expect(await(await d).failure()).toBeNull();
 }
 await result.evaluate(()=>window.scrollTo(0,0));await result.screenshot({path:'../work/o15l-validation-viewer.png'});
 expect(errors).toEqual([]);
});

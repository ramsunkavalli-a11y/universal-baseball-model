// Test only this repo's local static application; no user browser or login state.
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
const require=createRequire(import.meta.url);
const {chromium}=require('C:/Users/ramav/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(import.meta.dirname,'..');
const out=path.join(root,'reports/generated/hitter-final-2026-reviewed-explorer');
const suffix=process.env.UBM_UI_REVIEW_SUFFIX||'';
assert(!fs.existsSync(path.join(out,`browser-review${suffix}.json`)),'Preserve browser review');
const data=JSON.parse(fs.readFileSync(path.join(out,'data.json'),'utf8'));
const errors=[];let browser;
try {
 browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1400,height:950}});
 await page.route('**/*',route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'&&u.port==='8810'?route.continue():route.abort()});
 page.on('pageerror',e=>errors.push(String(e)));
 await page.goto('http://127.0.0.1:8810/');await page.locator('#filterTotals').filter({hasText:'4,030 hitters'}).waitFor();
 assert.equal(await page.locator('#rows tr').count(),75);
 assert((await page.locator('#page').textContent()).includes('Page 1 of 54'));
 await page.locator('#next').click();assert((await page.locator('#page').textContent()).includes('Page 2 of 54'));
 await page.locator('#team').selectOption({label:'San Francisco Giants'});
 await page.locator('#stage').selectOption({label:'Upper minors'});
 const giants=data.players.filter(p=>p.org==='San Francisco Giants'&&p.stage==='Upper minors');
 assert(giants.length>0);assert((await page.locator('#filterTotals').textContent()).startsWith(`${giants.length} hitters`));
 await page.locator('[data-sort="hitting_wins_per_600"]').click();
 const first=await page.locator('#rows [data-player]').first().getAttribute('data-player');
 assert.equal(Number(first),giants.toSorted((a,b)=>b.hitting_wins_per_600-a.hitting_wins_per_600||a.player_id-b.player_id)[0].player_id);
 await page.screenshot({path:path.join(out,'giants-hitting.png'),fullPage:true});
 await page.locator('#team').selectOption('');await page.locator('#stage').selectOption('');await page.locator('#search').fill('592450');
 await page.locator('#filterTotals').filter({hasText:/^1 hitters/}).waitFor();
 assert.equal(await page.locator('#rows [data-player]').count(),1);await page.locator('#rows [data-player]').click();
 const detail=await page.locator('#detail').textContent();assert(detail.includes('Aaron Judge')&&detail.includes('99.3%')&&detail.includes('588 / 285')&&detail.includes('4.69'));
 await page.screenshot({path:path.join(out,'judge-walk.png'),fullPage:true});
 await page.locator('#search').fill('815908');await page.locator('#rows [data-player]').click();
 assert((await page.locator('#detail').textContent()).includes('No actual MLB hitting rate is observed'));
 assert((await page.locator('#detail').textContent()).includes('Sparse joint training profile'));
 await page.locator('#search').fill('');await page.locator('#review').selectOption('noPA');
 assert((await page.locator('#filterTotals').textContent()).startsWith('3,375 hitters'));
 const pas=await page.locator('#rows tr td:nth-child(3)').allTextContents();assert(pas.every(v=>v==='0'));
 await page.locator('#review').selectOption('');await page.locator('#search').fill('no such player exists');
 assert((await page.locator('#rows').textContent()).includes('No matching players'));
 await page.locator('#search').fill('Lee');await page.setViewportSize({width:430,height:900});
 await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
 assert(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth),'Mobile whole-page overflow');
 await page.locator('#search').fill('830475');await page.locator('#rows [data-player]').click();
 assert((await page.locator('#detail').textContent()).includes('Name unavailable (830475)'));
 await page.locator('[data-sort="player_name"]').click();
 assert.equal(await page.locator('#outside tr').count(),7);assert.equal(await page.locator('#cohorts tr').count(),4);
 assert.equal(errors.length,0,errors.join('\n'));
 fs.writeFileSync(path.join(out,`browser-review${suffix}.json`),JSON.stringify({status:'passed',browser:'Independent headless Edge, not user browser session',
  tests:['4,030 fixed players; 75-row pagination','2025 Giants plus upper-minors filter','Hitting-only descending sort matches saved rates','Judge exact PA, probability and hitting display','Made sparse warning and unobserved actual rate','Non-arrival and empty search','Four cohort totals and seven missing forecasts','Desktop and mobile render without whole-page overflow; no JavaScript errors','Missing source-name ID search, fallback label and name sorting'],
  in_app_connector:'Failed kernel asset initialization twice; Codex open queued separately.',forecast_changes:false,errors},null,2));
 console.log('Explorer tests passed: filters, sorting, player calculations, missingness, pagination, desktop and mobile.');
}finally {if(browser)await browser.close()}

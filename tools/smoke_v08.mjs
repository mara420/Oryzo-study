import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
const browser=await chromium.launch({headless:true,args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"]});
await fs.mkdir("test-output",{recursive:true});
try{
const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1,reducedMotion:"reduce"});
const errors=[];
page.on("pageerror",e=>errors.push(e.message));
page.on("console",m=>{if(m.type()==="error")errors.push(m.text())});
const root=path.resolve("node_modules/three"),prefix="https://cdn.jsdelivr.net/npm/three@0.178.0/";
await page.route(prefix+"**",async route=>{
const file=path.resolve(root,new URL(route.request().url()).pathname.split("/three@0.178.0/")[1]);
if(!file.startsWith(root+path.sep))return route.abort();
await route.fulfill({body:await fs.readFile(file),contentType:"application/javascript"});
});
try {
await page.goto("http://127.0.0.1:8765/v08/",{waitUntil:"domcontentloaded",timeout:90000});
await page.waitForFunction(()=>window.study?.version==="0.8"&&study.handReady&&document.querySelector("#status").hidden,{},{timeout:120000});
await page.waitForFunction(()=>study.bakeAvailable,{},{timeout:120000});
await page.locator('button[data-p=".66"]').click({timeout:60000});
await page.waitForFunction(()=>study.handActive&&study.handRoot.visible,{},{timeout:90000});
await page.locator("#release").click({timeout:60000});
await page.waitForFunction(()=>study.gripValue<.05,{},{timeout:60000});
const rest=await page.evaluate(()=>study.handJoints.map(j=>j.bone.quaternion.toArray()));
await page.screenshot({path:"test-output/hand-open.png",timeout:90000});
await page.locator("#grip").click({timeout:60000});
await page.waitForFunction(()=>study.gripValue>.95,{},{timeout:60000});
const flexed=await page.evaluate(()=>study.handJoints.map(j=>j.bone.quaternion.toArray()));
if(rest.length<10||!flexed.some((q,i)=>q.some((v,j)=>Math.abs(v-rest[i][j])>.01)))throw Error("No animated finger rotation");
await page.screenshot({path:"test-output/hand-grip.png",timeout:90000});
await page.locator("#flex").evaluate(el=>{el.value="40";el.dispatchEvent(new Event("input",{bubbles:true}))});
await page.waitForFunction(()=>Math.abs(study.gripValue-.4)<.02,{},{timeout:60000});
await page.locator('button[data-p=".35"]').click({timeout:60000});
await page.waitForFunction(()=>!study.handRoot.visible&&!document.querySelector("#lab").hidden,{},{timeout:90000});
await page.locator("#thermal").click({timeout:60000});
await page.waitForFunction(()=>study.thermalMode,{},{timeout:60000});
await page.screenshot({path:"test-output/thermal.png",timeout:90000});
await page.locator('button[data-p=".94"]').click({timeout:60000});
await page.waitForFunction(()=>document.querySelector("#handcontrols").hidden&&document.querySelector("#lab").hidden,{},{timeout:90000});
await page.screenshot({path:"test-output/detail.png",timeout:90000});
if(errors.length)throw Error(errors.join("\n"));
console.log("V0.8 passed; articulated joints:",rest.length);
} catch(e){console.error(await page.evaluate(()=>({status:document.querySelector("#msg")?.textContent,rig:document.querySelector("#handstate")?.textContent,scroll:scrollY,errors:window.study?.handReady})));await page.screenshot({path:"test-output/failure.png",timeout:90000}).catch(()=>{});throw e}
}finally{await browser.close()}

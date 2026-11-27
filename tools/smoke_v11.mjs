import {chromium} from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
const browser=await chromium.launch({headless:true,args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"]});
await fs.mkdir("test-output",{recursive:true});
try{
for(const [name,viewport] of [["desktop",{width:1280,height:720}],["mobile",{width:390,height:844}]]){
const page=await browser.newPage({viewport,deviceScaleFactor:1,reducedMotion:"reduce"});
const errors=[];page.on("pageerror",e=>errors.push(e.message));page.on("console",m=>{if(m.type()==="error")errors.push(m.text())});
const root=path.resolve("node_modules/three"),prefix="https://cdn.jsdelivr.net/npm/three@0.178.0/";
await page.route(prefix+"**",async route=>{
const file=path.resolve(root,new URL(route.request().url()).pathname.split("/three@0.178.0/")[1]);
if(!file.startsWith(root+path.sep))return route.abort();
await route.fulfill({body:await fs.readFile(file),contentType:"application/javascript"});
});
const shot=async suffix=>page.screenshot({path:"test-output/"+name+"-"+suffix+".png",timeout:90000});
try{
await page.goto("http://127.0.0.1:8765/v11/",{waitUntil:"domcontentloaded",timeout:90000});
await page.waitForFunction(()=>window.study?.version==="1.1"&&study.handReady&&study.bakeAvailable&&document.querySelector("#status").hidden,{},{timeout:180000});
await page.waitForFunction(()=>document.querySelector("#diagnostics").textContent.includes("HDRI"),{},{timeout:120000});
await page.waitForFunction(()=>study.photoReady&&study.photoActive&&study.macroReady&&document.querySelector("#plate").complete,{},{timeout:120000});
if(!(await page.evaluate(()=>study.pivot.visible&&!study.desk.visible&&study.scene.background===null)))throw Error("Hybrid opening not active");
await shot("01-workshop");
await page.locator("#settingsToggle").click();
await page.locator("#photoToggle").click();
await page.waitForFunction(()=>!study.photoActive&&study.desk.visible,{},{timeout:90000});
await shot("01-live-comparison");
await page.locator("#photoToggle").click();
await page.locator("#settingsToggle").click();
await page.waitForFunction(()=>study.photoActive,{},{timeout:90000});
for(const [p,label] of [[".23","02-object"],[".43","03-touch"],[".66","04-material"],[".94","05-ritual"]]){
await page.locator('button[data-p="'+p+'"]').click({timeout:90000});
await page.waitForFunction(x=>Math.abs(study.story-Number(x))<.015,p,{timeout:90000});
if(await page.evaluate(()=>study.photoActive))throw Error("Photo plate leaked into live chapters");
if(p===".43"&&!(await page.evaluate(()=>study.handRoot.visible)))throw Error("Hand not visible");
if(p===".94"&&!(await page.evaluate(()=>study.ritualRoot.visible&&study.beans.length===23)))throw Error("Final scene missing");
await shot(label);
}
await page.locator("#replay").click({timeout:90000});
await page.waitForFunction(()=>study.story<.025,{},{timeout:90000});
await page.locator("#settingsToggle").click();
await page.locator("#experiments").click();
await page.locator("#settingsToggle").click();
await page.locator('button[data-p=".23"]').click({timeout:90000});
await page.waitForFunction(()=>!document.querySelector("#lab").hidden,{},{timeout:90000});
await page.locator("#thermal").click({timeout:90000});
await page.waitForFunction(()=>study.thermalMode,{},{timeout:90000});
await shot("06-thermal");
await page.locator('button[data-p=".43"]').click({timeout:90000});
await page.waitForFunction(()=>!document.querySelector("#handcontrols").hidden,{},{timeout:90000});
await page.locator("#grip").click({timeout:90000});
await page.waitForFunction(()=>study.gripValue>.95,{},{timeout:90000});
await shot("07-grip");
if(name==="desktop"){
await page.locator("#settingsToggle").click();
await page.locator("#film").click({timeout:90000});
await page.locator("#settingsToggle").click();
await shot("08-film");
if(await page.locator("#film").getAttribute("aria-pressed")!=="true")throw Error("Film failed");
}
if(errors.length)throw Error(errors.join("\n"));
console.log(name,"PASS: all five chapters, baked maps, hand, thermal, replay");
}catch(e){console.error(name,e.message);await shot("failure").catch(()=>{});throw e}finally{await page.close()}
}
}finally{await browser.close()}

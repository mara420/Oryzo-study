import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
const root=process.cwd(),browser=await chromium.launch({headless:true,args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"]});
await fs.mkdir("test-output",{recursive:true});
try{
 for(const [name,viewport] of [["desktop",{width:960,height:540}],["mobile",{width:390,height:844}]]){
 const page=await browser.newPage({viewport,deviceScaleFactor:1,reducedMotion:"reduce"});
 const errors=[];page.on("pageerror",e=>errors.push(e.message));page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
 const prefix="https://cdn.jsdelivr.net/npm/three@0.178.0/";
 await page.route(prefix+"**",async route=>{
 const filename=path.resolve(root,"node_modules/three",new URL(route.request().url()).pathname.split("/three@0.178.0/")[1]);
 if(!filename.startsWith(path.resolve(root,"node_modules/three")+path.sep))return route.abort();
 await route.fulfill({body:await fs.readFile(filename),contentType:"application/javascript"});
 });
 try{
 await page.goto("http://127.0.0.1:8765/v06/",{waitUntil:"domcontentloaded",timeout:60000});
 await page.waitForFunction(()=>window.study?.version==="0.6"&&document.querySelector("#status").hidden,{},{timeout:120000});
 await page.waitForFunction(()=>study.bakeAvailable&&document.querySelector("#diagnostics").textContent.includes("HDRI"),{},{timeout:120000});
 const shot=async s=>page.screenshot({path:"test-output/"+name+"-"+s+".png",timeout:90000});
 await shot("intro-baked");
 await page.locator("#lightctl").click({timeout:60000});
 if(await page.locator("#lightctl").getAttribute("aria-pressed")!=="false")throw Error("Baked lighting toggle failed");
 await shot("intro-live");
 await page.locator('button[data-p=".48"]').click({timeout:60000});
 await page.waitForFunction(()=>!document.querySelector("#lab").hidden,{},{timeout:90000});
 await page.locator("#thermal").click({timeout:60000});
 await page.waitForFunction(()=>study.thermalMode,{},{timeout:60000});
 await page.locator("#energy").evaluate(el=>{el.value="90";el.dispatchEvent(new Event("input",{bubbles:true}));});
 if(await page.evaluate(()=>study.thermalUniforms.uEnergy.value)!==.9)throw Error("Thermal energy control failed");
 await shot("thermal");
 await page.locator("#flip").click({timeout:60000});
 await shot("flip");
 await page.locator("#surface").click({timeout:60000});
 await page.locator("#film").click({timeout:60000});
 await shot("film");
 if(await page.locator("#film").getAttribute("aria-pressed")!=="true")throw Error("Film rendering unavailable");
 await page.locator('button[data-p=".94"]').click({timeout:60000});
 await page.waitForFunction(()=>document.querySelector("#lab").hidden&&document.querySelector('button[data-p=".94"]').getAttribute("aria-current")==="true",{},{timeout:90000});
 await shot("detail");
 if(errors.length)throw Error(errors.join("\n"));
 console.log(name,"PASSED",await page.evaluate(()=>study.renderer.getContext().getParameter(study.renderer.getContext().VERSION)));
 }catch(e){console.error(name,await page.evaluate(()=>({url:location.href,scroll:scrollY,status:document.querySelector("#msg")?.textContent,diagnostics:document.querySelector("#diagnostics")?.textContent})));await page.screenshot({path:"test-output/"+name+"-failure.png",timeout:90000}).catch(()=>{});throw e;}
 finally{await page.close();}
 }
}finally{await browser.close();}

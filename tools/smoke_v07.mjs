import {chromium} from "playwright";
import fs from "node:fs/promises";
import path from "node:path";
const browser=await chromium.launch({headless:true,args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"]});
await fs.mkdir("test-output",{recursive:true});
try{
 const page=await browser.newPage({viewport:{width:960,height:540},deviceScaleFactor:1});
 const errors=[];page.on("pageerror",e=>errors.push(e.message));page.on("console",m=>{if(m.type()==="error")console.log("browser:",m.text());});
 const root=path.resolve("node_modules/three"),prefix="https://cdn.jsdelivr.net/npm/three@0.180.0/";
 await page.route(prefix+"**",async route=>{
  const f=path.resolve(root,new URL(route.request().url()).pathname.split("/three@0.180.0/")[1]);
  if(!f.startsWith(root+path.sep))return route.abort();
  await route.fulfill({body:await fs.readFile(f),contentType:"application/javascript"});
 });
 await page.goto("http://127.0.0.1:8765/v07/",{waitUntil:"domcontentloaded",timeout:90000});
 await page.waitForFunction(()=>window.study?.version==="0.7"&&document.querySelector("#status").hidden,{},{timeout:120000});
 await page.screenshot({path:"test-output/mesh.png",timeout:90000});
 await page.waitForFunction(()=>study.ready,{},{timeout:120000});
 const info=await page.evaluate(()=>({splats:study.numSplats,webgl:study.renderer.getContext().getParameter(study.renderer.getContext().VERSION)}));
 if(info.splats!==60000)throw Error("Unexpected count "+info.splats);
 await page.locator("#splat").click({timeout:60000});
 await page.waitForFunction(()=>study.mode==="splat"&&!study.product.visible,{},{timeout:60000});
 await page.waitForTimeout(1500);
 await page.screenshot({path:"test-output/hybrid.png",timeout:90000});
 await page.locator("#mesh").click({timeout:60000});
 await page.waitForFunction(()=>study.mode==="mesh"&&study.product.visible,{},{timeout:60000});
 if(errors.length)throw Error(errors.join("\n"));
 console.log("V0.7 controls passed",JSON.stringify(info));
}finally{await browser.close()}

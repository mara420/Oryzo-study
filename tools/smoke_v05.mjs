import { chromium } from "playwright";
import fs from "node:fs/promises";
import path from "node:path";

const root=process.cwd();
const browser=await chromium.launch({headless:true,args:["--use-gl=angle","--use-angle=swiftshader","--enable-unsafe-swiftshader","--disable-dev-shm-usage"]});
await fs.mkdir("test-output",{recursive:true});
try {
 for(const [name,viewport] of [["desktop",{width:1365,height:768}],["mobile",{width:390,height:844}]]){
  const page=await browser.newPage({viewport,deviceScaleFactor:1});
  const errors=[];
  page.on("pageerror",e=>errors.push(e.message));
  page.on("console",m=>{if(m.type()==="error")errors.push(m.text());});
  // Same Three.js version, local files for reproducible testing without CDN latency.
  const prefix="https://cdn.jsdelivr.net/npm/three@0.178.0/";
  await page.route(prefix+"**",async route=>{
   const filename=path.resolve(root,"node_modules/three",new URL(route.request().url()).pathname.split("/three@0.178.0/")[1]);
   if(!filename.startsWith(path.resolve(root,"node_modules/three")+path.sep))return route.abort();
   await route.fulfill({body:await fs.readFile(filename),contentType:"application/javascript"});
  });
  await page.goto("http://127.0.0.1:8765/v05/",{waitUntil:"domcontentloaded",timeout:60000});
  await page.waitForFunction(()=>window.study?.version==="0.5"&&document.querySelector("#status").hidden,{},{timeout:120000});
  await page.waitForFunction(()=>document.querySelector("#diagnostics").textContent.includes("GLB + HDRI"),{},{timeout:90000});
  const info=await page.evaluate(()=>({version:study.version,webgl:study.renderer.getContext().getParameter(study.renderer.getContext().VERSION),matNodes:study.matGroup?.children.length||0,cutterNodes:study.cutterGroup?.children.length||0,renderCalls:study.renderer.info.render.calls}));
  console.log(name,JSON.stringify(info));
  if(!info.matNodes||!info.cutterNodes)throw Error("Expected composition groups missing");
  await page.screenshot({path:"test-output/"+name+"-intro.png"});
  await page.locator('button[data-p=".48"]').click();
  await page.waitForFunction(()=>document.querySelector('button[data-p=".48"]').getAttribute("aria-current")==="true",{},{timeout:20000});
  await page.waitForTimeout(1500);
  await page.screenshot({path:"test-output/"+name+"-object.png"});
  await page.locator('button[data-p=".94"]').click();
  await page.waitForFunction(()=>document.querySelector('button[data-p=".94"]').getAttribute("aria-current")==="true",{},{timeout:20000});
  await page.waitForTimeout(1500);
  await page.screenshot({path:"test-output/"+name+"-detail.png"});
  const film=page.locator("#film"),before=await film.getAttribute("aria-pressed");
  await film.click();
  if(await film.getAttribute("aria-pressed")===before)throw Error("Film toggle failed");
  await page.waitForTimeout(500);
  if(errors.length)throw Error(name+" browser errors: "+errors.join("\n"));
  await page.close();
 }
}finally{await browser.close();}

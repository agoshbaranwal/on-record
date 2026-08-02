/**
 * The MEASURED gate — Phase 3's real promise.
 *
 * Static rules can only prove that no font-size is declared below 13px. They cannot prove what a
 * phone actually renders, which is the thing Agosh kept pointing at. So this walks the real pages
 * in a real browser at 390px and measures every visible text node.
 *
 * It also checks contrast against the actual composited background, and looks for overlapping text
 * boxes — the failure that produced the screenshot where Bedrock ran under the masthead.
 *
 *   node scripts/check-rendered.mjs --base http://127.0.0.1:PORT --paths / /place/mumbai /how-we-know
 */
import { spawn } from "node:child_process";
import { writeFileSync, mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const args = process.argv.slice(2);
const argOf = (k, d) => { const i = args.indexOf(k); return i >= 0 ? args[i + 1] : d; };
const BASE = argOf("--base", "http://127.0.0.1:4701");
const PATHS = (() => { const i = args.indexOf("--paths"); return i >= 0 ? args.slice(i + 1) : ["/"]; })();
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const FLOOR = 13;

const probe = `
(function(){
  function lum(c){var m=c.match(/[\\d.]+/g)||[0,0,0];var f=m.slice(0,3).map(function(v){v=v/255;
    return v<=0.03928?v/12.92:Math.pow((v+0.055)/1.055,2.4);});
    return 0.2126*f[0]+0.7152*f[1]+0.0722*f[2];}
  function bgOf(el){var n=el;while(n&&n!==document.documentElement){var b=getComputedStyle(n).backgroundColor;
    if(b&&!/rgba\\(0, 0, 0, 0\\)|transparent/.test(b))return b;n=n.parentElement;}
    return getComputedStyle(document.body).backgroundColor;}
  var small=[],low=[],over=[],leaves=[];
  document.querySelectorAll("body *").forEach(function(e){
    var cs=getComputedStyle(e); if(cs.display==="none"||cs.visibility==="hidden")return;
    var t=(e.textContent||"").trim(); if(!t)return;
    for(var i=0;i<e.children.length;i++) if((e.children[i].textContent||"").trim().length>t.length*0.8)return;
    leaves.push(e);
    var fs=parseFloat(cs.fontSize);
    if(fs<${FLOOR}-0.01) small.push(fs.toFixed(1)+"px "+(e.className||e.tagName)+" :: "+t.slice(0,34));
    var r=(lum(cs.color)+0.05)/(lum(bgOf(e))+0.05), ratio=r<1?1/r:r;
    var big=fs>=24||(fs>=18.66&&(cs.fontWeight>=600));
    if(ratio < (big?3:4.5)) low.push(ratio.toFixed(2)+":1 "+fs.toFixed(0)+"px "+(e.className||e.tagName)+" :: "+t.slice(0,26));
  });
  for(var a=0;a<leaves.length;a++)for(var b=a+1;b<leaves.length;b++){
    var A=leaves[a],B=leaves[b]; if(A.contains(B)||B.contains(A))continue;
    var ra=A.getBoundingClientRect(),rb=B.getBoundingClientRect();
    if(ra.width<4||rb.width<4)continue;
    var ox=Math.min(ra.right,rb.right)-Math.max(ra.left,rb.left);
    var oy=Math.min(ra.bottom,rb.bottom)-Math.max(ra.top,rb.top);
    if(ox>8&&oy>8&&over.length<5)over.push((A.className||A.tagName)+" X "+(B.className||B.tagName));
  }
  document.title="R::"+JSON.stringify({small:small,low:low,over:over,
    scrollW:document.documentElement.scrollWidth,nodes:leaves.length});
})();
`;

// The shell must be served from the SAME ORIGIN as the app: a file:// page cannot read the
// contentDocument of an http:// iframe, and the probe silently hangs forever instead of failing.
const SHELL = join(fileURLToPath(new URL("../apps/web/public/", import.meta.url)), "__probe.html");
writeFileSync(SHELL, `<!doctype html><meta charset=utf-8><style>html,body{margin:0}iframe{width:390px;height:844px;border:0}</style>
<iframe id="f"></iframe>
<script>
var p=new URLSearchParams(location.search).get("p")||"/";
var f=document.getElementById("f");
f.onload=function(){setTimeout(function(){
  var d=f.contentDocument, s=d.createElement("script");
  s.textContent=${JSON.stringify(probe)}; d.body.appendChild(s); document.title=d.title;},900);};
f.src=p;
</script>`);

async function measure(path) {
  const dir = mkdtempSync(join(tmpdir(), "onrec-"));
  return new Promise((res) => {
    const p = spawn(CHROME, ["--headless=new", "--window-size=560,900", "--virtual-time-budget=7000",
      `--user-data-dir=${dir}`, "--dump-dom", `${BASE}/__probe.html?p=${encodeURIComponent(path)}`],
      { stdio: ["ignore", "pipe", "ignore"] });
    let out = "";
    p.stdout.on("data", (d) => (out += d));
    // Chrome does not always exit after --dump-dom; never wait on it forever.
    const kill = setTimeout(() => { try { p.kill("SIGKILL"); } catch {} }, 20000);
    p.on("close", () => { clearTimeout(kill);
      const m = out.match(/R::(\{[\s\S]*?\})<\/title>/); res(m ? JSON.parse(m[1]) : null); });
  });
}

let ok = true;
for (const path of PATHS) {
  const r = await measure(path);
  if (!r) { console.log(`  ✗ ${path} — could not measure`); ok = false; continue; }
  const pass = r.small.length === 0 && r.low.length === 0 && r.over.length === 0 && r.scrollW <= 391;
  console.log(`  ${pass ? "✓" : "✗"} ${path.padEnd(18)} ${r.nodes} text nodes · ${r.scrollW}px wide`);
  for (const x of r.small) console.log(`        under ${FLOOR}px: ${x}`);
  for (const x of r.low) console.log(`        low contrast: ${x}`);
  for (const x of r.over) console.log(`        overlap: ${x}`);
  ok &&= pass;
}
console.log(ok ? "\n  RENDERED GATE PASS (390px: no text under 13px, AA contrast, no overlap, no h-scroll)"
                : "\n  *** RENDERED GATE FAILED ***");
process.exit(ok ? 0 : 1);

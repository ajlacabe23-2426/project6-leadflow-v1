/* LeadFlow lightweight website launcher. Local demo only: do not expose
   publicly without tenant isolation, consent review, CSP and abuse controls. */
(function(){
"use strict";
var script=document.currentScript;
if(!script)return;
var url;
try{url=new URL(script.src);}catch{return;}
if(!/^https?:$/.test(url.protocol))return;
var label=(script.getAttribute("data-label")||"Request a callback").trim().slice(0,60)||"Request a callback";
var chosen=script.getAttribute("data-accent")||"#193b62";
var accent=/^#[0-9a-fA-F]{6}$/.test(chosen)?chosen:"#193b62";
var align=script.getAttribute("data-align")==="left"?"left":"right";
var root=document.createElement("div");
root.style.cssText="position:fixed;bottom:18px;"+align+":18px;z-index:2147483000;";
var shadow=root.attachShadow({mode:"open"});
var style=document.createElement("style");
style.textContent="*{box-sizing:border-box}.launcher{background:var(--lf-accent);color:#fff;border:1px solid #ffffff33;border-radius:999px;padding:14px 19px;font:700 14px system-ui;cursor:pointer;box-shadow:0 12px 32px #06142549;min-height:46px}.launcher:focus-visible{outline:3px solid #77d7f7;outline-offset:3px}.frame{width:min(380px,calc(100vw - 34px));height:min(590px,calc(100dvh - 115px));background:#fff;border:1px solid #b6c6d8;border-radius:18px;box-shadow:0 20px 50px #07172e55;display:block;margin:0 0 13px;overflow:hidden}.frame[hidden]{display:none}@media(prefers-reduced-motion:reduce){*{transition:none!important}}";
var button=document.createElement("button");
button.className="launcher";button.type="button";button.textContent=label;
button.setAttribute("aria-expanded","false");
button.setAttribute("aria-label","Open LeadFlow inquiry form");
button.style.setProperty("--lf-accent",accent);
var frame=document.createElement("iframe");
frame.className="frame";frame.hidden=true;frame.title="LeadFlow inquiry form";
frame.setAttribute("referrerpolicy","no-referrer");
frame.setAttribute("loading","lazy");
frame.src=url.origin+"/widget?accent="+encodeURIComponent(accent);
function setOpen(open){
  frame.hidden=!open;
  button.setAttribute("aria-expanded",String(open));
  button.setAttribute("aria-label",open?"Close LeadFlow inquiry form":"Open LeadFlow inquiry form");
  button.textContent=open?"Close inquiry":label;
  if(open)frame.focus();
  else button.focus();
}
button.addEventListener("click",function(){setOpen(frame.hidden);});
shadow.addEventListener("keydown",function(event){if(event.key==="Escape"&&!frame.hidden){event.preventDefault();setOpen(false);}});
shadow.append(style,frame,button);
document.body.appendChild(root);
}());

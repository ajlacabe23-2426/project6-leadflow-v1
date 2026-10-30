/* LeadFlow self-service embed: iframe isolates customer intake from host websites.
   Demonstration only. Hosting, rate limits and privacy approval required for live use. */
(function(){
"use strict";
var script=document.currentScript;
if(!script)return;
var url;
try{url=new URL(script.src);}catch{return;}
if(!/^https?:$/.test(url.protocol))return;
var label=script.getAttribute("data-label") || "Request a callback";
var root=document.createElement("div");
root.style.cssText="position:fixed;bottom:18px;right:18px;z-index:2147483000;";
var shadow=root.attachShadow({mode:"open"});
var style=document.createElement("style");
style.textContent="*{box-sizing:border-box}.launcher{background:#193b62;color:white;border:0;border-radius:28px;padding:14px 18px;font:700 14px system-ui;cursor:pointer;box-shadow:0 5px 22px #0003}.frame{width:min(360px,calc(100vw - 30px));height:min(570px,calc(100dvh - 110px));background:#fff;border:1px solid #b6c6d8;border-radius:16px;box-shadow:0 12px 36px #0003;display:block;margin:0 0 12px}.frame[hidden]{display:none}";
var button=document.createElement("button");
button.className="launcher";button.type="button";button.textContent=label;
button.setAttribute("aria-expanded","false");
button.setAttribute("aria-label","Open LeadFlow inquiry form");
var frame=document.createElement("iframe");
frame.className="frame";frame.hidden=true;frame.title="LeadFlow inquiry form";
frame.setAttribute("referrerpolicy","no-referrer");
frame.setAttribute("loading","lazy");
frame.src=url.origin+"/widget";
button.addEventListener("click",function(){
  frame.hidden=!frame.hidden;
  button.setAttribute("aria-expanded",String(!frame.hidden));
  button.textContent=frame.hidden?label:"Close inquiry";
});
shadow.append(style,frame,button);
document.body.appendChild(root);
}());
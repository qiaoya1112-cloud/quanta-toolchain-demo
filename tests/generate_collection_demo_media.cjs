/* Generate local illustrative media for the collection prototype, never production recordings. */
const fs=require('node:fs');
const path=require('node:path');
const {spawn}=require('node:child_process');
const output=path.resolve(__dirname,'../static/post_training_collection/media');
const profile=path.resolve(__dirname,'../instance/collection-media-generator');
const delay=ms=>new Promise(r=>setTimeout(r,ms));
async function main(){
  fs.mkdirSync(output,{recursive:true});
  const chrome=spawn('C:/Program Files/Google/Chrome/Application/chrome.exe',['--headless','--disable-gpu','--no-first-run',`--user-data-dir=${profile}`,'--remote-debugging-port=9372','about:blank'],{stdio:'ignore',windowsHide:true});
  let ws;
  try{
    let page;
    for(let i=0;i<100;i++){try{page=(await fetch('http://127.0.0.1:9372/json/list').then(r=>r.json())).find(p=>p.type==='page');if(page)break;}catch(_){}await delay(100);}
    ws=new WebSocket(page.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
    let seq=0;const pending=new Map();ws.onmessage=e=>{const m=JSON.parse(e.data);if(m.id&&pending.has(m.id)){const p=pending.get(m.id);pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}};
    const call=(method,params)=>new Promise((resolve,reject)=>{const id=++seq;pending.set(id,{resolve,reject});ws.send(JSON.stringify({id,method,params}));});
    const result=await call('Runtime.evaluate',{awaitPromise:true,returnByValue:true,expression:`(${capture.toString()})()`});
    if(result.exceptionDetails)throw Error(result.exceptionDetails.exception?.description||result.exceptionDetails.text);
    for(const clip of result.result.value){fs.writeFileSync(path.join(output,clip.camera+'.webm'),Buffer.from(clip.video,'base64'));fs.writeFileSync(path.join(output,clip.camera+'.png'),Buffer.from(clip.poster,'base64'));}
    console.log('Generated three local illustrative clips in '+output);
  }finally{ws?.close();chrome.kill();}
}
async function capture(){
  const cameras=['head','left','right'];
  const canvases=cameras.map(()=>{const c=document.createElement('canvas');c.width=640;c.height=360;document.body.append(c);return c;});
  function draw(canvas,camera,t){
    const c=canvas.getContext('2d'),p=Math.min(1,Math.max(0,(t-1)/4)),ease=(1-Math.cos(p*Math.PI))/2;
    const grad=c.createLinearGradient(0,0,0,360);grad.addColorStop(0,'#c9d6d9');grad.addColorStop(1,'#ebefed');c.fillStyle=grad;c.fillRect(0,0,640,360);
    c.save();if(camera==='left'){c.translate(-75,-75);c.scale(1.45,1.45);}if(camera==='right'){c.translate(-200,-65);c.scale(1.45,1.45);}
    c.fillStyle='#aab8b9';c.fillRect(65,72,510,266);c.fillStyle='#e5e4da';c.fillRect(60,66,520,256);
    c.strokeStyle='#ccd0c7';c.lineWidth=1;for(let x=75;x<580;x+=35){c.beginPath();c.moveTo(x,66);c.lineTo(x,322);c.stroke();}for(let y=81;y<322;y+=30){c.beginPath();c.moveTo(60,y);c.lineTo(580,y);c.stroke();}
    c.fillStyle='#b7c8c9';c.fillRect(358,91,153,103);c.fillStyle='#eff4f1';c.fillRect(365,98,139,86);c.strokeStyle='#94abad';c.strokeRect(365,98,139,86);
    c.fillStyle='#d2c3a8';c.fillRect(121,99,84,55);c.fillStyle='#e9dcc3';c.fillRect(127,104,72,44);
    const x=245+ease*175,y=218-ease*74-Math.sin(p*Math.PI)*36;
    c.fillStyle='#364a4c22';c.beginPath();c.ellipse(x+8,239-ease*80,24,9,0,0,Math.PI*2);c.fill();
    function arm(bx,by,ex,ey,tx,ty){
      c.lineCap='round';c.lineJoin='round';c.strokeStyle='#607779';c.lineWidth=27;c.beginPath();c.moveTo(bx,by);c.lineTo(ex,ey);c.lineTo(tx,ty);c.stroke();
      c.strokeStyle='#c8d6d4';c.lineWidth=18;c.beginPath();c.moveTo(bx,by);c.lineTo(ex,ey);c.lineTo(tx,ty);c.stroke();
      for(const [jx,jy] of [[bx,by],[ex,ey]]){c.fillStyle='#405a5e';c.beginPath();c.arc(jx,jy,15,0,7);c.fill();c.fillStyle='#91acac';c.beginPath();c.arc(jx,jy,7,0,7);c.fill();}
      c.strokeStyle='#344d50';c.lineWidth=6;c.beginPath();c.moveTo(tx-11,ty+13);c.lineTo(tx-14,ty-5);c.moveTo(tx+11,ty+13);c.lineTo(tx+14,ty-5);c.stroke();
    }
    arm(113,308,154,225,x,y+9);arm(529,306,476,244,452,224);
    c.fillStyle='#c4854d';c.fillRect(x-11,y-11,23,24);c.fillStyle='#e9b77d';c.beginPath();c.moveTo(x-11,y-11);c.lineTo(x-3,y-18);c.lineTo(x+20,y-18);c.lineTo(x+12,y-11);c.fill();c.fillStyle='#a76b3b';c.beginPath();c.moveTo(x+12,y-11);c.lineTo(x+20,y-18);c.lineTo(x+20,y+6);c.lineTo(x+12,y+13);c.fill();
    c.restore();c.fillStyle='#163b4499';c.fillRect(16,16,139,26);c.fillStyle='#fff';c.font='12px sans-serif';c.fillText('INTERACTION DEMO',25,34);
    c.fillStyle='#1d393b99';c.fillRect(532,320,92,24);c.fillStyle='#fff';c.font='12px monospace';c.fillText('00:0'+Math.floor(t)+'.'+Math.floor(t%1*10),543,336);
  }
  const tracks=canvases.map(c=>c.captureStream(20));
  const recorders=tracks.map(s=>new MediaRecorder(s,{mimeType:'video/webm;codecs=vp8',videoBitsPerSecond:650000}));
  const results=recorders.map((r,i)=>new Promise(resolve=>{const chunks=[];r.ondataavailable=e=>{if(e.data.size)chunks.push(e.data);};r.onstop=async()=>{const blob=new Blob(chunks,{type:'video/webm'});const fr=new FileReader();fr.onload=()=>resolve({camera:cameras[i],video:fr.result.split(',')[1],poster:canvases[i].dataset.poster});fr.readAsDataURL(blob);};}));
  canvases.forEach((c,i)=>{draw(c,cameras[i],0);c.dataset.poster=c.toDataURL('image/png').split(',')[1];});
  recorders.forEach(r=>r.start());
  const start=performance.now();await new Promise(resolve=>{function tick(){const t=(performance.now()-start)/1000;canvases.forEach((c,i)=>draw(c,cameras[i],t));if(t<7) setTimeout(tick,40);else resolve();}tick();});
  recorders.forEach(r=>r.stop());const output=await Promise.all(results);tracks.forEach(s=>s.getTracks().forEach(t=>t.stop()));return output;
}
main().catch(e=>{console.error(e);process.exitCode=1;});

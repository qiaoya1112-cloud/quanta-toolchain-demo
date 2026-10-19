// Keep each gallery's position, including when it is recreated inside Common's iframe.
(()=>{
  const key=`component-scroll:${location.pathname}${location.search}`;
  let saved=null;
  try{saved=JSON.parse(sessionStorage.getItem(key));}catch(_){}
  let restoring=!!saved;
  if(document.documentElement.classList.contains('gallery-loading')&&'scrollRestoration' in history)history.scrollRestoration='manual';
  let timer;
  const save=()=>{
    if(restoring)return;
    try{sessionStorage.setItem(key,JSON.stringify({x:scrollX,y:scrollY}));}catch(_){}
  };
  window.addEventListener('scroll',()=>{clearTimeout(timer);timer=setTimeout(save,100);},{passive:true});
  window.addEventListener('pagehide',save);
  window.addEventListener('beforeunload',save);
  const restore=async()=>{
    if(document.fonts)await document.fonts.ready;
    requestAnimationFrame(()=>requestAnimationFrame(()=>{
      if(saved&&!location.hash)window.scrollTo({left:saved.x,top:saved.y,behavior:'instant'});
      restoring=false;
      document.documentElement.classList.remove('gallery-loading');
    }));
  };
  if(document.readyState==='complete')restore();
  else window.addEventListener('load',restore,{once:true});
})();
(()=>{
  const key=document.documentElement.dataset.previewThemeKey||"workbench-component-theme";
  const button=document.querySelector("[data-component-theme]");
  if(!location.pathname.endsWith('/workbench/segmented-track.html')&&!document.documentElement.hasAttribute('data-preview-theme-key')){
    button?.remove();
    document.documentElement.dataset.theme='light';
    for(const element of [document.documentElement,document.body]){
      element.classList.remove('component-dark');
      element.classList.add('theme-light');
    }
    return;
  }
  if(!button)return;
  const apply=theme=>{
    theme=['light','dark','blue'].includes(theme)?theme:'dark';
    if(!button.querySelector(`[data-preview-theme="${theme}"]`))theme=theme==='dark'&&button.querySelector('[data-preview-theme="blue"]')?'blue':button.querySelector('[data-preview-theme]')?.dataset.previewTheme||'light';
    const dark=theme!=='light';
    for(const element of [document.documentElement,document.body]){
      element.classList.toggle('component-dark',dark);
      element.classList.toggle('theme-light',!dark);
    }
    document.documentElement.dataset.theme=dark?'dark':'light';
    document.documentElement.dataset.workbenchTheme=theme;
    if(window.parent!==window)window.parent.postMessage({type:'common-preview-theme',theme},'*');
    button.querySelectorAll('[data-preview-theme]').forEach(item=>item.setAttribute('aria-pressed',String(item.dataset.previewTheme===theme)));
    document.querySelectorAll('.workbench-theme-tabs [data-theme],timeline-controls [data-theme]').forEach(control=>{
      control.classList.toggle('is-active',control.dataset.theme===theme);
      control.setAttribute('aria-pressed',String(control.dataset.theme===theme));
    });
  };
  let theme=document.documentElement.dataset.workbenchTheme||'dark';
  try{theme=localStorage.getItem(key)||theme;}catch(_){}
  apply(theme);
  window.addEventListener('message',event=>{
    if(event.source===window.parent&&event.data?.type==='common-preview-theme-request')window.parent.postMessage({type:'common-preview-theme',theme:document.documentElement.dataset.workbenchTheme},'*');
  });
  button.addEventListener('click',event=>{
    const target=event.target.closest('[data-preview-theme]');if(!target)return;
    apply(target.dataset.previewTheme);
    try{localStorage.setItem(key,target.dataset.previewTheme);}catch(_){}
  });
  new MutationObserver(()=>{
    const theme=document.documentElement.dataset.workbenchTheme;
    button.querySelectorAll('[data-preview-theme]').forEach(item=>item.setAttribute('aria-pressed',String(item.dataset.previewTheme===theme)));
  }).observe(document.documentElement,{attributes:true,attributeFilter:['data-workbench-theme']});
})();

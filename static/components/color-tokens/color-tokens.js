(()=>{
  const groups=[
    ['背景色',[
      ['页面背景','--color-bg-canvas'],['内容表面','--color-bg-surface'],['抬升表面','--color-bg-surface-raised'],
      ['次级表面','--color-bg-surface-subtle'],['输入区域','--color-bg-input'],['悬浮背景','--color-bg-hover'],
      ['区块标题','--color-bg-section-header'],['分组标题','--color-bg-group-header'],['轨道背景','--color-bg-track']
    ]],
    ['边框与分隔线',[
      ['默认边框','--color-border'],['强调边框','--color-border-strong'],['媒体边框','--color-border-media'],
      ['轨道边框','--color-border-track'],['分隔线','--color-divider']
    ]],
    ['文字色',[
      ['主要文字','--color-text-primary'],['次要文字','--color-text-secondary'],['弱化文字','--color-text-muted'],
      ['占位文字','--color-text-placeholder'],['反色文字','--color-text-inverse']
    ]],
    ['品牌与交互',[
      ['品牌主色','--color-brand'],['品牌悬浮','--color-brand-hover'],['品牌浅色','--color-brand-soft'],['品牌选中','--color-brand-selected']
    ]],
    ['深色导航',[
      ['导航表面','--color-inverse-surface'],['导航抬升表面','--color-inverse-raised'],['导航边框','--color-inverse-border'],
      ['导航文字','--color-inverse-text'],['导航弱化文字','--color-inverse-muted']
    ]],
    ['状态色',[
      ['成功','--color-success'],['范围','--color-range'],['警告','--color-warning'],['警告浅色','--color-warning-soft'],
      ['警告标记','--color-warning-marker'],['危险','--color-danger'],['危险浅色','--color-danger-soft']
    ]],
    ['通用辅助配色',[
      ['青绿色 · 强调色','--color-accent-teal'],['青绿色 · 底色','--color-accent-teal-soft'],
      ['灰色 · 强调色','--color-accent-gray'],['灰色 · 底色','--color-accent-gray-soft'],
      ['蓝色 · 强调色','--color-accent-blue'],['蓝色 · 底色','--color-accent-blue-soft'],
      ['薄荷绿 · 强调色','--color-accent-mint'],['薄荷绿 · 底色','--color-accent-mint-soft'],
      ['黄色 · 强调色','--color-accent-yellow'],['黄色 · 底色','--color-accent-yellow-soft'],
      ['紫色 · 强调色','--color-accent-purple'],['紫色 · 底色','--color-accent-purple-soft'],
      ['粉紫色 · 强调色','--color-accent-magenta'],['粉紫色 · 底色','--color-accent-magenta-soft'],
      ['粉色 · 强调色','--color-accent-pink'],['粉色 · 底色','--color-accent-pink-soft'],
      ['橙色 · 强调色','--color-accent-orange'],['橙色 · 底色','--color-accent-orange-soft'],
      ['珊瑚红 · 强调色','--color-accent-coral'],['珊瑚红 · 底色','--color-accent-coral-soft'],
      ['草绿 · 强调色','--color-accent-grass'],['草绿 · 底色','--color-accent-grass-soft'],
      ['青蓝 · 强调色','--color-accent-cyan'],['青蓝 · 底色','--color-accent-cyan-soft'],
      ['靛蓝 · 强调色','--color-accent-indigo'],['靛蓝 · 底色','--color-accent-indigo-soft'],
    ]],

  ];
  const root=document.querySelector('[data-color-token-groups]');
  const styles=getComputedStyle(document.documentElement);
  groups.forEach(([title,tokens])=>{
    const section=document.createElement('section');
    section.className='component-gallery__group color-token-group';
    const heading=document.createElement('h2');heading.textContent=title;
    const grid=document.createElement('div');grid.className='color-token-grid';
    tokens.forEach(([name,variable])=>{
      const value=styles.getPropertyValue(variable).trim()||'未定义';
      const card=document.createElement('article');card.className='color-token';
      card.style.setProperty('--token-color',`var(${variable}, transparent)`);
      card.innerHTML=`<span class="color-token__swatch" aria-hidden="true"></span><div class="color-token__info"><strong class="color-token__name"></strong><code class="color-token__variable"></code><output class="color-token__value"></output></div>`;
      card.querySelector('.color-token__name').textContent=name;
      card.querySelector('.color-token__variable').textContent=`var(${variable})`;
      card.querySelector('.color-token__value').textContent=value;
      grid.append(card);
    });
    section.append(heading,grid);root.append(section);
  });
})();

const paginationExample=document.querySelector('.general-pagination-example');
paginationExample?.addEventListener('click',event=>{
  const button=event.target.closest('button');if(!button||button.disabled)return;
  const buttons=[...paginationExample.querySelectorAll('button')];
  const index=buttons.indexOf(button);
  const next=index===0?1:index===3?2:index;
  buttons.forEach((item,i)=>{if(i===next)item.setAttribute('aria-current','page');else item.removeAttribute('aria-current');});
  buttons[0].disabled=next===1;buttons[3].disabled=next===2;
});

document.querySelectorAll('[data-component-destination]').forEach(link=>{
  link.addEventListener('click',event=>{
    if(window.parent===window)return;
    event.preventDefault();
    window.parent.postMessage({type:'common-preview-navigate',destination:link.dataset.componentDestination},'*');
  });
});

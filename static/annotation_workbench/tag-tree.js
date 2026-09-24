// The same taxonomy used by /data/tags, keyed by stable management IDs.
window.workbenchTagCatalog = (() => {
  const source = JSON.parse(document.getElementById('workbench-tag-tree').textContent);
  const leaves = new Map();
  function read(nodes, path=[], depth=1) {
    if (depth>3) return [];
    return nodes.map(node=>{
      const names=[...path,node.name];
      const rawChildren=node.tags || node.sub_tags || [];
      const result={id:node.id,name:node.name,path:names.join(' / '),depth,children:read(rawChildren,names,depth+1),leaf:!rawChildren.length};
      if(result.leaf)leaves.set(result.id,result);
      return result;
    });
  }
  const excluded = new Set(['quality', 'process', 'project_delivery']);
  return {tree:read(source.filter(node=>!excluded.has(node.id))),leaves};
})();

// Reuse the workbench's multi-select trigger, chips, option states and popover.
class WorkbenchTagTreeSelect extends HTMLElement {
  connectedCallback() {
    this.selected=new Set();
    this.innerHTML='<div class="workbench-multi-select__trigger input-like" role="button" tabindex="0" aria-label="选择标签" aria-haspopup="tree" aria-expanded="false"><span class="workbench-multi-select__value"></span><img src="/static/annotation_workbench/assets/icon-chevron.svg" alt=""></div><div class="workbench-multi-select__popover" hidden><div class="workbench-multi-select__options tag-tree-options" role="tree" aria-label="标签管理" aria-multiselectable="true"></div></div>';
    this.trigger=this.querySelector('[role=button]'); this.popup=this.querySelector('.workbench-multi-select__popover');
    const build=(nodes,parent)=>nodes.forEach(node=>{
      if(node.leaf){
        const option=document.createElement('button'); option.type='button'; option.dataset.tagLeaf=node.id; option.dataset.multiOption=node.id;
        option.setAttribute('role','treeitem'); option.setAttribute('aria-level',node.depth); option.setAttribute('aria-selected','false');
        option.textContent=node.name; option.title=node.path;
        const check=document.createElement('span'); check.textContent='✓'; option.append(check); parent.append(option);
      }else{
        const branch=document.createElement('details'); branch.dataset.tagBranch=node.id;
        const summary=document.createElement('summary'); summary.textContent=node.name;
        summary.setAttribute('role','treeitem'); summary.setAttribute('aria-level',node.depth); summary.setAttribute('aria-expanded','false');
        branch.addEventListener('toggle',()=>summary.setAttribute('aria-expanded',String(branch.open)));
        const children=document.createElement('div'); children.setAttribute('role','group'); build(node.children,children);
        branch.append(summary,children); parent.append(branch);
      }
    });
    build(workbenchTagCatalog.tree,this.querySelector('[role=tree]'));
    this.trigger.addEventListener('click',event=>{if(!event.target.closest('[data-remove-value]'))this.open(this.popup.hidden);});
    this.trigger.addEventListener('keydown',event=>{if(event.target===this.trigger && ['Enter',' '].includes(event.key)){event.preventDefault();this.open(this.popup.hidden);}});
    this.addEventListener('click',event=>{
      const remove=event.target.closest('[data-remove-value]'), option=event.target.closest('[data-tag-leaf]');
      if(remove)this.selected.delete(remove.dataset.removeValue);
      else if(option){const id=option.dataset.tagLeaf;this.selected.has(id)?this.selected.delete(id):this.selected.add(id);}
      else return;
      this.render(); this.dispatchEvent(new CustomEvent('multi-select-change',{bubbles:true,detail:{values:this.values}}));
    });
    this.outside=event=>{if(!this.contains(event.target))this.open(false);};
    this.escape=event=>{if(event.key==='Escape'){this.open(false);}};
    this.resize=()=>{if(!this.popup.hidden)this.position();};
    document.addEventListener('click',this.outside);document.addEventListener('keydown',this.escape);window.addEventListener('resize',this.resize);
    this.render();
  }
  disconnectedCallback(){document.removeEventListener('click',this.outside);document.removeEventListener('keydown',this.escape);window.removeEventListener('resize',this.resize);}
  get values(){return [...this.selected].filter(id=>workbenchTagCatalog.leaves.has(id));}
  setValues(values){this.selected=new Set(values.filter(id=>workbenchTagCatalog.leaves.has(id)));this.render();}
  position(){const rect=this.trigger.getBoundingClientRect();this.popup.style.width=`${Math.min(Math.max(rect.width,320),innerWidth-24)}px`;this.popup.style.left=`${Math.max(12,Math.min(rect.left,innerWidth-this.popup.offsetWidth-12))}px`;this.popup.style.top=`${Math.max(12,rect.top-this.popup.offsetHeight-8)}px`;}
  open(value){this.popup.hidden=!value;this.trigger.setAttribute('aria-expanded',String(value));this.trigger.classList.toggle('is-open',value);if(value)this.position();}
  render(){
    const value=this.querySelector('.workbench-multi-select__value');value.replaceChildren();
    this.values.forEach(id=>{
      const chip=document.createElement('span');chip.className='workbench-multi-select__tag';chip.textContent=workbenchTagCatalog.leaves.get(id).path;chip.title=chip.textContent;
      const remove=document.createElement('button');remove.type='button';remove.dataset.removeValue=id;remove.textContent='×';remove.setAttribute('aria-label',`移除${chip.textContent}`);chip.append(remove);value.append(chip);
    });
    if(!this.values.length){const placeholder=document.createElement('span');placeholder.className='workbench-multi-select__placeholder';placeholder.textContent='请选择标签';value.append(placeholder);}
    this.querySelectorAll('[data-tag-leaf]').forEach(option=>{const selected=this.selected.has(option.dataset.tagLeaf);option.classList.toggle('is-selected',selected);option.setAttribute('aria-selected',String(selected));});
  }
}
customElements.define('workbench-tag-tree-select',WorkbenchTagTreeSelect);

const assignmentBoard=document.querySelector('assignment-board');
const assignmentTitle=document.querySelector('.process-page__main>task-page-header');
const resourcePanel=assignmentBoard.querySelector('.assignment-resources');
resourcePanel.querySelector('h2')?.remove();
resourcePanel.querySelector(':scope > p')?.remove();
if(assignmentTitle)resourcePanel.prepend(assignmentTitle);
assignmentBoard.classList.add('has-column-titles');
const assignmentFilter=document.querySelector('.assignment-content>task-filter-bar');
if(assignmentFilter){
  assignmentBoard.querySelector('.assignment-overview').after(assignmentFilter);
  assignmentBoard.classList.add('has-detail-filter');
}
let assignmentFilters={scene:'质检'};
document.addEventListener('filter-change',event=>{
  assignmentFilters={...event.detail,scene:assignmentFilters.scene};
  document.querySelector('assignment-board').setFilters(assignmentFilters);
});
document.addEventListener('scene-change',event=>{
  assignmentFilters.scene=event.detail.value;
  document.querySelector('assignment-board').setFilters(assignmentFilters);
});

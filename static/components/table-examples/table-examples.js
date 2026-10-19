const categories = document.querySelector('.example-categories');
const preview = document.querySelector('iframe');
const links = [...categories.querySelectorAll('a')];
const storageKey = 'table-examples:selected-page';

function selectCategory(link) {
  links.forEach((item) => item.removeAttribute('aria-current'));
  link.setAttribute('aria-current', 'page');
  preview.title = link.textContent.trim();
  document.title = `表格示例 · ${preview.title}`;
  if (preview.src !== link.href) preview.src = link.href;
  try {
    sessionStorage.setItem(storageKey, link.getAttribute('href'));
  } catch (_) {
    // Keep navigation usable when browser storage is unavailable.
  }
}

let savedPage;
try {
  savedPage = sessionStorage.getItem(storageKey);
} catch (_) {}
selectCategory(links.find((link) => link.getAttribute('href') === savedPage) || links[0]);

categories.addEventListener('click', (event) => {
  const link = event.target.closest('a');
  if (!link || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
  event.preventDefault();
  selectCategory(link);
});

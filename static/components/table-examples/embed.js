// Render the real business page without duplicating the catalog navigation.
if (new URLSearchParams(location.search).get('embed') === 'table-example') {
  document.documentElement.classList.add('table-example-embedded');
}

document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('[data-list-filter]').forEach((form) => {
    const tableId = form.dataset.target;
    const table = document.getElementById(tableId);
    if (!table) return;

    const searchInput = form.querySelector('[data-filter-search]');
    const statusSelect = form.querySelector('[data-filter-status]');
    const resetButton = form.querySelector('[data-filter-reset]');
    const countNode = form.querySelector('[data-filter-count]');
    const rows = Array.from(table.querySelectorAll('tbody tr[data-filter-row]'));
    const emptyRow = table.querySelector('tbody tr[data-filter-empty]');

    const normalize = (value) => (value || '').toString().trim().toLocaleLowerCase('de-DE');

    const apply = () => {
      const query = normalize(searchInput ? searchInput.value : '');
      const status = normalize(statusSelect ? statusSelect.value : 'all');
      let visible = 0;

      rows.forEach((row) => {
        const haystack = normalize(row.dataset.search || row.textContent);
        const rowStatus = normalize(row.dataset.status || '');
        const matchesQuery = !query || haystack.includes(query);
        const matchesStatus = !status || status === 'all' || rowStatus === status;
        const show = matchesQuery && matchesStatus;
        row.hidden = !show;
        if (show) visible += 1;
      });

      if (emptyRow) emptyRow.hidden = visible !== 0;
      if (countNode) countNode.textContent = `${visible} Treffer`;
    };

    form.addEventListener('submit', (event) => {
      event.preventDefault();
      apply();
    });
    if (searchInput) searchInput.addEventListener('input', apply);
    if (statusSelect) statusSelect.addEventListener('change', apply);
    if (resetButton) {
      resetButton.addEventListener('click', () => {
        form.reset();
        if (searchInput) searchInput.value = '';
        if (statusSelect) statusSelect.value = 'all';
        apply();
        if (searchInput) searchInput.focus();
      });
    }

    apply();
  });
});

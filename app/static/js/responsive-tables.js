document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("table").forEach((table) => {
    const labels = Array.from(table.querySelectorAll("thead th"), (cell) =>
      cell.textContent.trim()
    );
    if (!labels.length) return;

    table.classList.add("responsive-table");
    table.querySelectorAll("tbody tr").forEach((row) => {
      const cells = Array.from(row.children).filter(
        (cell) => cell.tagName === "TD"
      );
      cells.forEach((cell, index) => {
        if (!cell.hasAttribute("colspan")) {
          cell.dataset.label = labels[index] || "";
        }
      });
    });
  });
});

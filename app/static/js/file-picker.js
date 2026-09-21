// Keep the in-app labels German regardless of the embedded browser's language.
document.querySelectorAll('[data-file-picker]').forEach((button) => {
  const input = document.getElementById(button.dataset.filePicker);
  const label = document.getElementById(`${button.dataset.filePicker}-filename`);
  if (!input || !label) return;
  const refresh = () => { label.textContent = input.files.length ? input.files[0].name : 'Keine Datei ausgewählt'; };
  button.addEventListener('click', () => input.click());
  input.addEventListener('change', refresh);
  input.form?.addEventListener('reset', () => setTimeout(refresh, 0));
  refresh();
});

const btn = document.getElementById('parseBtn');

btn.addEventListener('click', () => {

  btn.disabled = true;

  btn.textContent = 'Ожидайте';

  btn.style.backgroundColor = '#e14242';

  btn.style.cursor = 'default';
  btn.style.opacity = '1';
});

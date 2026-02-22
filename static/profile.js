const chipContainer = document.getElementById('chipcontainer');

chipContainer.addEventListener('click', (e) => {
const el = e.target;
if (!el.classList.contains('chip')) return;
el.classList.toggle('selected');
updateSelectedChips();
});

function updateSelectedChips(){
const selectedValues = getSelectedValues();
console.log('selected values:', selectedValues);
}

function getSelectedChips(){
const selectedChips = chipContainer.getElementsByClassName('selected');
return Array.from(selectedChips).map(chip => ({
    value: chip.dataset.value,
    label: chip.textContent.trim()
}));
}

function getSelectedValues(){
return getSelectedChips().map(c => c.label);
}

function getSelectedIds(){
return getSelectedChips().map(c => {
    const v = c.value;
    return Number.isNaN(Number(v)) ? v : Number(v);
});
}

async function sendSelectedChips() {
const values = getSelectedValues();
const ids = getSelectedIds();
try {
    const res = await fetch('/save-chips', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ values, ids })
    });
    if (!res.ok) {
    console.error('server error', res.status);
    return;
    }
    try {
    const data = await res.json();
    console.log('server response', data);
    } catch {
    console.log('no JSON response, status', res.status);
    if (res.status === 303 && res.headers.get('location')) {
        window.location = res.headers.get('location');
    }
    }
} catch (err) {
    console.error('send failed', err);
}
}

document.querySelector('.savebtn').addEventListener('click', (e) => {
e.preventDefault();
sendSelectedChips();
});

async function sendSelectedChips() {
const values = getSelectedValues();
const ids = getSelectedIds();
try {
    const res = await fetch('/save-chips', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ values, ids })
    });
    if (!res.ok) throw new Error('Server error: ' + res.status);
    const data = await res.json();
    if (data.ok) {
    location.reload();
    } else {
    console.error('save failed', data);
    }
} catch (err) {
    console.error('send failed', err);
}
}
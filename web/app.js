const $ = id => document.getElementById(id);
const API = '';

let currentArchiveB64 = null;
let currentFilename = null;
let restoredB64 = null;

// --- Upload ---
const dropZone = $('dropZone');
const fileInput = $('fileInput');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('dragover'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));
dropZone.addEventListener('drop', e => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener('change', e => { if (e.target.files.length) handleFile(e.target.files[0]); });

function handleFile(file) {
    if (file.size > 20 * 1024 * 1024) {
        alert('File too large. Max 20 MB for demo.');
        return;
    }
    window.uploadedFile = file;
    $('fName').textContent = file.name;
    $('fSize').textContent = formatBytes(file.size);
    $('fileInfo').classList.remove('hidden');
    $('actionPanel').classList.remove('hidden');
    $('resultsPanel').classList.add('hidden');
    $('verifyPanel').classList.remove('hidden');
}

// --- Compress ---
$('compressBtn').addEventListener('click', async () => {
    const btn = $('compressBtn');
    const file = window.uploadedFile;
    if (!file) return;

    btn.disabled = true;
    $('compSpinner').classList.remove('hidden');

    const form = new FormData();
    form.append('file', file);

    try {
        const res = await fetch(`${API}/api/compress`, { method: 'POST', body: form });
        const data = await res.json();

        if (!data.success) {
            alert('Compression failed: ' + (data.error || 'Unknown error'));
            return;
        }

        showResults(data);
    } catch (err) {
        alert('Network error: ' + err.message);
    } finally {
        btn.disabled = false;
        $('compSpinner').classList.add('hidden');
    }
});

function showResults(data) {
    currentArchiveB64 = data.archive_b64;
    currentFilename = data.filename;

    $('resultsPanel').classList.remove('hidden');

    // Winner
    $('winnerName').textContent = data.winner_strategy;
    const saved = data.saved_pct;
    const savedEl = $('savedPct');
    savedEl.textContent = (saved >= 0 ? '-' : '+') + Math.abs(saved).toFixed(1) + '%';
    savedEl.style.color = saved >= 0 ? 'var(--success)' : 'var(--danger)';
    $('bigLabel').textContent = saved >= 0 ? 'space saved' : 'size increased';

    // Metrics
    $('origSize').textContent = data.original_size_human;
    $('compSize').textContent = data.compressed_size_human;
    $('compRatio').textContent = data.compression_ratio + 'x';
    $('compTime').textContent = data.elapsed_ms + ' ms';

    // Candidates table
    const tbody = $('candTable').querySelector('tbody');
    tbody.innerHTML = '';
    data.candidates.forEach(c => {
        const tr = document.createElement('tr');
        if (c.is_winner) tr.classList.add('winner');
        if (c.saved_pct < 0) tr.classList.add('negative');
        tr.innerHTML = `
            <td>${escapeHtml(c.label)}</td>
            <td>${c.size_human}</td>
            <td>${c.saved_pct >= 0 ? '-' : '+'}${Math.abs(c.saved_pct).toFixed(1)}%</td>
            <td>${c.is_winner ? '🏆 Winner' : (c.saved_pct < 0 ? 'Expanded' : 'Valid')}</td>
        `;
        tbody.appendChild(tr);
    });

    // Profile
    const pg = $('profileGrid');
    pg.innerHTML = '';
    const p = data.profile;
    const items = [
        ['Entropy', p.entropy],
        ['Byte Diversity', p.byte_diversity],
        ['Printable Ratio', (p.printable_ratio * 100).toFixed(1) + '%'],
        ['Run Ratio', (p.run_ratio * 100).toFixed(1) + '%'],
        ['Repetition', p.repetition_score.toFixed(2)],
        ['Signature', p.signature],
        ['Already Compressed', p.already_compressed ? 'Yes' : 'No'],
    ];
    items.forEach(([label, val]) => {
        const div = document.createElement('div');
        div.className = 'profile-item';
        div.innerHTML = `<label>${escapeHtml(label)}</label><span>${escapeHtml(String(val))}</span>`;
        pg.appendChild(div);
    });
}

// --- Download Compressed ---
$('dlCompBtn').addEventListener('click', () => {
    if (!currentArchiveB64) return;
    downloadFile(currentArchiveB64, currentFilename + '.zc');
});

// --- Verify / Decompress ---
const vDrop = $('verifyDropZone');
const vInput = $('verifyInput');

vDrop.addEventListener('click', () => vInput.click());
vDrop.addEventListener('dragover', e => { e.preventDefault(); vDrop.classList.add('dragover'); });
vDrop.addEventListener('dragleave', () => vDrop.classList.remove('dragover'));
vDrop.addEventListener('drop', e => {
    e.preventDefault();
    vDrop.classList.remove('dragover');
    if (e.dataTransfer.files.length) handleVerifyFile(e.dataTransfer.files[0]);
});
vInput.addEventListener('change', e => { if (e.target.files.length) handleVerifyFile(e.target.files[0]); });

function handleVerifyFile(file) {
    window.verifyFile = file;
    $('decompressBtn').classList.remove('hidden');
    $('verifyResult').classList.add('hidden');
}

$('decompressBtn').addEventListener('click', async () => {
    const btn = $('decompressBtn');
    const file = window.verifyFile;
    if (!file) return;

    btn.disabled = true;
    $('decSpinner').classList.remove('hidden');

    const form = new FormData();
    form.append('file', file);

    try {
        const res = await fetch(`${API}/api/decompress`, { method: 'POST', body: form });
        const data = await res.json();

        const badge = $('verifyBadge');
        const details = $('verifyDetails');

        if (data.success && data.verified) {
            badge.textContent = '✓ LOSSLESS VERIFIED';
            badge.className = 'verify-badge';
            restoredB64 = data.restored_b64;
            details.innerHTML = `
                CRC32: MATCH<br>
                SHA-256: MATCH<br>
                Size: ${data.restored_size_human} (expected)<br>
                Time: ${data.elapsed_ms} ms
            `;
            $('dlRestoredBtn').classList.remove('hidden');
        } else {
            badge.textContent = '✗ VERIFICATION FAILED';
            badge.className = 'verify-badge fail';
            details.textContent = data.error || 'Archive validation failed.';
            $('dlRestoredBtn').classList.add('hidden');
        }
        $('verifyResult').classList.remove('hidden');
    } catch (err) {
        alert('Network error: ' + err.message);
    } finally {
        btn.disabled = false;
        $('decSpinner').classList.add('hidden');
    }
});

$('dlRestoredBtn').addEventListener('click', () => {
    if (!restoredB64) return;
    downloadFile(restoredB64, currentFilename || 'restored.bin');
});

// --- Utilities ---
function formatBytes(b) {
    if (b === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(b) / Math.log(k));
    return parseFloat((b / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function downloadFile(b64, filename) {
    const blob = base64ToBlob(b64);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function base64ToBlob(b64) {
    const bin = atob(b64);
    const arr = new Uint8Array(bin.length);
    for (let i = 0; i < bin.length; i++) arr[i] = bin.charCodeAt(i);
    return new Blob([arr]);
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
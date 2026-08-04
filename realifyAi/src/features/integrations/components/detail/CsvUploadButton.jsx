import React, { useRef, useState } from 'react';

const MAX_BYTES = 5 * 1024 * 1024;

/** Human-readable size, so a rejected file says *why* it was too big. */
const formatBytes = (bytes) => {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
};

/**
 * Split one CSV line, honouring quoted fields.
 *
 * A plain `split(',')` breaks the moment a value contains a comma — which for a
 * product export ("Chair, oak") is the common case, not the edge case.
 */
const splitRow = (line) => {
  const out = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < line.length; i += 1) {
    const ch = line[i];
    if (ch === '"') {
      /* A doubled quote inside a quoted field is an escaped quote. */
      if (inQuotes && line[i + 1] === '"') { field += '"'; i += 1; }
      else inQuotes = !inQuotes;
    } else if (ch === ',' && !inQuotes) {
      out.push(field.trim());
      field = '';
    } else {
      field += ch;
    }
  }
  out.push(field.trim());
  return out;
};

const parseCsv = (text) => {
  const lines = text.split(/\r\n|\n|\r/).filter((l) => l.trim() !== '');
  if (lines.length === 0) return { error: 'That file is empty.' };

  const headers = splitRow(lines[0]).filter(Boolean);
  if (headers.length < 2) {
    return { error: 'No columns found — is this a comma-separated file?' };
  }
  return { headers, rows: lines.length - 1 };
};

/**
 * Upload a CSV instead of authorising a live connection.
 *
 * Genuinely functional client-side: it reads the file, validates it, parses the
 * header row and reports what it found. There is no upload endpoint to post to,
 * so it stops at "parsed and understood" and hands the result to `onParsed`.
 */
const CsvUploadButton = ({ connectorName, onParsed }) => {
  const inputRef = useRef(null);
  const [file, setFile] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);

  const reset = () => {
    setFile(null);
    setResult(null);
    setError('');
    /* Clear the input's value too, or picking the same file twice fires no
       change event and the button appears dead. */
    if (inputRef.current) inputRef.current.value = '';
  };

  const handleFile = (picked) => {
    if (!picked) return;
    reset();

    const isCsv =
      picked.type === 'text/csv' ||
      picked.type === 'application/vnd.ms-excel' ||
      /\.csv$/i.test(picked.name);

    if (!isCsv) {
      setError(`${picked.name} is not a .csv file.`);
      return;
    }
    if (picked.size > MAX_BYTES) {
      setError(`${formatBytes(picked.size)} is over the ${formatBytes(MAX_BYTES)} limit.`);
      return;
    }

    setFile(picked);
    setBusy(true);

    const reader = new FileReader();
    reader.onerror = () => {
      setBusy(false);
      setError('That file could not be read.');
    };
    reader.onload = () => {
      setBusy(false);
      const parsed = parseCsv(String(reader.result || ''));
      if (parsed.error) {
        setError(parsed.error);
        setFile(null);
        return;
      }
      setResult(parsed);
      onParsed?.({ name: picked.name, size: picked.size, ...parsed });
    };
    reader.readAsText(picked);
  };

  return (
    <div className="flex flex-col items-stretch sm:items-end gap-2 flex-shrink-0">
      <input
        ref={inputRef}
        type="file"
        accept=".csv,text/csv"
        className="hidden"
        onChange={(e) => handleFile(e.target.files?.[0])}
      />

      <button
        onClick={() => inputRef.current?.click()}
        disabled={busy}
        className="px-3.5 py-2 rounded-xl border border-gray-200 dark:border-slate-700 bg-white dark:bg-slate-900 text-[12.5px] font-bold text-gray-700 dark:text-slate-300 hover:bg-gray-50 dark:hover:bg-slate-800 transition-colors flex items-center justify-center gap-2 whitespace-nowrap disabled:opacity-60"
      >
        {busy ? (
          <><i className="fa-solid fa-circle-notch fa-spin text-[11px]" /> Reading…</>
        ) : (
          <><i className="fa-solid fa-file-arrow-up text-[11px]" /> Upload CSV</>
        )}
      </button>

      {error && (
        <p className="text-[11.5px] text-rose-600 dark:text-rose-400 flex items-start gap-1.5 max-w-[280px] text-left">
          <i className="fa-solid fa-circle-exclamation text-[10px] mt-[3px] flex-shrink-0" />
          <span>{error}</span>
        </p>
      )}

      {result && file && (
        <div className="rounded-xl border border-emerald-100 dark:border-emerald-900/40 bg-emerald-50/60 dark:bg-emerald-950/20 px-3 py-2 max-w-[280px] text-left">
          <p className="text-[11.5px] font-bold text-gray-900 dark:text-white flex items-center gap-1.5">
            <i className="fa-solid fa-circle-check text-[10px] text-emerald-500 flex-shrink-0" />
            <span className="truncate">{file.name}</span>
          </p>
          <p className="text-[11px] text-gray-600 dark:text-slate-400 mt-0.5">
            {result.rows.toLocaleString('en-US')} row{result.rows === 1 ? '' : 's'} ·{' '}
            {result.headers.length} columns · {formatBytes(file.size)}
          </p>
          <p className="text-[10.5px] text-gray-500 dark:text-slate-500 mt-1 leading-snug">
            {result.headers.slice(0, 4).join(', ')}
            {result.headers.length > 4 ? ` +${result.headers.length - 4} more` : ''}
          </p>
          <div className="flex items-center gap-3 mt-1.5">
            <button
              onClick={() => inputRef.current?.click()}
              className="text-[11px] font-bold text-indigo-600 dark:text-indigo-400 hover:text-indigo-700"
            >
              Replace
            </button>
            <button
              onClick={reset}
              className="text-[11px] font-bold text-gray-500 dark:text-slate-400 hover:text-gray-700 dark:hover:text-slate-200"
            >
              Remove
            </button>
          </div>
          <p className="text-[10px] text-gray-400 dark:text-slate-500 mt-1.5 leading-snug">
            Will import into {connectorName} on continue.
          </p>
        </div>
      )}
    </div>
  );
};

export default CsvUploadButton;

const run = $input.first().json;
// Prevent spreadsheet formula evaluation in text cells; prices remain numbers.
const safeText = value => /^[=+@\-\t\r\n]/.test(value) ? "'" + value : value;
return run.products.map(p => ({json: {...p, name: safeText(p.name)}}));

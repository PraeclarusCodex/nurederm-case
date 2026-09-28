const run = $('Compare snapshots').first().json;
const state = $getWorkflowStaticData('global');
state.previous = run.snapshot;
state.lastSuccessAt = run.timestamp;
return [{json: {success: true, timestamp: run.timestamp, products: run.products.length,
  changes: run.changes.length, note: 'Kalıcı durum yalnızca aktif zamanlanmış çalışmalarda saklanır.'}}];

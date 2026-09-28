const test = require('node:test');
const assert = require('node:assert/strict');
const {workflow, run, extract} = require('./helpers.cjs');
const page = (price = '$416.99', id = 31) => ({names:['Packard 255 G2'],prices:[price],reviews:['2'],links:[`/test-sites/e-commerce/static/product/${id}`]});
const refs = count => ({'Build page list': Array.from({length:count}, (_,i)=>({page:i+1})), 'Configuration':[{timestamp:'2026-09-28T07:00:00Z'}]});
test('Pagination discovers last page, including ellipsis', () => {
  const result = run('Build page list', [{data:'<div id="static-pagination"><a href="/test-sites/e-commerce/static/computers/laptops?page=2">2</a>…<a href="/test-sites/e-commerce/static/computers/laptops?page=20">20</a></div>'}]);
  assert.equal(result.length,20); assert.ok(result[19].url.endsWith('?page=20'));
});
test('Missing pagination and excessive pages fail closed', () => {
  assert.throws(()=>run('Build page list',[{data:'Maintenance'}]));
  assert.throws(()=>run('Build page list',[{data:'static-pagination <a href="/static/computers/laptops?page=201">'}]));
});
test('HTML selectors keep full title, prices and zero reviews', () => {
  const out = extract('<div class="thumbnail"><a class="title" title="Full &amp; long name" href="/test-sites/e-commerce/static/product/31">Short…</a><span itemprop="price">$416.99</span><span itemprop="reviewCount">0</span></div>');
  assert.equal(out.names[0],'Full & long name');assert.equal(out.reviews[0],'0');
});
test('First run reports all products as new, without updating state', () => {
  const state = {};
  const result = run('Compare snapshots',[page()],refs(1),state)[0];
  assert.equal(result.changes.length,1); assert.equal(result.changes[0].change,'new');
  assert.equal(typeof result.products[0].price,'number'); assert.equal(result.products[0].price,416.99);
  assert.deepEqual(state,{});
});
test('Unchanged second run sends no change notification', () => {
  const first = run('Compare snapshots',[page()],refs(1))[0];
  const second = run('Compare snapshots',[page()],refs(1),{previous:first.snapshot})[0];
  assert.equal(second.hasChanges,false);assert.equal(second.changes.length,0);
});
test('Price rises, falls and new products detected by URL', () => {
  const first = run('Compare snapshots',[page()],refs(1))[0];
  for (const price of ['$400.00','$500.00']) {
    const result = run('Compare snapshots',[page(price),page('$10.00',32)],refs(2),{previous:first.snapshot})[0];
    assert.equal(result.changes.length,2);assert.equal(result.changes[0].oldPrice,416.99);
    assert.equal(result.changes[0].change,'price_changed');assert.equal(result.changes[1].change,'new');
  }
});
test('Partial, empty, duplicate and malformed results fail', () => {
  for (const [pages,expected] of [[[page()],2], [[{names:[],prices:[],reviews:[],links:[]}],1], [[page(),page()],2], [[page('USD nope')],1], [[{...page(),reviews:[]}],1], [[{...page(),links:['https://evil.example/']}],1]]) {
    const state = {previous:{sentinel:{price:10}}};
    assert.throws(()=>run('Compare snapshots',pages,refs(expected),state));
    assert.deepEqual(state,{previous:{sentinel:{price:10}}});
  }
});
test('Thousands separator becomes numeric price', () => {
  assert.equal(run('Compare snapshots',[page('$1,234.56')],refs(1))[0].products[0].price,1234.56);
});
test('Live site prices without decimals remain valid', () => {
  assert.equal(run('Compare snapshots',[page('$399')],refs(1))[0].products[0].price,399);
});
test('CSV text cannot become a spreadsheet formula', () => {
  const result = run('CSV rows',[{products:[{name:'=HYPERLINK("evil")',price:10}]}]);
  assert.ok(result[0].name.startsWith("'="));assert.equal(result[0].price,10);
});
test('Commit changes baseline only in the final step', () => {
  const result = run('Compare snapshots',[page()],refs(1))[0];const state = {};
  run('Commit successful snapshot',[],{'Compare snapshots':[result]},state);
  assert.deepEqual(state.previous,result.snapshot);assert.equal(state.lastSuccessAt,result.timestamp);
});
test('Workflow graph has valid endpoints, daily schedule and error branches', () => {
  const names = new Set(workflow.nodes.map(n=>n.name));
  assert.equal(names.size,workflow.nodes.length);
  for (const [source,connections] of Object.entries(workflow.connections)) {
    assert.ok(names.has(source));for (const output of connections.main) for(const edge of output) assert.ok(names.has(edge.node));
  }
  for (const name of ['Discover pagination','Fetch every page','Build page list','Extract products','Compare snapshots','CSV rows','Create CSV','Table rows','Save price history','Verify saved rows','Notify changes','Commit successful snapshot']) {
    const node=workflow.nodes.find(n=>n.name===name);assert.equal(node.onError,'continueErrorOutput');
    assert.equal(workflow.connections[name].main[1][0].node,'Prepare failure alert');
  }
  assert.equal(workflow.connections['Notify failure'].main[0][0].node,'Mark execution failed');
  assert.equal(workflow.nodes.find(n=>n.type.endsWith('scheduleTrigger')).parameters.rule.interval[0].expression,'0 9 * * *');
  assert.equal(workflow.settings.timezone,'Europe/Istanbul');assert.equal(workflow.active,false);
});

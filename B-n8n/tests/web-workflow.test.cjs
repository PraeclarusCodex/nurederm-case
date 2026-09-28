const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const w = JSON.parse(fs.readFileSync(path.join(__dirname,'../workflow.json'),'utf8'));
const node = name => w.nodes.find(n=>n.name===name);
const product = {timestamp:'2026-09-28T07:00:00.000Z',name:'Laptop',price:416.99,reviews:2,url:'https://webscraper.io/test-sites/e-commerce/static/product/31',currency:'USD'};
function verify(rows){
  return new Function('$input','$',node('Verify saved rows').parameters.jsCode)(
    {all:()=>rows.map(json=>({json}))},()=>({first:()=>({json:{products:[product]}})}));
}
test('Web workflow has no disk node or output directory',()=>{
  assert.ok(!w.nodes.some(n=>n.type==='n8n-nodes-base.readWriteFile'));
  assert.ok(!node('Configuration').parameters.jsCode.includes('outputDir'));
  assert.equal(w.active,false);
});
test('Table preserves numeric types and requires a real table selection',()=>{
  const p=node('Save price history').parameters;
  assert.equal(p.operation,'insert');assert.equal(p.dataTableId.value,'');
  assert.equal(p.columns.schema.find(s=>s.id==='price').type,'number');
  assert.equal(p.columns.schema.find(s=>s.id==='reviews').type,'number');
  assert.equal(p.options.optimizeBulk,false);
});
test('Saved rows must match full snapshot and numeric types',()=>{
  assert.equal(verify([{...product,id:1}])[0].json.products.length,1);
  for(const rows of [[],[product,product],[{...product,price:'416.99'}],[{...product,url:'wrong'}],[{...product,timestamp:'wrong'}]])assert.throws(()=>verify(rows));
});
test('CSV follows verified storage and produces one notification input',()=>{
  for(const [a,b] of [['Compare snapshots','Table rows'],['Table rows','Save price history'],['Save price history','Verify saved rows'],['Verify saved rows','CSV rows'],['CSV rows','Create CSV'],['Create CSV','Any changes']]){
    assert.equal(w.connections[a].main[0][0].node,b);
  }
});
test('Every risky step retains failure routing and references exist',()=>{
  const names=new Set(w.nodes.map(n=>n.name));assert.equal(names.size,w.nodes.length);
  for(const [source,c] of Object.entries(w.connections)){
    assert.ok(names.has(source));for(const out of c.main)for(const e of out)assert.ok(names.has(e.node));
  }
  for(const n of w.nodes.filter(n=>n.onError==='continueErrorOutput')){
    assert.equal(w.connections[n.name].main[1][0].node,'Prepare failure alert');
  }
});

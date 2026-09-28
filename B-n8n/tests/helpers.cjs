const fs = require('node:fs');
const path = require('node:path');
const cheerio = require('cheerio');
const workflow = JSON.parse(fs.readFileSync(path.join(__dirname, '../workflow.json'), 'utf8'));
function run(name, input, references = {}, state = {}) {
  const node = workflow.nodes.find(n => n.name === name);
  const items = input.map(json => ({json}));
  const lookup = key => {
    if (!references[key]) throw Error('Missing reference: ' + key);
    const ref = references[key].map(json => ({json}));
    return {first: () => ref[0], all: () => ref};
  };
  return new Function('$input', '$', '$getWorkflowStaticData', '$execution', node.parameters.jsCode)(
    {first: () => items[0], all: () => items}, lookup, () => state, {id: 'test-123'}).map(item => item.json);
}
function extract(html) {
  const $ = cheerio.load(html);
  const values = workflow.nodes.find(n => n.name === 'Extract products').parameters.extractionValues.values;
  return Object.fromEntries(values.map(v => [v.key, $(v.cssSelector).toArray().map(el =>
    (v.returnValue === 'attribute' ? $(el).attr(v.attribute) ?? '' : $(el).text()).trim())]));
}
module.exports = {workflow, run, extract};

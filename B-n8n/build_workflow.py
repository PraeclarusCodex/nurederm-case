"""Code node kaynaklarından yeniden üretilebilir n8n workflow JSON."""
import json
from pathlib import Path
import uuid

BASE = Path(__file__).resolve().parent
nodes, connections = [], {}


def node(name, type_, parameters, x, y=0, version=1, error=False, **extra):
    data = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'nurederm/' + name)), name=name,
                type='n8n-nodes-base.' + type_, typeVersion=version, position=[x, y], parameters=parameters, **extra)
    if error:
        data['onError'] = 'continueErrorOutput'
    nodes.append(data)


def code(name, file, x, y=0):
    node(name, 'code', dict(jsCode=(BASE / 'code' / file).read_text(), mode='runOnceForAllItems'), x, y, 2, True)


def link(source, target, output=0):
    main = connections.setdefault(source, {'main': []})['main']
    while len(main) <= output:
        main.append([])
    main[output].append(dict(node=target, type='main', index=0))


node('Daily 09 Istanbul', 'scheduleTrigger', {'rule': {'interval': [{'field': 'cronExpression', 'expression': '0 9 * * *'}]}}, 0, version=1.2)
node('Manual preview', 'manualTrigger', {}, 0, 180)
node('Configuration', 'code', {'mode': 'runOnceForAllItems', 'jsCode': "return [{json: {timestamp: new Date().toISOString(), fromEmail: 'configure@example.invalid', toEmail: 'configure@example.invalid', outputDir: '/home/node/.n8n-files'}}];"}, 240, version=2)
http_options = {'response': {'response': {'responseFormat': 'text', 'outputPropertyName': 'data'}}, 'timeout': 20000}
node('Discover pagination', 'httpRequest', {'url': 'https://webscraper.io/test-sites/e-commerce/static/computers/laptops', 'options': http_options}, 480, version=4.2, error=True, retryOnFail=True, maxTries=3, waitBetweenTries=1000)
code('Build page list', 'pages.js', 720)
node('Fetch every page', 'httpRequest', {'url': '={{ $json.url }}', 'options': {**http_options, 'batching': {'batch': {'batchSize': 1, 'batchInterval': 250}}}}, 960, version=4.2, error=True, retryOnFail=True, maxTries=3, waitBetweenTries=1000)
values = [dict(key='names', cssSelector='.thumbnail a.title', returnValue='attribute', attribute='title', returnArray=True),
          dict(key='prices', cssSelector='.thumbnail [itemprop="price"]', returnValue='text', returnArray=True),
          dict(key='reviews', cssSelector='.thumbnail [itemprop="reviewCount"]', returnValue='text', returnArray=True),
          dict(key='links', cssSelector='.thumbnail a.title', returnValue='attribute', attribute='href', returnArray=True)]
node('Extract products', 'html', {'operation': 'extractHtmlContent', 'sourceData': 'json', 'dataPropertyName': 'data', 'extractionValues': {'values': values}, 'options': {'trimValues': True, 'cleanUpText': True}}, 1200, version=1.2, error=True)
code('Compare snapshots', 'compare.js', 1440)
code('CSV rows', 'rows.js', 1680)
node('Create CSV', 'convertToFile', {'operation': 'csv', 'binaryPropertyName': 'data', 'options': {'headerRow': True, 'fileName': 'laptops.csv'}}, 1920, version=1.1, error=True)
node('Archive dated CSV', 'readWriteFile', {'operation': 'write', 'fileName': "={{ $('Configuration').first().json.outputDir + '/laptops-' + $execution.id + '.csv' }}", 'dataPropertyName': 'data', 'options': {'append': False}}, 2160, error=True)
node('Any changes', 'if', {'conditions': {'options': {'caseSensitive': True, 'leftValue': '', 'typeValidation': 'strict', 'version': 2}, 'conditions': [{'id': 'has-changes', 'leftValue': "={{ $('Compare snapshots').first().json.hasChanges }}", 'rightValue': '', 'operator': {'type': 'boolean', 'operation': 'true', 'singleValue': True}}], 'combinator': 'and'}, 'options': {}}, 2400, version=2.2)
email_base = {'fromEmail': "={{ $('Configuration').first().json.fromEmail }}", 'toEmail': "={{ $('Configuration').first().json.toEmail }}", 'emailFormat': 'text', 'options': {'appendAttribution': False}}
node('Notify changes', 'emailSend', {**email_base, 'subject': "={{ $('Compare snapshots').first().json.subject }}", 'text': "={{ $('Compare snapshots').first().json.text }}"}, 2640, -80, 2.1, True)
code('Commit successful snapshot', 'commit.js', 2880)
node('Prepare failure alert', 'code', {'mode': 'runOnceForAllItems', 'jsCode': "const errors = $input.all().map(i => i.json.error?.message || i.json.error || i.json.message || 'Bilinmeyen hata'); return [{json:{subject:'HATA: Laptop fiyat takibi tamamlanamadı', text: 'Çalışma: ' + $execution.id + '\\nÖnceki başarılı durum korunuyor.\\n' + errors.map(String).join('\\n').slice(0, 3000)}}];"}, 1440, 480, 2)
node('Notify failure', 'emailSend', {**email_base, 'subject': '={{ $json.subject }}', 'text': '={{ $json.text }}'}, 1680, 480, 2.1)
node('Mark execution failed', 'stopAndError', {'errorType': 'errorMessage', 'errorMessage': 'Fiyat takibi başarısız; önceki başarılı durum güncellenmedi.'}, 1920, 480)
node('Setup and provenance', 'stickyNote', {'content': '## FiyatRadar — günlük laptop takibi\nBaşlangıç şablonu: Track changes of product prices (#837)\nhttps://n8n.io/workflows/837-track-changes-of-product-prices/\n\n1. Configuration: e-posta adreslerini değiştir.\n2. Her iki Email düğümüne SMTP credential seç.\n3. CSV dizinini oluştur, kalıcı volume bağla ve yazma izni ver.\n4. Aktif/published akışı günde 09:00 Europe/Istanbul çalıştır.\n\nCSV: her çalışmada tüm ürünler + ISO tarih; karşılaştırma: son başarılı static data.\nManuel test static data saklamaz. İlk çalışmada tüm ürünler YENİ.\nHata çıkışları → bildirim → Stop And Error.\nCanlı SMTP ve n8n yürütme bu teslimde doğrulanmamıştır.', 'height': 430, 'width': 610}, 0, 430)
chain = ['Configuration', 'Discover pagination', 'Build page list', 'Fetch every page', 'Extract products', 'Compare snapshots', 'CSV rows', 'Create CSV', 'Archive dated CSV', 'Any changes']
link('Daily 09 Istanbul', 'Configuration'); link('Manual preview', 'Configuration')
for a, b in zip(chain, chain[1:]): link(a, b)
link('Any changes', 'Notify changes', 0); link('Any changes', 'Commit successful snapshot', 1)
link('Notify changes', 'Commit successful snapshot')
for n in nodes:
    if n.get('onError') == 'continueErrorOutput': link(n['name'], 'Prepare failure alert', 1)
link('Prepare failure alert', 'Notify failure'); link('Notify failure', 'Mark execution failed')
workflow = dict(name='FiyatRadar | Günlük Laptop Fiyat Takibi (disk sürümü)', nodes=nodes, connections=connections, active=False,
                settings={'executionOrder': 'v1', 'timezone': 'Europe/Istanbul', 'executionTimeout': 900},
                pinData={}, tags=[])
(BASE / 'workflow-local.json').write_text(json.dumps(workflow, ensure_ascii=False, indent=2) + '\n')
print(f'workflow-local.json: {len(nodes)} nodes')

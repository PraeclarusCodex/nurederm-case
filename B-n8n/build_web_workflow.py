"""Dosya sistemi erişimi gerektirmeyen Data Table varyantını üretir."""
import json
from pathlib import Path
import uuid

base = Path(__file__).resolve().parent
w = json.loads((base / 'workflow-local.json').read_text())
w['name'] = 'FiyatRadar | Günlük Laptop Fiyat Takibi'
w['nodes'] = [n for n in w['nodes'] if n['name'] != 'Archive dated CSV']
nodes = {n['name']: n for n in w['nodes']}
nodes['Configuration']['parameters']['jsCode'] = "return [{json: {timestamp: new Date().toISOString(), fromEmail: 'configure@example.invalid', toEmail: 'configure@example.invalid'}}];"

def add(name, type_, parameters, position, version=2):
    n = dict(id=str(uuid.uuid5(uuid.NAMESPACE_URL, 'nurederm-web/' + name)), name=name,
             type='n8n-nodes-base.'+type_, typeVersion=version, position=position,
             parameters=parameters, onError='continueErrorOutput')
    w['nodes'].append(n)

add('Table rows', 'code', {'mode':'runOnceForAllItems', 'jsCode':"return $input.first().json.products.map(p => ({json: {...p}}));"}, [1680, 0])
fields = [('timestamp','string'),('name','string'),('price','number'),('reviews','number'),('url','string'),('currency','string')]
add('Save price history', 'dataTable', {
    'resource':'row', 'operation':'insert', 'dataTableId':{'__rl':True,'value':'','mode':'list'},
    'columns': {'mappingMode':'autoMapInputData', 'value':{},
                'schema':[dict(id=k,displayName=k,required=False,defaultMatch=False,display=True,type=t,canBeUsedToMatch=True) for k,t in fields],
                'matchingColumns':[], 'attemptToConvertTypes':False, 'convertFieldsToString':False},
    'options':{'optimizeBulk':False}}, [1920,0], 1)
verify = """const run = $('Compare snapshots').first().json;
const rows = $input.all().map(i => i.json);
if (rows.length !== run.products.length) throw new Error('Tabloya eksik kayıt: önceki başarılı durum korunuyor.');
const expected = new Map(run.products.map(p => [p.url, p]));
const seen = new Set();
for (const row of rows) {
  const p = expected.get(row.url);
  if (!p || seen.has(row.url) || ['timestamp','name','price','reviews','currency'].some(k => row[k] !== p[k])) {
    throw new Error('Tablo yazım sonucu doğrulanamadı; sütun türlerini ve eşlemeyi kontrol edin.');
  }
  seen.add(row.url);
}
return [{json:run}];
"""
add('Verify saved rows', 'code', {'mode':'runOnceForAllItems','jsCode':verify}, [2160,0])
for name,x in [('CSV rows',2400),('Create CSV',2640),('Any changes',2880),('Notify changes',3120),('Commit successful snapshot',3360)]:
    nodes[name]['position'][0]=x
nodes['Setup and provenance']['parameters']['content'] = '''## FiyatRadar — Data Table kaydı
Şablon: Track changes of product prices (#837)
https://n8n.io/workflows/837-track-changes-of-product-prices/

1. Aynı projede fiyatradar_price_history tablosunu oluştur.
2. Sütunlar: timestamp (String), name (String), price (Number), reviews (Number), url (String), currency (String).
3. Save price history düğümünde tabloyu seç ve alan eşlemelerini kontrol et.
4. Configuration e-posta adresleri + iki Email düğümünde SMTP hesabını ayarla.

Günlük kalıcı kayıt: Data Table. CSV: isteğe bağlı indirme çıktısı.
Klasör, SSH veya sunucu dosya sistemi erişimi gerekmez.
Karşılaştırma: son başarılı aktif çalışmanın static data kaydı.
Manuel çalışmada static data kalıcılığı bekleme.
Tablo kayıtları tarihli geçmiş içerir; tekrar çalıştırma yeni satırlar ekler.
Data Table, SMTP ve zamanlanmış karşılaştırma canlı doğrulandı (28.09.2026).
Yeni ortamda tablo ve SMTP bağlantılarını yeniden seçin.'''
connections={}
def link(a,b,output=0):
    main=connections.setdefault(a,{'main':[]})['main']
    while len(main)<=output:main.append([])
    main[output].append({'node':b,'type':'main','index':0})
chain=['Configuration','Discover pagination','Build page list','Fetch every page','Extract products','Compare snapshots','Table rows','Save price history','Verify saved rows','CSV rows','Create CSV','Any changes']
link('Daily 09 Istanbul','Configuration');link('Manual preview','Configuration')
for a,b in zip(chain,chain[1:]):link(a,b)
link('Any changes','Notify changes');link('Any changes','Commit successful snapshot',1)
link('Notify changes','Commit successful snapshot')
for n in w['nodes']:
    if n.get('onError')=='continueErrorOutput':link(n['name'],'Prepare failure alert',1)
link('Prepare failure alert','Notify failure');link('Notify failure','Mark execution failed')
w['connections']=connections
(base/'workflow.json').write_text(json.dumps(w,ensure_ascii=False,indent=2)+'\n')

import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import Api, ApiFailure, classify, order_ids, process, render_summary, validate_messages


class Stub:
    def __init__(self, cart=None, error=False):
        self.value, self.error, self.calls = cart, error, []

    def cart(self, number):
        self.calls.append(number)
        if self.error:
            raise ApiFailure('API bağlantı/zaman aşımı hatası')
        return self.value


def message(text='5 numaralı siparişim nerede?', customer=5):
    return dict(id=1, kanal='whatsapp', musteri_id=customer, mesaj=text)


class MessageTests(unittest.TestCase):
    def setUp(self):
        self.cart = dict(id=5, userId=5, products=[dict(title='Test serum', quantity=2)], total=123.45)

    def test_all_supplied_topics(self):
        data = json.loads((Path(__file__).resolve().parents[1] / 'mesajlar.json').read_text())
        expected = ['siparis-durumu'] * 3 + ['istenmeyen-etki', 'iade-sikayet', 'siparis-durumu', 'diger', 'siparis-durumu', 'urun-sorusu', 'fiyat', 'urun-sorusu', 'siparis-durumu', 'urun-sorusu', 'fiyat', 'urun-sorusu']
        self.assertEqual([classify(m['mesaj']) for m in data], expected)

    def test_sensitive_precedes_order_and_price(self):
        for text in ['5 numaralı siparişimdeki krem yüzümü yaktı, kızardı; fiyatı ne?', 'iade etmek istiyorum 5 numaralı siparişi']:
            api = Stub(self.cart)
            r = process(message(text), api)
            self.assertTrue(r['devret'])
            self.assertEqual(api.calls, [])
            self.assertEqual(r['cevap_taslagi'], 'Mesajınızı değerlendirmesi için müşteri temsilcimize yönlendiriyorum.')

    def test_foreign_order_never_leaks(self):
        self.cart.update(userId=99, total=987654.32, products=[dict(title='SECRET_PRODUCT', quantity=1)])
        r = process(message(), Stub(self.cart))
        self.assertTrue(r['devret'])
        for secret in ['SECRET_PRODUCT', '987654', '99']:
            self.assertNotIn(secret, json.dumps(r))

    def test_owner_checked_before_products(self):
        r = process(message(), Stub(dict(userId=99, products=None)))
        self.assertIn('Sahiplik', r['not'])

    def test_matching_owner(self):
        r = process(message(), Stub(self.cart))
        self.assertFalse(r['devret'])
        self.assertIn('Test serum × 2', r['cevap_taslagi'])
        self.assertIn('123.45', r['cevap_taslagi'])
        self.assertIn('teslim tarihi sağlamıyor', r['cevap_taslagi'])
        self.assertEqual(set(r), {'id', 'konu', 'devret', 'cevap_taslagi', 'not'})

    def test_not_found(self):
        r = process(message(), Stub())
        self.assertTrue(r['devret'])
        self.assertIn('bulunamadı', r['cevap_taslagi'])

    def test_outage(self):
        r = process(message(), Stub(error=True))
        self.assertTrue(r['devret'])
        self.assertIn('şu anda', r['cevap_taslagi'])

    def test_missing_ambiguous_numbers(self):
        for text in ['Siparişim nerede?', 'Sipariş #5 ve #6 nerede?', 'Siparişim 200 ml krem, fiyat 500 TL']:
            api = Stub(self.cart)
            self.assertTrue(process(message(text), api)['devret'])
            self.assertEqual(api.calls, [])

    def test_extract_english_and_turkish(self):
        for text in ['order #5', 'sipariş no: 5', '5 numaralı siparişim', 'order number 5']:
            self.assertEqual(order_ids(text), [5])

    def test_mixed_intent(self):
        r = process(message('Krem fiyatı ne? 5 numaralı siparişim ne zaman gelir?'), Stub(self.cart))
        self.assertEqual(r['konu'], 'siparis-durumu')
        self.assertIn('fiyatı sorunuz', r['cevap_taslagi'])

    def test_english_reply(self):
        r = process(message('Hi, where is my order #5?'), Stub(self.cart))
        self.assertIn('Order #5', r['cevap_taslagi'])

    def test_invalid_api_fields(self):
        for key, value in [('userId', True), ('userId', '5'), ('total', 'NaN'), ('total', -10), ('total', True), ('products', []), ('products', [None]), ('products', [dict(title='X', quantity=True)]), ('id', 6)]:
            cart = copy.deepcopy(self.cart)
            cart[key] = value
            self.assertTrue(process(message(), Stub(cart))['devret'], (key, value))

    def test_html_injection_is_escaped(self):
        m = message('<script>alert(1)</script> krem fiyatı?')
        r = process(m, Stub())
        page = render_summary([m], [r], 'now')
        self.assertNotIn('<script>alert(1)</script>', page)
        self.assertIn('&lt;script&gt;', page)

    def test_invalid_input(self):
        for data in [None, [{}], [message(), message()], [message(customer=True)], [message('')]]:
            with self.assertRaises(ValueError):
                validate_messages(data)

    @patch('main.time.sleep')
    @patch('main.urlopen')
    def test_http_404_does_not_retry(self, urlopen, sleep):
        urlopen.side_effect = HTTPError('url', 404, 'not found', {}, None)
        api = Api()
        self.assertIsNone(api.cart(5))
        self.assertIsNone(api.cart(5))
        self.assertEqual(urlopen.call_count, 1)

    @patch('main.time.sleep')
    @patch('main.urlopen')
    def test_network_retry_bounded(self, urlopen, sleep):
        urlopen.side_effect = URLError('timeout')
        with self.assertRaises(ApiFailure):
            Api().cart(5)
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)


if __name__ == '__main__':
    unittest.main()

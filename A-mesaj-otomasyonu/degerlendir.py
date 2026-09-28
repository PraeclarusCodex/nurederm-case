"""Konu sınıflandırmasını verilen 15 mesaj dışındaki etiketli setlerle ölçer."""
from collections import Counter
import json
from pathlib import Path

from main import BASE, TOPICS, classify


def evaluate(path):
    data = json.loads(path.read_text(encoding='utf-8'))
    misses = [(x['beklenen'], classify(x['mesaj']), x['mesaj']) for x in data if classify(x['mesaj']) != x['beklenen']]
    return data, misses


def main():
    for path in sorted((BASE / 'degerlendirme').glob('*.json')):
        data, misses = evaluate(path)
        total = Counter(x['beklenen'] for x in data)
        missed = Counter(expected for expected, _, _ in misses)
        print(f'{path.name}: {len(data) - len(misses)}/{len(data)} doğru')
        for topic in TOPICS:
            if total[topic]:
                print(f'  {topic:<16} {total[topic] - missed[topic]}/{total[topic]}')
        for expected, got, text in misses:
            print(f'  HATA  beklenen={expected} bulunan={got} | {text}')


if __name__ == '__main__':
    main()

import 'package:brujula_finance_sample/finance_review.dart';
import 'package:test/test.dart';

Json row(String id, {String ref = '', int amount = -250, int? sourceRow}) => {
  'id': id,
  'accountId': 'demo-bank',
  'date': '2026-01-12',
  'amountCents': amount,
  'currency': 'EUR',
  'description': 'Coffee',
  'reference': ref,
  if (sourceRow != null) 'sourceRow': sourceRow,
};

void main() {
  for (final input in [
    '12-3',
    'E U R 12',
    '--12',
    '-12-',
    '(12)-',
    '(+12)',
    '1+2',
    '12+',
    '1,23,456',
    '12.34,56',
    '12,34.56',
    '1 2',
    '',
    ' ',
    '1,',
    '.50',
    'NaN',
    'EUR USD 12',
    '1EUR2',
    '((12))',
    '12..00',
  ]) {
    test('reject malformed original amount: "$input"', () {
      expect(() => moneyCents(input), throwsFormatException);
    });
  }
  test('one old reference cannot settle two incoming rows', () {
    final matches = reviewImport(
      [row('a', ref: 'R'), row('b', ref: 'R')],
      [row('old', ref: 'R')],
      'new',
    );
    expect(matches.map((r) => r.match), everyElement(ImportMatch.conflict));
  });
  test(
    'multiple existing reference candidates require review in either order',
    () {
      final old = [row('a', ref: 'R'), row('b', ref: 'R', amount: -350)];
      for (final candidates in [old, old.reversed.toList()]) {
        expect(
          reviewImport([row('new', ref: 'R')], candidates, 'new').single.match,
          ImportMatch.conflict,
        );
      }
    },
  );
  test('missing source row is not a strong provenance match', () {
    expect(
      reviewImport(
        [row('new', amount: -600)],
        [
          {...row('old'), 'documentId': 'doc'},
        ],
        'doc',
      ).single.match,
      ImportMatch.fresh,
    );
  });
  test(
    'same id with another reference cannot silently insert a new record',
    () {
      expect(
        reviewImport(
          [row('a', ref: 'B')],
          [row('a', ref: 'A')],
          'doc',
        ).single.match,
        ImportMatch.conflict,
      );
    },
  );
  test('duplicate existing ids fail explicitly', () {
    expect(
      () => reviewImport([row('new')], [row('a'), row('a')], 'doc'),
      throwsFormatException,
    );
  });
}

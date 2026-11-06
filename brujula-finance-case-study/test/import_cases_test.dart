import 'package:brujula_finance_sample/finance_review.dart';
import 'package:test/test.dart';

Json row(String id, {String ref = '', int? sourceRow}) => {
  'id': id,
  'accountId': 'demo',
  'date': '2026-01-01',
  'amountCents': -250,
  'currency': 'EUR',
  'description': 'Coffee',
  'reference': ref,
  if (sourceRow != null) 'sourceRow': sourceRow,
};
void main() {
  for (final change in <Json>[
    {'id': ''},
    {'accountId': null},
    {'date': null},
    {'currency': ''},
    {'amountCents': 9007199254740992},
  ]) {
    test('incomplete identity or unsafe source data $change', () {
      expect(
        () => reviewImport(
          [
            {...row('a'), ...change},
          ],
          [],
          'doc',
        ),
        throwsFormatException,
      );
    });
  }
  test('account and reference delimiters cannot collide across accounts', () {
    final result = reviewImport(
      [
        {...row('a', ref: 'c'), 'accountId': 'a|b'},
        {...row('b', ref: 'b|c'), 'accountId': 'a'},
      ],
      [],
      'doc',
    );
    expect(result.map((r) => r.match), everyElement(ImportMatch.fresh));
  });
  final formats = {
    '-12.34': -1234,
    '12.34-': -1234,
    '−12,34': -1234,
    '(12,34)': -1234,
    '(EUR 1.234,56)': -123456,
    '+12.34': 1234,
    '€-12,34': -1234,
    '-€12,34': -1234,
    '1,234.56 USD': 123456,
    '1 234,56': 123456,
    '1\u00a0234,56': 123456,
    '1.234': 123400,
    '1,234,567': 123456700,
    '90071992547409.91': 9007199254740991,
  };
  for (final entry in formats.entries) {
    test(
      'supported original format ${entry.key}',
      () => expect(moneyCents(entry.key), entry.value),
    );
  }
  for (final input in [
    '90071992547409.92',
    '99999999999999999999999999999999999',
    '(12',
    '12)',
    '1,2,3',
    '1.234.56',
    '1e3',
    '12 EUR EUR',
  ]) {
    test(
      'reject invalid or unsafe format $input',
      () => expect(() => moneyCents(input), throwsFormatException),
    );
  }
  test('same-file source repetition is detected even without a reference', () {
    final result = reviewImport(
      [row('a', sourceRow: 1), row('b', sourceRow: 1)],
      [],
      'doc',
    );
    expect(result.map((r) => r.match), [
      ImportMatch.fresh,
      ImportMatch.duplicate,
    ]);
  });
  test('same-file unreferenced purchases preserve multiplicity', () {
    expect(
      reviewImport(
        [row('a', sourceRow: 1), row('b', sourceRow: 2)],
        [],
        'doc',
      ).map((r) => r.match),
      everyElement(ImportMatch.fresh),
    );
  });
  test('source-row candidates are consumed once even with distinct bank references', () {
    final old = {...row('old', sourceRow: 1), 'documentId': 'doc'};
    final result = reviewImport(
      [row('a', ref: 'A', sourceRow: 1), row('b', ref: 'B', sourceRow: 1)],
      [old],
      'doc',
    );
    expect(result.map((r) => r.match), [
      ImportMatch.duplicate,
      ImportMatch.conflict,
    ]);
  });
  test('ambiguous similarity is deterministic across existing input order', () {
    final old = [row('b'), row('a')];
    for (final candidates in [old, old.reversed.toList()]) {
      final result = reviewImport(
        [row('x'), row('y'), row('z')],
        candidates,
        'doc',
      );
      expect(result.map((r) => r.match), [
        ImportMatch.possible,
        ImportMatch.possible,
        ImportMatch.fresh,
      ]);
      expect(result.first.existing!['id'], 'a');
    }
  });
  test('incoming ID collision is explicit even across accounts', () {
    expect(
      reviewImport(
        [row('a')],
        [
          {...row('a'), 'accountId': 'other'},
        ],
        'doc',
      ).single.match,
      ImportMatch.conflict,
    );
  });
  test('repeated incoming IDs are never staged as two new records', () {
    expect(
      reviewImport([row('a'), row('a')], [], 'doc').map((r) => r.match),
      everyElement(ImportMatch.conflict),
    );
  });
}

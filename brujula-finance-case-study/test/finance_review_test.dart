import 'package:test/test.dart';
import 'package:brujula_finance_sample/finance_review.dart';

Json row(
  String id, {
  String ref = '',
  int amount = -250,
  String date = '2026-01-12',
  String currency = 'EUR',
}) => {
  'id': id,
  'accountId': 'demo-bank',
  'date': date,
  'amountCents': amount,
  'currency': currency,
  'description': 'Coffee',
  'reference': ref,
  'sourceRow': id,
  'sourceTable': 'synthetic-table',
};

void main() {
  test('locale and negative formats have hand-calculated integer cents', () {
    expect(moneyCents('1.234,56 EUR'), 123456);
    expect(moneyCents('1,234.56 USD'), 123456);
    expect(moneyCents('(2,50)'), -250);
    expect(moneyCents('2.50-'), -250);
  });
  test('sub-cent ambiguity and unsafe amounts are rejected', () {
    expect(() => moneyCents('1,2345'), throwsFormatException);
    expect(() => moneyCents('90071992547410.00'), throwsFormatException);
  });
  test('same reference and financial values is a duplicate', () {
    expect(
      reviewImport(
        [row('new', ref: 'A')],
        [row('old', ref: 'A')],
        'new-doc',
      ).single.match,
      ImportMatch.duplicate,
    );
  });
  test('same reference but altered amount is a conflict', () {
    expect(
      reviewImport(
        [row('new', ref: 'A', amount: -300)],
        [row('old', ref: 'A')],
        'new-doc',
      ).single.match,
      ImportMatch.conflict,
    );
  });
  test('same reference but altered date or currency is a conflict', () {
    for (final change in [
      row('new', ref: 'A', date: '2026-01-13'),
      row('new', ref: 'A', currency: 'USD'),
    ]) {
      expect(
        reviewImport([change], [row('old', ref: 'A')], 'new-doc').single.match,
        ImportMatch.conflict,
      );
    }
  });
  test('identical legitimate purchases with distinct references survive', () {
    expect(
      reviewImport(
        [row('new', ref: 'B')],
        [row('old', ref: 'A')],
        'new-doc',
      ).single.match,
      ImportMatch.fresh,
    );
  });
  test('no-reference overlap asks for review, not automatic deletion', () {
    expect(
      reviewImport([row('new')], [row('old')], 'new-doc').single.match,
      ImportMatch.possible,
    );
  });
  test('one previous match cannot consume two legitimate occurrences', () {
    expect(
      reviewImport(
        [row('new-1'), row('new-2')],
        [row('old')],
        'new-doc',
      ).map((r) => r.match),
      [ImportMatch.possible, ImportMatch.fresh],
    );
  });
  test('two no-reference purchases in a new file remain two records', () {
    expect(
      reviewImport(
        [row('line-1'), row('line-2')],
        [],
        'new-doc',
      ).map((r) => r.match),
      [ImportMatch.fresh, ImportMatch.fresh],
    );
  });
  test('original file, table and row identify reimports', () {
    final incoming = {...row('new'), 'sourceRow': 2, 'sourceTable': 'main'};
    final old = {
      ...row('old'),
      'sourceRow': 2,
      'sourceTable': 'main',
      'documentId': 'same-doc',
    };
    expect(
      reviewImport([incoming], [old], 'same-doc').single.match,
      ImportMatch.duplicate,
    );
    incoming['sourceTable'] = 'other';
    expect(
      reviewImport([incoming], [old], 'same-doc').single.match,
      ImportMatch.possible,
    );
  });
  test('account identity and deleted entries keep scopes separate', () {
    final old = {...row('old', ref: 'A'), 'accountId': 'another-bank'};
    expect(
      reviewImport([row('new', ref: 'A')], [old], 'new-doc').single.match,
      ImportMatch.fresh,
    );
    old['accountId'] = 'demo-bank';
    old['deleted'] = true;
    expect(
      reviewImport([row('new', ref: 'A')], [old], 'new-doc').single.match,
      ImportMatch.fresh,
    );
  });
  test('changed classification preserves source financial identity', () {
    final original = row('old', ref: 'A');
    final edited = {
      ...original,
      'description': 'Edited label',
      'statementData': {...original},
    };
    expect(
      reviewImport([row('new', ref: 'A')], [edited], 'new-doc').single.match,
      ImportMatch.duplicate,
    );
  });
}

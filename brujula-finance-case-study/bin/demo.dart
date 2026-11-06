import 'dart:convert';

import 'package:brujula_finance_sample/finance_review.dart';

Json row(String id, String description, String amount, String reference) => {
  'id': id,
  'accountId': 'demo-bank',
  'date': '2026-01-12',
  'currency': 'EUR',
  'amountCents': moneyCents(amount),
  'description': description,
  'reference': reference,
  'sourceRow': id,
  'sourceTable': 'synthetic-table',
};

void main() {
  final existing = [
    row('saved-a', 'Bookshop', '-18,50', 'DEMO-A'),
    row('saved-b', 'Coffee', '-2,50', ''),
    row('saved-c', 'Train', '-15,00', 'DEMO-C'),
  ];
  final incoming = [
    row('new-a', 'Groceries', '-31,20', 'DEMO-N'),
    row('new-b', 'Bookshop', '-18,50', 'DEMO-A'),
    row('new-c', 'Coffee', '-2,50', ''),
    row('new-d', 'Train', '-16,00', 'DEMO-C'),
  ];
  final result = reviewImport(incoming, existing, 'synthetic-statement');
  final outcomes = result.map((r) => r.match.name).join(',');
  if (outcomes != 'fresh,duplicate,possible,conflict') {
    throw StateError('Unexpected import review: $outcomes');
  }
  print(
    const JsonEncoder.withIndent('  ').convert({
      'data': 'Synthetic demo data',
      'rows': [
        for (final r in result)
          {
            'description': r.transaction['description'],
            'amountCents': r.transaction['amountCents'],
            'status': r.match.name,
            'reason': r.reason,
          },
      ],
    }),
  );
}

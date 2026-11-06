// Selected logic extracted from Brújula; see docs/PROVENANCE.md.
// Copyright 2026 Martin Calpe Blasco. All rights reserved.
typedef Json = Map<String, dynamic>;

int moneyCents(String input) {
  var value = input
      .trim()
      .replaceAll(RegExp(r'[€$£\s\u00a0]'), '')
      .replaceAll(RegExp('EUR|USD|GBP', caseSensitive: false), '')
      .replaceAll('−', '-');
  final negative =
      value.startsWith('-') ||
      (value.startsWith('(') && value.endsWith(')')) ||
      value.endsWith('-');
  value = value.replaceAll(RegExp(r'[()+-]'), '');
  final comma = value.lastIndexOf(',');
  final dot = value.lastIndexOf('.');
  String whole, fraction;
  if (comma >= 0 && dot >= 0) {
    final decimal = comma > dot ? ',' : '.';
    final parts = value.split(decimal);
    fraction = parts.removeLast();
    whole = parts.join().replaceAll(RegExp('[.,]'), '');
  } else if (comma >= 0 || dot >= 0) {
    final parts = value.split(comma >= 0 ? ',' : '.');
    if (parts.length == 2 && parts.last.length <= 2) {
      whole = parts.first;
      fraction = parts.last;
    } else if (parts.skip(1).every((p) => p.length == 3)) {
      whole = parts.join();
      fraction = '';
    } else {
      throw const FormatException('Importe ambiguo. Usa 1.234,56 o 1234.56.');
    }
  } else {
    whole = value;
    fraction = '';
  }
  if (!RegExp(r'^\d+$').hasMatch(whole) ||
      !RegExp(r'^\d{0,2}$').hasMatch(fraction)) {
    throw const FormatException(
      'Introduce un importe válido, con un máximo de dos decimales.',
    );
  }
  final result = int.parse(whole) * 100 + int.parse(fraction.padRight(2, '0'));
  if (result > 9007199254740991) {
    throw const FormatException('Importe demasiado grande.');
  }
  return negative ? -result : result;
}

String normalize(String value) {
  const accents = 'áàäâéèëêíìïîóòöôúùüûñç';
  const plain = 'aaaaeeeeiiiioooouuuunc';
  var result = value.toLowerCase().trim();
  for (var i = 0; i < accents.length; i++) {
    result = result.replaceAll(accents[i], plain[i]);
  }
  return result;
}

enum ImportMatch { fresh, duplicate, possible, conflict }

class ReviewedImportRow {
  final int index;
  final Json transaction;
  final ImportMatch match;
  final String reason;
  final Json? existing;
  ReviewedImportRow(
    this.index,
    this.transaction,
    this.match,
    this.reason, [
    this.existing,
  ]);
}

Json _original(Json t) => t['statementData'] is Map
    ? Map<String, dynamic>.from(t['statementData'])
    : t;

bool _sameMoney(Json a, Json b) =>
    a['date'] == b['date'] &&
    a['amountCents'] == b['amountCents'] &&
    a['currency'] == b['currency'];

/// A matching amount is evidence to review, never proof of a duplicate.
/// Consume candidates one by one so repeated purchases retain their multiplicity.
List<ReviewedImportRow> reviewImport(
  List<Json> incoming,
  List<Json> existing,
  String documentId,
) {
  final pool = existing.where((t) => t['deleted'] != true).toList();
  final consumed = <String>{};
  final staged = <Json>[];
  final result = <ReviewedImportRow>[];
  for (var i = 0; i < incoming.length; i++) {
    final t = incoming[i];
    final source = _original(t);
    final candidates = [
      ...pool,
      ...staged,
    ].where((e) => e['accountId'] == t['accountId']).toList();
    final ref = '${source['reference'] ?? ''}'.trim();
    final strong = candidates.where(
      (e) =>
          (ref.isNotEmpty && _original(e)['reference'] == ref) ||
          (e['documentId'] == documentId &&
              (e['sourceTable'] ?? '') == (t['sourceTable'] ?? '') &&
              (e['sourceComponent'] ?? '') == (t['sourceComponent'] ?? '') &&
              e['sourceRow'] == t['sourceRow']),
    );
    final identified = strong.firstOrNull;
    if (identified != null) {
      final equal = _sameMoney(source, _original(identified));
      result.add(
        ReviewedImportRow(
          i,
          t,
          equal ? ImportMatch.duplicate : ImportMatch.conflict,
          equal
              ? 'Misma referencia u original y fila.'
              : 'La misma referencia o fila tiene otro importe, fecha o moneda.',
          identified,
        ),
      );
      consumed.add(identified['id']);
      continue;
    }
    final collision = candidates.where((e) => e['id'] == t['id']).firstOrNull;
    if (collision != null && !_sameMoney(source, _original(collision))) {
      result.add(
        ReviewedImportRow(
          i,
          t,
          ImportMatch.conflict,
          'El identificador ya existe con otros datos financieros.',
          collision,
        ),
      );
      continue;
    }
    final similar = candidates.where((e) {
      final old = _original(e);
      // Different bank references are distinct purchases even when identical.
      final oldRef = '${old['reference'] ?? ''}'.trim();
      return !consumed.contains(e['id']) &&
          !(ref.isNotEmpty && oldRef.isNotEmpty && ref != oldRef) &&
          _sameMoney(source, old) &&
          normalize(
                '${source['description']}',
              ).replaceAll(RegExp(r'\s+'), ' ') ==
              normalize(
                '${old['description']}',
              ).replaceAll(RegExp(r'\s+'), ' ');
    }).firstOrNull;
    if (similar != null && pool.contains(similar)) {
      consumed.add(similar['id']);
      result.add(
        ReviewedImportRow(
          i,
          t,
          ImportMatch.possible,
          'Coinciden cuenta, fecha, concepto e importe; falta una referencia común.',
          similar,
        ),
      );
    } else {
      result.add(
        ReviewedImportRow(i, t, ImportMatch.fresh, 'Movimiento nuevo.'),
      );
      // No-reference rows inside the same statement can be separate purchases.
      staged.add({...t, 'documentId': documentId});
    }
  }
  return result;
}

// Adapted from Brújula; see docs/PROVENANCE.md.
// Copyright 2026 Martin Calpe Blasco. All rights reserved.
import 'dart:convert';

typedef Json = Map<String, dynamic>;

/// Accept edge signs, accounting parentheses and validated grouping.
/// A separator followed by exactly three digits denotes thousands.
int moneyCents(String input) {
  Never invalid() =>
      throw const FormatException('Invalid or ambiguous amount.');
  var text = input
      .trim()
      .replaceAll('−', '-')
      .replaceAll(RegExp(r'[\u00a0\u202f]'), ' ');
  final accounting = text.startsWith('(') && text.endsWith(')');
  if (accounting) text = text.substring(1, text.length - 1).trim();
  if (text.contains('(') || text.contains(')')) invalid();
  final first = RegExp(r'\d').firstMatch(text);
  if (first == null) invalid();
  final last = RegExp(r'\d').allMatches(text).last;
  final edges = [text.substring(0, first.start), text.substring(last.end)];
  final token = RegExp(r'EUR|USD|GBP|€|\$|£|[+-]', caseSensitive: false);
  var signs = 0, currencies = 0;
  var negative = accounting;
  for (var i = 0; i < edges.length; i++) {
    final edge = edges[i].trim();
    var cursor = 0;
    for (final match in token.allMatches(edge)) {
      if (edge.substring(cursor, match.start).trim().isNotEmpty) invalid();
      final value = match.group(0)!;
      if (value == '-' || value == '+') {
        if (accounting || ++signs > 1 || (i == 1 && value == '+')) invalid();
        negative = value == '-';
      } else if (++currencies > 1) {
        invalid();
      }
      cursor = match.end;
    }
    if (edge.substring(cursor).trim().isNotEmpty) invalid();
  }
  final value = text.substring(first.start, last.end);
  if (!RegExp(r'^[\d., ]+$').hasMatch(value)) invalid();
  final comma = value.lastIndexOf(','), dot = value.lastIndexOf('.');
  String whole = value, fraction = '';
  String digits(String input, String separator) {
    if (RegExp(r'^\d+$').hasMatch(input)) return input;
    final escaped = RegExp.escape(separator);
    if (!RegExp('^\\d{1,3}(?:$escaped\\d{3})+\$').hasMatch(input)) invalid();
    return input.replaceAll(separator, '');
  }

  if (comma >= 0 && dot >= 0) {
    final decimal = comma > dot ? ',' : '.';
    final parts = value.split(decimal);
    if (parts.length != 2 || !RegExp(r'^\d{1,2}$').hasMatch(parts.last))
      invalid();
    whole = digits(parts.first, decimal == ',' ? '.' : ',');
    fraction = parts.last;
  } else if (comma >= 0 || dot >= 0) {
    final separator = comma >= 0 ? ',' : '.';
    final parts = value.split(separator);
    if (parts.length == 2 && RegExp(r'^\d{1,2}$').hasMatch(parts.last)) {
      whole = digits(parts.first, ' ');
      fraction = parts.last;
    } else {
      whole = digits(value, separator);
    }
  } else {
    whole = digits(value, ' ');
  }
  final result =
      BigInt.parse(whole) * BigInt.from(100) +
      BigInt.parse(fraction.padRight(2, '0'));
  if (result > BigInt.from(9007199254740991)) invalid();
  return negative ? -result.toInt() : result.toInt();
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
String _ref(Json row) => '${_original(row)['reference'] ?? ''}'.trim();
String _refKey(Json row) => jsonEncode([row['accountId'], _ref(row)]);
void _validateRow(Json row) {
  final source = _original(row);
  bool present(dynamic value) => value is String && value.trim().isNotEmpty;
  if (!present(row['id']) ||
      !present(row['accountId']) ||
      !present(source['date']) ||
      !present(source['currency']) ||
      source['amountCents'] is! int ||
      (source['amountCents'] as int).abs() > 9007199254740991) {
    throw const FormatException(
      'Transaction identity, date, currency and safe integer cents required.',
    );
  }
}

String _description(Json row) =>
    normalize('${_original(row)['description']}')
        .replaceAll(RegExp(r'\s+'), ' ');

/// Conservative one-to-one review. Ambiguous references retain their rows.
List<ReviewedImportRow> reviewImport(
  List<Json> incoming,
  List<Json> existing,
  String documentId,
) {
  final pool = existing.where((t) => t['deleted'] != true).toList()
    ..sort((a, b) => '${a['id']}'.compareTo('${b['id']}'));
  final ids = <String>{};
  for (final row in pool) {
    _validateRow(row);
    if (row['id'] is! String || !ids.add(row['id'] as String)) {
      throw const FormatException(
        'Existing transaction IDs must be unique strings.',
      );
    }
  }
  final referenceCounts = <String, int>{}, idCounts = <String, int>{};
  for (final row in incoming) {
    _validateRow(row);
    if (row['id'] is! String)
      throw const FormatException('Incoming transaction ID required.');
    idCounts[row['id']] = (idCounts[row['id']] ?? 0) + 1;
    if (_ref(row).isNotEmpty)
      referenceCounts[_refKey(row)] = (referenceCounts[_refKey(row)] ?? 0) + 1;
  }
  final consumed = <String>{}, staged = <Json>[];
  final result = <ReviewedImportRow>[];
  for (var i = 0; i < incoming.length; i++) {
    final t = incoming[i], source = _original(incoming[i]);
    final all = [...pool, ...staged];
    final candidates = all
        .where((e) => e['accountId'] == t['accountId'])
        .toList();
    void add(ImportMatch match, String reason, [Json? old]) =>
        result.add(ReviewedImportRow(i, t, match, reason, old));
    if (idCounts[t['id']]! > 1) {
      add(ImportMatch.conflict, 'Repeated incoming identifier.');
      continue;
    }
    final collision = all.where((e) => e['id'] == t['id']).firstOrNull;
    if (collision != null &&
        (collision['accountId'] != t['accountId'] ||
            !_sameMoney(source, _original(collision)) ||
            _ref(t) != _ref(collision))) {
      add(
        ImportMatch.conflict,
        'Identifier collides with another transaction.',
        collision,
      );
      continue;
    }
    final provenance = candidates
        .where(
          (e) =>
              documentId.isNotEmpty &&
              t['sourceRow'] != null &&
              e['sourceRow'] != null &&
              e['documentId'] == documentId &&
              e['sourceRow'] == t['sourceRow'] &&
              (e['sourceTable'] ?? '') == (t['sourceTable'] ?? '') &&
              (e['sourceComponent'] ?? '') == (t['sourceComponent'] ?? ''),
        )
        .toList();
    final strong = provenance.isNotEmpty
        ? provenance
        : candidates
              .where((e) => _ref(t).isNotEmpty && _ref(e) == _ref(t))
              .toList();
    if ((provenance.isEmpty && (referenceCounts[_refKey(t)] ?? 0) > 1) ||
        strong.length > 1) {
      add(
        ImportMatch.conflict,
        'Reference or source identity has multiple candidates.',
      );
      continue;
    }
    if (strong.isNotEmpty) {
      final old = strong.single;
      if (consumed.contains(old['id'])) {
        add(
          ImportMatch.conflict,
          'This existing record already matched another incoming row.',
          old,
        );
      } else {
        consumed.add(old['id']);
        final same = _sameMoney(source, _original(old));
        add(
          same ? ImportMatch.duplicate : ImportMatch.conflict,
          same
              ? 'Matching reference or source row.'
              : 'Identity matches but amount, date or currency differs.',
          old,
        );
      }
      continue;
    }
    if (collision != null) {
      add(
        ImportMatch.conflict,
        'Identifier matches without confirming source identity.',
        collision,
      );
      continue;
    }
    final similar = pool
        .where(
          (e) =>
              e['accountId'] == t['accountId'] &&
              !consumed.contains(e['id']) &&
              !(_ref(t).isNotEmpty &&
                  _ref(e).isNotEmpty &&
                  _ref(t) != _ref(e)) &&
              _sameMoney(source, _original(e)) &&
              _description(t) == _description(e),
        )
        .firstOrNull;
    if (similar != null) {
      consumed.add(similar['id']);
      add(
        ImportMatch.possible,
        'Matching account, date, description and amount; no common reference.',
        similar,
      );
    } else {
      add(ImportMatch.fresh, 'New transaction.');
      staged.add({...t, 'documentId': documentId});
    }
  }
  return result;
}

// Standalone model of Brújula's version/receipt workflow; see provenance.
// Copyright 2026 Martin Calpe Blasco. All rights reserved.
import 'dart:convert';

typedef Data = Map<String, dynamic>;
Data _copy(Data value) => jsonDecode(jsonEncode(value)) as Data;
String _canonical(dynamic value) {
  if (value is Map) {
    final keys = value.keys.cast<String>().toList()..sort();
    return '{${keys.map((k) => '${jsonEncode(k)}:${_canonical(value[k])}').join(',')}}';
  }
  if (value is List) return '[${value.map(_canonical).join(',')}]';
  return jsonEncode(value);
}

class VersionedRecord {
  final int version;
  final Data data;
  VersionedRecord(this.version, Data data) : data = _copy(data);
  Data toJson() => {'version': version, 'data': _copy(data)};
  factory VersionedRecord.fromJson(Data json) =>
      VersionedRecord(json['version'] as int, json['data'] as Data);
}

class Operation {
  final String id;
  final int baseVersion;
  final Data data;
  bool sent;
  String status;
  Operation(
    this.id,
    this.baseVersion,
    Data data, {
    this.sent = false,
    this.status = 'pending',
  }) : data = _copy(data);
  Data toJson() => {
    'id': id,
    'baseVersion': baseVersion,
    'data': _copy(data),
    'sent': sent,
    'status': status,
  };
  factory Operation.fromJson(Data json) => Operation(
    json['id'],
    json['baseVersion'],
    json['data'],
    sent: json['sent'],
    status: json['status'],
  );
  String get identity => _canonical({'baseVersion': baseVersion, 'data': data});
}

class Receipt {
  final String operationId;
  final String status;
  final VersionedRecord record;
  Receipt(this.operationId, this.status, this.record);
  Data toJson() => {
    'operationId': operationId,
    'status': status,
    'record': record.toJson(),
  };
  factory Receipt.fromJson(Data json) => Receipt(
    json['operationId'],
    json['status'],
    VersionedRecord.fromJson(json['record']),
  );
}

class SyncServer {
  VersionedRecord record;
  final Map<String, Receipt> _receipts = {};
  final Map<String, String> _identities = {};
  SyncServer(this.record);
  Receipt apply(Operation operation) {
    if (_receipts.containsKey(operation.id)) {
      if (_identities[operation.id] != operation.identity)
        throw StateError('Operation ID reused with different content.');
      return _receipts[operation.id]!;
    }
    final matches = operation.baseVersion == record.version;
    if (matches) record = VersionedRecord(record.version + 1, operation.data);
    final receipt = Receipt(
      operation.id,
      matches ? 'applied' : 'conflict',
      VersionedRecord(record.version, record.data),
    );
    _receipts[operation.id] = receipt;
    _identities[operation.id] = operation.identity;
    return receipt;
  }

  Data snapshot() => {
    'record': record.toJson(),
    'receipts': _receipts.map((k, v) => MapEntry(k, v.toJson())),
    'identities': _identities,
  };
  factory SyncServer.restore(Data json) {
    final server = SyncServer(VersionedRecord.fromJson(json['record']));
    server._receipts.addAll(
      (json['receipts'] as Map).map(
        (k, v) => MapEntry(k as String, Receipt.fromJson(v as Data)),
      ),
    );
    server._identities.addAll(Map<String, String>.from(json['identities']));
    return server;
  }
}

class SyncClient {
  final String device;
  VersionedRecord local;
  VersionedRecord remote;
  final List<Operation> pending = [];
  int _sequence = 0;
  SyncClient(this.device, VersionedRecord initial)
    : local = VersionedRecord(initial.version, initial.data),
      remote = VersionedRecord(initial.version, initial.data);
  Operation edit(Data data) {
    final unsent = pending
        .where((p) => !p.sent && p.status == 'pending')
        .toList();
    final base = unsent.isNotEmpty ? unsent.first.baseVersion : local.version;
    pending.removeWhere(unsent.contains);
    final op = Operation('$device-${++_sequence}', base, data);
    pending.add(op);
    local = VersionedRecord(base + 1, data);
    return op;
  }

  Operation send() {
    final operation = pending.firstWhere((p) => p.status == 'pending');
    operation.sent = true;
    return operation;
  }

  void reconcile(VersionedRecord confirmed, [Receipt? receipt]) {
    if (confirmed.version < remote.version) return;
    remote = VersionedRecord(confirmed.version, confirmed.data);
    if (receipt != null) {
      final operation = pending
          .where((p) => p.id == receipt.operationId)
          .firstOrNull;
      if (operation != null) {
        final satisfied =
            receipt.status == 'conflict' &&
            _canonical(operation.data) == _canonical(confirmed.data);
        if (satisfied ||
            (receipt.status == 'applied' &&
                confirmed.version > operation.baseVersion)) {
          pending.remove(operation);
        } else if (receipt.status == 'conflict') {
          operation.status = 'conflict';
        }
      }
    }
    if (pending.isEmpty) local = VersionedRecord(remote.version, remote.data);
  }

  void resolve({required bool keepLocal}) {
    if (!pending.any((p) => p.status == 'conflict'))
      throw StateError('No conflict to resolve.');
    final wanted = _copy(local.data);
    pending.clear();
    local = VersionedRecord(remote.version, remote.data);
    if (keepLocal) edit(wanted);
  }

  Data snapshot() => {
    'device': device,
    'sequence': _sequence,
    'local': local.toJson(),
    'remote': remote.toJson(),
    'pending': pending.map((p) => p.toJson()).toList(),
  };
  factory SyncClient.restore(Data json) {
    final client = SyncClient(
      json['device'],
      VersionedRecord.fromJson(json['remote']),
    );
    client.local = VersionedRecord.fromJson(json['local']);
    client._sequence = json['sequence'];
    client.pending.addAll(
      (json['pending'] as List).map((p) => Operation.fromJson(p as Data)),
    );
    return client;
  }
}

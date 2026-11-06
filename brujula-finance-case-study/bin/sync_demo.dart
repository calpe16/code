import 'dart:convert';

import 'package:brujula_finance_sample/sync_demo.dart';

void main() {
  var server = SyncServer(VersionedRecord(1, {'title': 'Review budget'}));
  final a = SyncClient('device-a', server.record);
  final b = SyncClient('device-b', server.record);
  a.edit({'title': 'Review November budget'});
  b.edit({'title': 'Review groceries budget'});
  final operation = a.send();
  server.apply(operation); // Response lost: keep the same operation identity.
  server = SyncServer.restore(jsonDecode(jsonEncode(server.snapshot())));
  final retry = server.apply(operation);
  a.reconcile(server.record, retry);
  final stale = server.apply(b.send());
  b.reconcile(server.record, stale);
  final retained = b.local.data['title'];
  b.resolve(keepLocal: true);
  final rebased = server.apply(b.send());
  b.reconcile(server.record, rebased);
  if (server.record.version != 3 || b.pending.isNotEmpty)
    throw StateError('Demo invariant failed');
  print(
    const JsonEncoder.withIndent('  ').convert({
      'data': 'Synthetic demo data',
      'retryVersion': retry.record.version,
      'deviceBConflict': stale.status,
      'preservedLocalEdit': retained,
      'final': server.record.toJson(),
      'pending': b.pending.length,
    }),
  );
}

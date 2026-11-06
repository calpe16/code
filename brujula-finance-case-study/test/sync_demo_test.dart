import 'dart:convert';

import 'package:brujula_finance_sample/sync_demo.dart';
import 'package:test/test.dart';

void main() {
  late SyncServer server;
  late SyncClient a;
  late SyncClient b;
  setUp(() {
    server = SyncServer(VersionedRecord(1, {'title': 'Initial'}));
    a = SyncClient('a', server.record);
    b = SyncClient('b', server.record);
  });
  Receipt apply(SyncClient c) {
    final r = server.apply(c.send());
    c.reconcile(server.record, r);
    return r;
  }

  void conflict() {
    a.edit({'title': 'A'});
    b.edit({'title': 'B'});
    apply(a);
    apply(b);
  }

  test('applied edit increments once and clears its pending operation', () {
    a.edit({'title': 'A'});
    expect(apply(a).status, 'applied');
    expect(server.record.version, 2);
    expect(a.pending, isEmpty);
  });
  test('lost response retry survives server and client snapshot restart', () {
    a.edit({'title': 'A'});
    final op = a.send();
    server.apply(op);
    server = SyncServer.restore(jsonDecode(jsonEncode(server.snapshot())));
    a = SyncClient.restore(jsonDecode(jsonEncode(a.snapshot())));
    final receipt = server.apply(a.send());
    a.reconcile(server.record, receipt);
    expect(server.record.version, 2);
    expect(a.pending, isEmpty);
  });
  test('operation identity cannot be reused with another payload', () {
    final op = a.edit({'title': 'A'});
    server.apply(op);
    expect(
      () => server.apply(Operation(op.id, 1, {'title': 'different'})),
      throwsStateError,
    );
  });
  test('conflict preserves the local and remote edits separately', () {
    conflict();
    expect(b.local.data['title'], 'B');
    expect(b.remote.data['title'], 'A');
    expect(b.pending.single.status, 'conflict');
  });
  test('accepting remote clears the conflict', () {
    conflict();
    b.resolve(keepLocal: false);
    expect(b.local.data['title'], 'A');
    expect(b.pending, isEmpty);
  });
  test('keeping local rebases into a new operation', () {
    conflict();
    final old = b.pending.single.id;
    b.resolve(keepLocal: true);
    expect(b.pending.single.baseVersion, 2);
    expect(b.pending.single.id, isNot(old));
    apply(b);
    expect(server.record.version, 3);
    expect(server.record.data['title'], 'B');
  });
  test('rebased edit conflicts again if another device writes first', () {
    conflict();
    b.resolve(keepLocal: true);
    a.edit({'title': 'A again'});
    apply(a);
    expect(apply(b).status, 'conflict');
    expect(b.local.data['title'], 'B');
  });
  test('unsent local edits coalesce against the original base', () {
    a.edit({'title': 'A'});
    a.edit({'title': 'B'});
    expect(a.pending.length, 1);
    expect(a.pending.single.baseVersion, 1);
    apply(a);
    expect(server.record.version, 2);
  });
  test(
    'an edit after sending stays distinct from its in-flight predecessor',
    () {
      a.edit({'title': 'A'});
      final op = a.send();
      a.edit({'title': 'B'});
      final receipt = server.apply(op);
      a.reconcile(server.record, receipt);
      expect(a.pending.length, 1);
      expect(a.local.data['title'], 'B');
      apply(a);
      expect(server.record.version, 3);
    },
  );
  test(
    'receipt without newer confirmed record cannot clear a pending edit',
    () {
      a.edit({'title': 'A'});
      final op = a.send();
      final receipt = server.apply(op);
      a.reconcile(VersionedRecord(1, {'title': 'Initial'}), receipt);
      expect(a.pending, isNotEmpty);
      a.reconcile(server.record, receipt);
      expect(a.pending, isEmpty);
    },
  );
  test('missing receipt retains pending changes and stale remote does not roll back', () {
    a.edit({'title': 'A'});
    a.reconcile(VersionedRecord(3, {'title': 'Remote'}));
    a.reconcile(VersionedRecord(2, {'title': 'Stale'}));
    expect(a.local.data['title'], 'A');
    expect(a.remote.version, 3);
  });
  test('already-satisfied conflict clears idempotently', () {
    a.edit({'title': 'same'});
    b.edit({'title': 'same'});
    apply(a);
    apply(b);
    expect(b.pending, isEmpty);
    expect(b.local.version, 2);
  });
}

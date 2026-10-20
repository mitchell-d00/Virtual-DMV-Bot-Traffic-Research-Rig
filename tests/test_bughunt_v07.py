"""v0.7 regression gates from the 2026-10-20 bug hunt.

Each class corresponds to one numbered finding in evaluation/BUGHUNT-V07.md.
They were run against unmodified v0.6 first; that red log is kept in
evaluation/BUGHUNT-RED-V07.txt. Demo keys only; not a production audit.
"""
import contextlib
import copy
import io
import json
import pathlib
import re
import tempfile
import unittest
from virtual_dmv import engine as E
from virtual_dmv import portable as C
from virtual_dmv import cli

NOW = 1893456000
PLATE = 'VDMV-RESEARCH-01'
BASE = pathlib.Path(__file__).resolve().parents[1]


def fresh():
    return E.bootstrap(seed='bughunt-v07', now=NOW)


def forge_renew(state, *, issued_at, requested_at=None):
    """Append an issuer- and owner-signed renew event, bypassing creation guards."""
    cur = E.audit(state)[PLATE]['credential']['payload']
    new = {**cur, 'revision': cur['revision'] + 1, 'issued_at': issued_at, 'expires_at': issued_at + 86400}
    intent = {'schema': 'vdmv.owner-intent.v2', 'kind': 'renew', 'plate_id': PLATE,
              'from_revision': cur['revision'],
              'requested_at': issued_at if requested_at is None else requested_at,
              'successor_sha256': C.sha256(new)}
    E._event(state, 'renew', {'credential': E._signed(state['issuer']['seed'], new),
                              'owner_intent': E._signed(state['owners']['alice']['seed'], intent)})


class Finding02PolicyIntegrity(unittest.TestCase):
    def test_audit_rejects_malformed_policy_shapes(self):
        bad_shapes = [
            {'description': 'x', 'anonymous': 'crawl', 'allows': {}, 'attribution': []},
            {'description': 'x', 'anonymous': [], 'allows': {'crawl': 'research'}, 'attribution': []},
            {'description': 'x', 'anonymous': ['teleport'], 'allows': {}, 'attribution': []},
            {'description': 'x', 'anonymous': [], 'allows': {'crawl': ['wizard']}, 'attribution': []},
            {'description': 'x', 'allows': {}, 'attribution': []},
            {'description': 7, 'anonymous': [], 'allows': {}, 'attribution': []},
        ]
        for shape in bad_shapes:
            with self.subTest(shape=shape):
                s = fresh()
                s['policies']['research-library'] = shape
                with self.assertRaises(E.ProtocolError):
                    E.audit_all(s)

    def test_audit_reports_policy_divergence_from_release_defaults(self):
        s = fresh()
        self.assertTrue(E.audit_all(s)['policies_match_release'])
        s['policies']['research-library']['anonymous'] = ['crawl']
        report = E.audit_all(s)
        self.assertFalse(report['policies_match_release'])
        self.assertEqual(report['policy_changes'], ['research-library'])

    def test_malformed_policy_still_yields_signed_denial(self):
        s = fresh()
        ch = E.challenge(s, 'anonymous', 'open-index', 'crawl', now=NOW)
        del s['policies']['open-index']['anonymous']
        before = len(s['receipts'])
        r = E.decide(s, ch, '', now=NOW)
        self.assertEqual((r['allow'], r['reason']), (False, 'MALFORMED_CREDENTIAL_OR_REGISTRY'))
        self.assertEqual(len(s['receipts']), before + 1)
        self.assertTrue(E.verify_receipts(s)['ok'])


class Finding03AuditChronology(unittest.TestCase):
    def test_audit_rejects_transition_after_predecessor_expired(self):
        s = fresh()
        cur = E.audit(s)[PLATE]['credential']['payload']
        forge_renew(s, issued_at=cur['expires_at'] + 10**6)
        with self.assertRaises(E.ProtocolError):
            E.audit(s)

    def test_audit_binds_v2_intent_time_to_successor(self):
        for bad in ('whenever', NOW + 999, True):
            with self.subTest(requested_at=bad):
                s = fresh()
                forge_renew(s, issued_at=NOW + 5, requested_at=bad)
                with self.assertRaises(E.ProtocolError):
                    E.audit(s)

    def test_engine_created_transitions_still_audit(self):
        s = fresh()
        E.renew(s, PLATE, 'alice', now=NOW + 10)
        E.transfer(s, PLATE, 'alice', 'bob', now=NOW + 20)
        self.assertEqual(E.audit(s)[PLATE]['credential']['payload']['revision'], 3)


class Finding04ReservedAnonymous(unittest.TestCase):
    def test_anonymous_is_not_an_issuable_plate_id(self):
        for label in ('anonymous', 'Anonymous', 'ANONYMOUS'):
            with self.subTest(label=label):
                s = fresh()
                with self.assertRaises(E.ProtocolError):
                    E.issue(s, 'alice', 'research', now=NOW, plate_id=label)
                self.assertEqual(len(s['events']), 2)

    def test_audit_rejects_imported_anonymous_plate(self):
        s = fresh()
        payload = {'schema': 'vdmv.plate.v1', 'plate_id': 'anonymous', 'issuer': s['issuer']['id'],
                   'participation_class': 'research', 'owner_public_key': s['owners']['alice']['public_key'],
                   'revision': 1, 'issued_at': NOW, 'expires_at': NOW + 86400}
        E._event(s, 'issue', {'credential': E._signed(s['issuer']['seed'], payload)})
        with self.assertRaises(E.ProtocolError):
            E.audit(s)


class Finding05BridgeTotality(unittest.TestCase):
    def assert_json_error(self, raw):
        out = json.loads(E.bridge(raw))
        self.assertFalse(out['ok'])
        self.assertIsInstance(out['error'], str)

    def test_bridge_never_raises(self):
        for payload in ({'op': 'roster', 'state': [1]}, {'op': 'roster', 'state': 'x'},
                        {'op': 'issue', 'args': [1]}, {'op': 'roster', 'args': 'x'},
                        [1], 'roster', None):
            with self.subTest(payload=payload):
                self.assert_json_error(json.dumps(payload))
        self.assert_json_error('[' * 100000 + ']' * 100000)
        self.assert_json_error('{not json')


class Finding06PoisonedQueue(unittest.TestCase):
    def test_malformed_pending_entries_are_pruned(self):
        s = fresh()
        for i in range(E.MAX_PENDING_CHALLENGES):
            s['challenges'][f'CH-junk{i}'] = 'junk' if i % 2 else {'expires_at': 'never'}
        ch = E.challenge(s, PLATE, 'research-library', 'crawl', now=NOW)
        self.assertEqual(list(s['challenges']), [ch['nonce']])


class Finding07NoLeakOnUnknownOwner(unittest.TestCase):
    def test_unknown_owner_fails_before_challenge_allocation(self):
        s = fresh()
        with self.assertRaises(E.ProtocolError):
            E.request(s, PLATE, 'research-library', 'crawl', owner='nobody', now=NOW)
        self.assertEqual((len(s['challenges']), s['sequence_nonce']), (0, 0))


class Finding08DispatchClockAndTtl(unittest.TestCase):
    def run_op(self, state, op, **args):
        return E.dispatch({'op': op, 'state': state, 'args': args})

    def test_renew_and_transfer_forward_ttl(self):
        s = fresh()
        out = self.run_op(s, 'renew', plate_id=PLATE, owner='alice', now=NOW + 60, ttl=999)
        p = E.audit(out['state'])[PLATE]['credential']['payload']
        self.assertEqual(p['expires_at'] - p['issued_at'], 999)
        out = self.run_op(out['state'], 'transfer', plate_id=PLATE, old_owner='alice', new_owner='bob', now=NOW + 120, ttl=5000)
        p = E.audit(out['state'])[PLATE]['credential']['payload']
        self.assertEqual((p['issued_at'], p['expires_at']), (NOW + 120, NOW + 5120))

    def test_ui_renew_can_extend_validity(self):
        s = fresh()
        out = self.run_op(s, 'renew', plate_id=PLATE, owner='alice', now=NOW + 80000)
        p = E.audit(out['state'])[PLATE]['credential']['payload']
        self.assertGreater(p['expires_at'], NOW + 86400)


class Finding09DistinctOwnerKeys(unittest.TestCase):
    def test_owner_seed_reuse_is_rejected(self):
        s = fresh()
        with self.assertRaises(E.ProtocolError):
            E.add_owner(s, 'eve', seed=s['owners']['alice']['seed'])
        self.assertNotIn('eve', s['owners'])

    def test_audit_rejects_imported_duplicate_owner_key(self):
        s = fresh()
        s['owners']['eve'] = copy.deepcopy(s['owners']['alice'])
        with self.assertRaises(E.ProtocolError):
            E.audit_all(s)


class Finding10Cli(unittest.TestCase):
    def call(self, *argv):
        err = io.StringIO()
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(err):
            try:
                code = cli.main(list(argv))
            except SystemExit as exit_:
                code = exit_.code
        return code, err.getvalue()

    def test_at_zero_is_honored(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 's.json'
            self.assertEqual(self.call('new', '--state', str(path), '--at', '0')[0], 0)
            self.assertEqual(json.loads(path.read_text())['created_at'], 0)

    def test_protocol_errors_exit_cleanly_from_main(self):
        with tempfile.TemporaryDirectory() as td:
            path = pathlib.Path(td) / 's.json'
            self.call('new', '--state', str(path))
            code, err = self.call('request', '--state', str(path), '--owner', 'nobody')
            self.assertEqual(code, 2)
            self.assertIn('Error:', err)
            self.assertNotIn('Traceback', err)


class Finding11StrictChallengeBytes(unittest.TestCase):
    def test_numerically_equal_but_retyped_challenge_is_rejected(self):
        s = fresh()
        ch = E.challenge(s, PLATE, 'research-library', 'crawl', now=NOW)
        proof = E.holder_proof(s, 'alice', ch)
        alt = copy.deepcopy(ch)
        alt['issued_at'] = float(alt['issued_at'])
        r = E.decide(s, alt, proof, now=NOW)
        self.assertEqual((r['allow'], r['reason']), (False, 'INVALID_OR_REPLAYED_CHALLENGE'))


class Finding01BrowserOracleGuard(unittest.TestCase):
    def test_verdict_is_assigned_only_after_oracle_check(self):
        js = (BASE / 'browser/client.js').read_text(encoding='utf8')
        for fn in ('inspect', 'choose'):
            match = re.search(r'async function ' + fn + r'\([^)]*\)\{(.*?)\n\}', js, re.S)
            self.assertIsNotNone(match, fn + '() not found in client.js')
            body = match.group(1)
            self.assertNotRegex(body, r'verdict=replay\.decision;\s*if\(replay\.scenario_matches_expectation',
                                fn + '() assigns verdict before the oracle guard')


class Finding12ReproducibleEvidence(unittest.TestCase):
    def test_scenario_runner_honors_source_date_epoch(self):
        src = (BASE / 'tools/run_scenarios.py').read_text(encoding='utf8')
        self.assertIn('SOURCE_DATE_EPOCH', src)


if __name__ == '__main__':
    unittest.main()

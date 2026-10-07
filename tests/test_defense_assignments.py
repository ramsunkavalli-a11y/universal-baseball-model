import unittest

import numpy as np

from universal_baseball import defense_assignments as a


def fixture():
    row = dict(row_id=1, player_id=10, origin_year=2024, outer_fold=2,
               origin_dh_outs=27., source_position='3', stage='Upper minors', age=21., prior_debut=0)
    source = dict(row_id=1, player_id=10, origin=2024, fold=2,
                  current_role_periods=[], current_source_status='unknown')
    bounds = dict(row_id=1, player_id=10, origin=2024, fold=2,
                  MLB_fielding_outs=None, MLB_reviewed_starts=None,
                  minor_fielding_outs=None, minor_reviewed_starts=None)
    return row, source, bounds


class AssignmentTests(unittest.TestCase):
    def test_gradient(self):
        rng = np.random.default_rng(4)
        x = np.column_stack([np.ones(5), rng.normal(size=(5, 3))])
        t = rng.dirichlet(np.ones(9), size=5)
        w = a.person_weights([1, 1, 2, 3, 3])
        b = rng.normal(size=36)
        _, g = a.objective(b, x, t, w)
        eps = 1e-6
        numerical = np.array([(a.objective(b+np.eye(36)[j]*eps, x, t, w)[0]-
                               a.objective(b-np.eye(36)[j]*eps, x, t, w)[0])/(2*eps) for j in range(36)])
        np.testing.assert_allclose(g, numerical, atol=2e-8, rtol=0)

    def test_each_person_total_weight_one(self):
        w = a.person_weights([1, 1, 2, 3, 3, 3])
        np.testing.assert_allclose(w, [.5, .5, 1., 1/3, 1/3, 1/3])

    def test_boundary_labels_fit(self):
        x = np.array([[0.], [1.], [.5], [.8]])
        t = np.zeros((4, 9)); t[0, 1] = 1; t[1, 8] = 1; t[2, 1] = .5; t[2, 8] = .5; t[3, 8] = 1
        m = a.fit(x, t, [1, 2, 3, 4])
        p = a.predict(x, m)
        self.assertTrue(np.isfinite(p).all())
        np.testing.assert_allclose(p.sum(axis=1), 1.)
        self.assertGreater(p[1, 8], p[0, 8])

    def test_invalid_labels(self):
        with self.assertRaises(ValueError):
            a.fit([[0.]], np.zeros((1, 9)), [1])

    def test_missing_not_certified_zero(self):
        row, source, bounds = fixture()
        f = a.features(row, source, bounds, {}, [])
        self.assertEqual(f['inputs']['current_s11_field_known'], 0.)
        self.assertEqual(f['fallback_kind'], 'roster_or_unknown')
        self.assertEqual(f['fallback_shares'][1], 1.)
        self.assertEqual(f['current_dominant_role'], 0)

    def test_levels_separate_and_DH_mismatch_not_filled(self):
        row, source, bounds = fixture()
        source['current_role_periods'] = [dict(player_id=10, season=2024, sport_id=s,
            position_code=p, fielding_outs=outs, reviewed_starts=starts)
            for s,p,outs,starts in [(11,3,27,1), (12,3,2700,100), (12,10,0,8)]]
        cert = {(10,2024,s): dict(measurements=dict(fielding_outs=dict(full_year=True),
                  reviewed_starts=dict(full_year=s == 11))) for s in (11,12)}
        f = a.features(row, source, bounds, cert, [])
        self.assertLess(f['inputs']['current_s11_r3'], f['inputs']['current_s12_r3'])
        self.assertEqual(f['inputs']['current_s12_r10'], 0.)
        self.assertEqual(f['inputs']['current_s12_DH_known'], 0.)
        self.assertEqual(f['current_counts'][1], 101.)

    def test_older_and_future_are_separate(self):
        row, source, bounds = fixture()
        annual = [dict(player_id=10, season=y, is_mlb=False,
                    **{f'outs_{p}': 270 if p == pos else 0 for p in range(2,10)}, starts_10=0)
                  for y,pos in [(2023,9),(2018,6),(2025,4)]]
        f = a.features(row, source, bounds, {}, annual)
        self.assertGreater(f['inputs']['minor_lag1_r9'], 0.)
        self.assertEqual(f['inputs']['minor_older_seen_r6'], 1.)
        self.assertEqual(f['inputs']['minor_older_seen_r4'], 0.)
        self.assertEqual(f['inputs']['minor_lag2_known'], 0.)

    def test_unplaced_mass_not_late(self):
        row, source, bounds = fixture()
        bounds['MLB_fielding_outs'] = dict(August_onward_minimum=[0,27,0,0,0,0,0,0,0],
                                         unresolved_period_exposure=[0,54,0,0,0,0,0,0,0])
        f = a.features(row, source, bounds, {}, [])
        self.assertGreater(f['inputs']['MLB_unplaced_r3'], f['inputs']['MLB_late_r3'])

    def test_existing_catching_guard_unknown_and_unseen(self):
        learned = np.ones(9); fallback = np.zeros(9); fallback[1] = 1
        p = a.allowed_shares(learned, fallback, unseen=True, catching=False, unknown=False)
        np.testing.assert_equal(p, fallback)
        p = a.allowed_shares(learned, fallback, unseen=False, catching=False, unknown=False)
        self.assertEqual(p[0], 0.); self.assertAlmostEqual(p.sum(), 1.)
        np.testing.assert_equal(a.allowed_shares(learned, fallback, unseen=False, catching=True, unknown=True), np.zeros(9))

    def test_source_identity_and_chronology(self):
        row, source, bounds = fixture()
        source['current_role_periods'] = [dict(player_id=10, season=2025, sport_id=1)]
        with self.assertRaises(ValueError):
            a.features(row, source, bounds, {}, [])


if __name__ == '__main__':
    unittest.main()

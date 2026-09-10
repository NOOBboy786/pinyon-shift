import importlib.util
from pathlib import Path
import unittest


spec = importlib.util.spec_from_file_location(
    "rank_corpus", Path(__file__).resolve().parents[1] / "rank-fh1-gpu-corpus.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class RankCorpusTests(unittest.TestCase):
    def test_independent_families_survive_key_overflow(self):
        family = dict(vertex_shader='000000000000000A', pixel_shader='000000000000000B',
                      count=3, first_frame=60, last_frame=180)
        corpus = dict(schema='pinyon-shift.fh1-gpu-corpus.v3', overflow=900,
                      collisions=0, shader_family_overflow=0, shader_families=[family],
                      observation_frame_stride=60, unique_keys=65536, unique_passes=12)
        ranked = module.rank_families(corpus)
        self.assertEqual(ranked['draws'], 3)
        self.assertEqual(ranked['status'], 'complete_for_observed_draws')
        self.assertEqual(ranked['observation_frame_stride'], 60)
        with self.assertRaises(ValueError):
            module.rank(corpus)
        self.assertEqual(module.rank_families(dict(corpus, shader_family_overflow=1))['status'], 'incomplete')
        for bad in (dict(corpus, shader_families=[family, family]),
                    dict(corpus, shader_family_overflow=-1),
                    dict(corpus, shader_families=[dict(family, last_frame=0)])):
            with self.assertRaises(ValueError):
                module.rank_families(bad)
        recorder_spec = importlib.util.spec_from_file_location('recorder',
            Path(__file__).resolve().parents[1]/'record-fh1-discovery.py')
        recorder = importlib.util.module_from_spec(recorder_spec)
        recorder_spec.loader.exec_module(recorder)
        _, coverage, pairs = recorder.coverage_snapshot(corpus, module, set())
        self.assertEqual(coverage['detailed_inventory_status'], 'incomplete')
        self.assertEqual(coverage['family_inventory_status'], 'complete_for_observed_draws')
        self.assertEqual(len(coverage['new_pairs_since_checkpoint']), 1)
        self.assertEqual(recorder.coverage_snapshot(corpus, module, pairs)[1]['new_pairs_since_checkpoint'], [])
        old = {k:v for k,v in corpus.items() if k not in ('shader_families','shader_family_overflow')}
        with self.assertRaises(ValueError):
            recorder.coverage_snapshot(old, module, pairs)

    def test_snapshot_coverage_and_rejected_ambiguity(self):
        def entry(identity, kind, count, indices, vs="a", pipeline="p"):
            return dict(identity=identity, kind=kind, count=count, index_count=indices,
                        vertex_shader=vs, pixel_shader="b", pipeline_state=pipeline)
        corpus = dict(schema="pinyon-shift.fh1-gpu-corpus.v3", overflow=0, collisions=0,
                      entries=[entry("1", 1, 4, 3), entry("2", 1, 2, 5, pipeline="q"),
                               entry("3", 2, 100, 99), entry("4", 1, 1, 90, vs="c")])
        result = module.rank(corpus)
        self.assertEqual(result["draws"], 7)
        self.assertEqual(result["pairs"][0], dict(vertex_shader="a", pixel_shader="b",
                         draws=6, submitted_indices=22, pipelines=["p", "q"]))
        for bad in (dict(corpus, overflow=1), dict(corpus, collisions=1),
                    dict(corpus, entries=corpus["entries"] * 2),
                    dict(corpus, entries=[entry("1", 1, -1, 3)])):
            with self.assertRaises(ValueError):
                module.rank(bad)

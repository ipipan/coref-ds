import unittest
import tempfile
from pathlib import Path

from dotenv import dotenv_values
from coref_ds.tei.layers.coreference import CoreferenceLayer
from coref_ds.tei.layers.mention import MentionLayer
from coref_ds.tei.mention import Mention
from coref_ds.tei.layers.morphosyntax import MorphosyntaxLayer
from coref_ds.tei.layers.segmentation import SegmentationLayer
from coref_ds.tei.pcc import PCCStructureLayer
from coref_ds.utils import count_mentions

local_config = dotenv_values(".env")

from coref_ds.tei.tei_doc import TEIDocument
from coref_ds.corefud.corefud_doc import CorefUDDoc

layers_mapping = {
    'text_structure': (PCCStructureLayer, 'text'),
    'coreference': (CoreferenceLayer, 'ann_coreference'),
    'groups': (None, 'ann_groups'),
    'mentions': (MentionLayer, 'ann_mentions'),
    'morphosyntax': (MorphosyntaxLayer, 'ann_morphosyntax'),
    'named_entities': (None, 'ann_named'),
    'segmentation': (SegmentationLayer, 'ann_segmentation'),
    'senses': (None, 'ann_senses'),
}


class TestTextAPI(unittest.TestCase):
    def test_mention_to_tuple_iter(self):
        tei_doc = TEIDocument(
            Path(local_config['PCC_ROOT']) / 'train' / '38b',
        )
        clusters = tei_doc.text.clusters
        for cluster in clusters:
            for m_start, m_end in cluster:  # __iter__()
                pass

    def test_noncontinuous_mentions(self):
        tei_doc = TEIDocument(
            Path(local_config['PCC_ROOT']) / 'train' / '3496',
        )
        text = tei_doc.text
        print()
        for mention in text.mentions:
            print(mention.text, mention.is_continuous)

        non_continuous_mentions = list(filter(lambda el: not el.is_continuous, text.mentions))
        print([m.text for m in non_continuous_mentions])
        for ind, subm in enumerate(non_continuous_mentions[0].submentions):
            print(ind, [(seg.orth, seg.get_token_index()) for seg in subm])
        print()
        self.assertEqual(len(non_continuous_mentions), 2)


    def test_count_noncontinuous_mentions(self):
        train_path = Path(local_config['PCC_ROOT']) / 'test'
        stats = dict()

        for p in train_path.iterdir():
            if not p.is_dir():
                continue
            tei_doc = TEIDocument(p)
            text = tei_doc.text
            non_continuous_mentions = list(filter(lambda el: not el.is_continuous, text.mentions))
            stats[text.text_id] = len(non_continuous_mentions)

        print()
        print(sum(stats.values()), len(stats.keys()))
        print()
        print(stats)

    def test_noncontinuous_mentions_indices(self):
        tei_doc = TEIDocument(
            Path(local_config['PCC_ROOT']) / 'train' / '3496',
        )
        text = tei_doc.text
        print()
        for mention in text.mentions:
            print(mention.text, mention.is_continuous)

        non_continuous_mentions = list(filter(lambda el: not el.is_continuous, text.mentions))

        # get mention indices (maximal coherent, continuous mention)
        for mention in text.mentions:
            span = mention.get_mention_span()
            if not mention.is_continuous:
                print(f"{[text.segments[ind] for ind in range(*span)]}")

        # get mention indices (full mention)
        non_continuous_mentions = 0
        for mention in text.mentions:
            span = mention.get_mention_span(include_noncontinuous=True)
            if isinstance(span, list) and len(span) > 1:
                non_continuous_mentions += 1
                print(f"\npruned: {mention.get_mention_span()} | {[s.orth for s in mention.segments]}")
        self.assertEqual(non_continuous_mentions, 2)


    def test_noncontinuous_mentions_clusters(self):
            tei_doc = TEIDocument(
                Path(local_config['PCC_ROOT']) / 'train' / '3496',
            )
            text = tei_doc.text

            # get all clusters
            mentions = []
            for cluster in text.clusters:
                for mention in cluster:
                    mentions.append(mention)

            mentions = sorted(mentions)
            self.assertIn((47,60), mentions)
            self.assertIn((36, 40), mentions)

    def test_noncontinuous_mentions_heads(self):
            tei_doc = TEIDocument(
                Path(local_config['PCC_ROOT']) / 'train' / '3342',
            )
            text = tei_doc.text

            banana = list(filter(
                lambda x: not x.is_continuous, sorted(text.mentions, key=lambda x: x.span_start)
                ))[1]
            banana_tokens = [seg.orth for seg in banana.segments]
            print(banana)
            self.assertIn('banany', banana_tokens)

    def test_aglutinants(self):
            tei_doc = TEIDocument(
                Path(local_config['PCC_ROOT']) / 'train' / '478',
            )
            text = tei_doc.text
            text.find_agglutinants()
            merged_mentions = text.merge_agglutinative_mentions()
            self.assertEqual(len(merged_mentions), 0)

    def test_aglutinants_corefud(self):
            tei_doc = CorefUDDoc(
                Path(local_config['PCC_COREFUD_SINGLE_TEXTS']) / 'train' / '478.conllu',
            )
            text = tei_doc.text
            merged_mentions = text.merge_agglutinative_mentions(verbose=True)
            self.assertEqual(len(merged_mentions), 3)

    def test_aglutinants_whole_dataset(self):
            for p in (Path(local_config['PCC_ROOT']) / 'train').iterdir():
                 if not p.is_dir():
                      continue
                 else:
                    tei_doc = TEIDocument(
                        p,
                    )
                    text = tei_doc.text
                    text.find_agglutinants()
                    merged_mentions = text.merge_agglutinative_mentions()
                    self.assertEqual(len(merged_mentions), 0)
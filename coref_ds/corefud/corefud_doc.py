from pathlib import Path
from collections import Counter
from abc import abstractmethod


import udapi
from udapi.block.read.conllu import Conllu as ConlluReader
from udapi.block.write.conllu import Conllu as ConlluWriter
from coref_ds.corefud.utils import add_mention, clusters_from_doc, node_to_segment, prepare_alignment

from coref_ds.text import Text


class CorefUDDoc:
    def __init__(self, p: Path):
        self.doc_path = p
        self.corpus_name = p.parent.parent.name  # after preprocessing
        self.part = p.parent.name
        self.udapi_docs = None
        self.first_sentence_ind = 0
        self.first_paragraph_ind = 0
        self.parse_doc()

    @classmethod
    def from_file(cls, p: Path):
        return cls(p)

    def parse_doc(self):
        with open(self.doc_path) as f:
            udapi_docs = ConlluReader(filehandle=f, split_docs=True).read_documents()
        self.udapi_docs = list(
            filter(lambda doc: list(doc.nodes_and_empty), udapi_docs)
            )

    @abstractmethod
    def get_sentence_ind(self, address: str) -> int:
        pass

    @abstractmethod
    def get_paragraph_ind(self, address: str) -> int:
        pass

    def get_index(self, address, first_sentence_ind = None, first_paragraph_ind = None):
        if first_sentence_ind is None:
            first_sentence_ind = self.first_sentence_ind

        paragraph_ind = 0
        if first_paragraph_ind is None:
            first_paragraph_ind = self.first_paragraph_ind

        paragraph_ind = self.get_paragraph_ind(address)
        sentence_ind = self.get_sentence_ind(address)

        return {
            'paragraph_ind': paragraph_ind - first_paragraph_ind,
            'sentence_ind': sentence_ind - first_sentence_ind,
        }
    
    @property
    def clusters(self) -> list[list[int]]:
        if self._clusters:
            return self._clusters
        else:
            clusters = []
            # @TODO
            
    @property
    def text(self) -> Text:
        if len(self.udapi_docs) == 1:
            doc = self.udapi_docs[0]
            segment_ind = 0
            segments_meta = []
            for sentence in doc.trees:
                words = list(sentence.descendants)
                words_addresses = {w.address():w_ind for w_ind, w in enumerate(words)}
                for w_ind, w in enumerate(words):
                    last_in_sent = w_ind == len(words) - 1
                    segments_meta.append(
                        node_to_segment(w, segment_ind, last_in_sent=last_in_sent, words_addresses=words_addresses)
                    )
                    segment_ind += 1

            text_id = Path(doc.meta.get('docname', self.doc_path.name)).stem.split('_')[0]
            cluster_mapping = clusters_from_doc(doc, segments_meta)
            text = Text(
                text_id=text_id,
                segments=[n.form for n in doc.nodes],
                segments_meta=segments_meta,
                clusters=cluster_mapping['clusters'],
                mentions=cluster_mapping['mentions'],
            )
            return text
        else:
            raise ValueError('More than one document in CorefUDDoc')

    def add_text_clusters_to_doc(self, text, doc, mentions_set=None, ent_ids=None):
        if mentions_set is None:
            mentions_set = set()
        if ent_ids is None:
            ent_ids = [1]
        udapi_words = [word for word in doc.nodes_and_empty]
        udapi_words_str = [word.form for word in udapi_words]
        aligned_clusters, aligned_heads = prepare_alignment(text, udapi_words_str)
        for cluster in aligned_clusters:
            ent_id = len(ent_ids)
            entity = doc.create_coref_entity(eid=f'c{ent_id}')
            ent_ids.append(ent_id)
            for mention in cluster:
                add_mention(
                    mention,
                    entity,
                    udapi_words,
                    udapi_words_str,
                    aligned_heads,
                    mentions_set=mentions_set,
                )
        udapi.core.coref.store_coref_to_misc(doc)

    def map_clusters(self, texts: list[Text], docname_mapper: callable = None):
        if docname_mapper is None:
            docname_mapper = lambda x: x
        
        self.remove_coref() # remove previous coref
        udapi_docs_map = {docname_mapper(doc.meta['docname']): doc for doc in self.udapi_docs}
        ent_ids = [1]

        for text in texts:
            doc = udapi_docs_map.get(text.text_id)
            if doc:
                print(f'Adding clusters for {text.text_id}')
                self.add_text_clusters_to_doc(text, doc, ent_ids=ent_ids)
            else:
                print(f'No doc found for {text.text_id}')

    def to_file(self, p: Path):
        with open(p, 'w') as f:
            writer = ConlluWriter(filehandle=f)
            for ind, doc in enumerate(self.udapi_docs):
                writer.before_process_document(doc)
                writer.process_document(doc)
            writer.after_process_document(doc)

    def remove_coref(self):
        for doc in self.udapi_docs:
            doc._eid_to_entity = {}

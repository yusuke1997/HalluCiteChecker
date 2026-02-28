import os
import re
from typing import List, Dict, Any
from .base import BaseCitationRecognizer
from HalluCiteChecker import Citation

from pprint import pprint
# --- PyTorch DataLoader のマルチプロセス回避パッチ ---
import torch.utils.data
class SingleProcessDataLoader(torch.utils.data.DataLoader):
    def __init__(self, *args, **kwargs):
        kwargs['num_workers'] = 0
        super().__init__(*args, **kwargs)
torch.utils.data.DataLoader = SingleProcessDataLoader

# パッチ適用後に DeLFT をインポート
import delft

# delft.DELFT_PROJECT_DIR = os.path.dirname(__file__)
delft.DELFT_PROJECT_DIR = os.path.join(os.path.dirname(__file__), "models")
#print(__file__)

from delft.sequenceLabelling import Sequence
from huggingface_hub import hf_hub_download

class DelftCitationRecognizer(BaseCitationRecognizer):
    def __init__(
        self, 
        model_name: str = 'grobid-citation-BidLSTM_CRF_FEATURES'
    ):
        """
        DeLFTモデルの初期化とロード
        """
        self.model_name = model_name
        
        print(f"Loading DeLFT model: {self.model_name} ...")
        self.model = Sequence(self.model_name)
        
        # Pathを無理やり押し込めるため。ここは再考の余地があるけど、delftに特化した処理なので、正直どうでもいい。
        # Hard Coding...
        embedding_lmdb_path_orig = hf_hub_download(
            repo_id="yusuke1997/glove-lmdb",
            filename="glove-840B/data.mdb",
            repo_type="model",
            revision="main",
        )
        embedding_lmdb_path = os.path.dirname(os.path.dirname(embedding_lmdb_path_orig))
        self.model.registry['embedding-lmdb-path'] = embedding_lmdb_path

        #print(self.model.registry)
        #exit()
        dir_path = os.path.join(os.path.dirname(__file__), "models")
            
        self.model.load(dir_path=dir_path)
        print("Model loaded successfully.")

    def parse(self, citations: List[Citation]) -> List[Dict[str, Any]]:
        """
        DeLFTを使用して引用文字列のリストを解析する
        """
        if not citations:
            return []

        raw_references = [raw_item.raw_reference for raw_item in citations]
        
        # tagメソッドは {'texts': [{'text': '...', 'entities': [...]}]} のような辞書を返す
        result = self.model.tag(raw_references, output_format='json')

        raw_items = []
        if isinstance(result, dict) and 'texts' in result:
            raw_items = result['texts']
        elif isinstance(result, list):
            raw_items = result
        
        return [self._map_to_dataclass(c, item) for c, item in zip(citations, raw_items)]

    def _map_to_dataclass(self, c: Citation, raw_item: dict) -> Citation:
        """DeLFTの出力を動的にParsedCitationへマッピング"""
        #parsed = ParsedCitation(raw_reference=raw_item.get('text', ''))

        assert raw_item.get('text', '') == c.raw_reference
        
        for ent in raw_item.get('entities', []):
            raw_tag = ent.get('class', '')
            text = ent.get('text', '').strip()
            
            # タグの整形 ('<title>' -> 'title', 'B-<author>' -> 'author')
            tag_name = raw_tag.strip('<>')
                       
            # 既に値が入っている場合（例: editorが複数）はスペースで結合
            current_val = getattr(c, tag_name)
            if current_val:
                setattr(c, tag_name, f"{current_val} {text}")
            else:
                setattr(c, tag_name, text)
                
            #match = re.search(r"\b(\d{4}\.\d{4,5}(?:v\d+)?)\b", parsed.raw_reference)
            # \b の代わりに (?<!\d) と (?!\d) を使う
            match = re.search(r"(?<!\d)(\d{4}\.\d{4,5}(?:v\d+)?)(?!\d)", c.raw_reference)
            if match:
                setattr(c, "arxiv", match.group(1))

        return c

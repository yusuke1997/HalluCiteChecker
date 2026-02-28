from abc import ABC, abstractmethod
from typing import List, Dict, Any
from pprint import pprint
from dataclasses import dataclass, field, fields
from HalluCiteChecker import Citation

class BaseCitationRecognizer(ABC):
    """
    引用解析パーサーの抽象基底クラス
    """
    
    @abstractmethod
    def parse(self, citations: List[Citation]) -> List[Dict[str, Any]]:
        """
        複数の引用文字列を受け取り、解析結果のリストを返す
        """
        pass

    def parse_single(self, citation: Citation) -> Dict[str, Any]:
        """
        単一の引用文字列を解析するユーティリティメソッド
        """
        results = self.parse_batch([citation], batch_size = 1)

        return results

    def parse_batch(self, citations: List[Citation], batch_size: int = 8) -> List[Dict[str, Any]]:
        """
        大量のリストを指定したバッチサイズごとに分割して処理する。
        メモリ溢れ（OOM）を防ぎつつ、モデルの並列計算を活用するためのメソッド。
        """
        all_results = []
        for i in range(0, len(citations), batch_size):
            batch = citations[i : i + batch_size]
            
            # サブクラスで実装された一括処理 (parse) に投げる
            batch_results = self.parse(batch)
            all_results.extend(batch_results)

        # これ引数に持っていても良いかもしれないが、一旦パス
        # Citation.reset_id_counter()
        #return [setattr(result, 'id', i) for i, result in enumerate(all_results)]
        return all_results

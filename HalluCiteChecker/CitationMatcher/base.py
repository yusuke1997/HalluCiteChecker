import os
from datasets import load_dataset
from abc import ABC, abstractmethod
from typing import List
from HalluCiteChecker import Citation

class BaseCitationMatcher(ABC):
    def __init__(
        self,
        db_path: str,
        score_cutoff: int = 90,
        workers: int = 8
    ):
        """
        Args:
            db_path: 読み込むデータベースのローカルパス(CSV/TSV)、または Hugging Face Dataset のパス
            score_cutoff: マッチングの閾値
            workers: 並列処理のワーカー数
        """
        self.score_cutoff = score_cutoff
        self.workers = workers
        self.db_name = db_path.split('/')[-1]

        # 子クラスの名前（FuzzCandidateGeneratorなど）を自動で取得して表示
        print(f"Initializing {self.__class__.__name__} for [{self.db_name}]...")

        # _loadメソッドを使って動的にデータを読み込み、正規化する
        self.titles_norm = self._load(db_path)

        #print(type(self.titles_norm))
        
        print(f"Database [{self.db_name}] loaded successfully. ({len(self.titles_norm)} records)")

    def _normalize(self, text: str) -> str:
        """空白を取り除き、小文字化する"""
        # NaNなどが混ざっていた場合の安全対策として str() で囲む
        return "".join(str(text).lower().split()).replace('-', '')

    def _load(self, db_path: str) -> List[str]:
        """
        パスの形式を判定し、CSV / TSV / Hugging Face Dataset からタイトルを読み込む
        """
        titles = []

        # 1. ローカルファイルとして存在する場合
        if os.path.exists(db_path):
            ext = os.path.splitext(db_path)[-1].lower()
            try:
                if ext == '.csv':
                    ds = load_dataset('csv', data_files=db_path, split='train')
                elif ext == '.tsv':
                    ds = load_dataset('csv', data_files=db_path, delimiter='\t', split='train')
                else:
                    raise ValueError(f"Unsupported local file format: {ext}. Please use .csv or .tsv")
            except Exception as e:
                raise ValueError(f"Failed to load local file '{db_path}' via datasets. Error: {e}")
        
        # 2. ローカルに無い場合は Hugging Face Datasets として読み込みを試みる
        else:
            try:
                ds = load_dataset(db_path, split='train')
            except Exception as e:
                raise ValueError(f"Failed to load '{db_path}' from Hugging Face. Error: {e}")
            
        
        # 共通処理: title カラムの存在確認
        if "title" not in ds.column_names:
            raise ValueError(f"Dataset '{db_path}' does not contain a 'title' column.")

        if "normalized_title" not in ds.column_names:
            # datasets の高速な batched map 用の関数を内部に定義 
            def normalize_batch(batch):
                return {
                    "normalized_title": [self._normalize(t) for t in batch["title"]]
                }
            
            print(f"Normalizing titles using {self.workers} workers...")
            # マルチプロセスかつバッチ単位で一気に正規化
            # remove_columns で元の重いデータ（abstract等）を捨ててメモリを極限まで節約する
            ds = ds.map(
                normalize_batch,
                batched=True,
                num_proc=self.workers,
                remove_columns=ds.column_names,
                desc="Normalizing titles"
            )
        #print('aaaaa')
        #aa = ds.data.column("normalized_title").to_pylist()
        #print('ccccc')
        # 抽出済みのリストとして返す（ここはすでに高速化・軽量化されている）
        return  ds.data.column("normalized_title").to_pylist()

    
    @abstractmethod
    def verify(self, citations: List[Citation]) -> List[Citation]:
        """
        引用リストを自身のデータベースと照合して検証する
        
        Args:
            citations: 検証対象の ParsedCitation オブジェクトのリスト
                           
        Returns:
            List[ParsedCitation]: データベースに見つからなかったハルシネーション候補のリスト
        """
        pass

    def is_match(self, citation: Citation) -> bool:
        """
        含まれているかどうかだけ判定するやつ
        あとで@abstractmethodを付けるように修正
        """
        pass

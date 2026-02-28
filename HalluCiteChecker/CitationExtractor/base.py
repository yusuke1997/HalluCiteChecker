from abc import ABC, abstractmethod

class CitationItem:
    """どのライブラリを使っても最終的にこの形式に変換する"""
    def __init__(self, text, bboxes=None):
        self.text = text.strip()
        self.bboxes = bboxes if bboxes else [] # list of {'page': int, 'rect': [l, t, r, b]}

    def merge(self, other):
        # テキスト結合（カンマ重複防止）
        if self.text.endswith(',') and other.text.startswith(','):
            self.text += " " + other.text.lstrip(',').strip()
        else:
            self.text += " " + other.text

        # 座標リスト結合（矩形なので、append）
        self.bboxes.extend(other.bboxes)

    def to_dict(self):
        return {"text": self.text, "bboxes": self.bboxes}

class CitationExtractor(ABC):
    """
    基盤となる抽象クラス。
    新しいライブラリを採用するときは、このクラスを継承します。
    """

    def __init__(self):
        self.converter = None
        self.initialize()

    def __call__(self, pdf_path):
        return self.extract_references(pdf_path)
        
    @abstractmethod
    def initialize(self):
        """モデルのロードなど、一度限りの初期化処理"""
        pass

    @abstractmethod
    def extract_references(self, pdf_path):
        """PDFから参考文献リスト(CitationItemのリスト)を抽出する"""
        pass

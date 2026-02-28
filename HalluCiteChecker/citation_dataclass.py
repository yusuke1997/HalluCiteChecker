from abc import ABC, abstractmethod
from typing import List, Dict, Any,  ClassVar
from pprint import pprint
from dataclasses import dataclass, field, fields

@dataclass(slots=True)
class Citation:
    """整形済みの引用データクラス（DeLFTの全タグ網羅）"""
    # 必須・基本情報
    _id_counter: ClassVar[int] = 0
    #_id_counter: int = field(init=False, repr=False, default=0)

    # 必須・基本情報
    id: str = field(init=False)  # 初期化引数から除外し、自動採番する
    paper_name: str = ""
    
    # OCR用
    #text: str = ""
    raw_reference: str = ""
    bboxes: list = field(default_factory=list) # bboxes if bboxes else [] # list of {'page': int, 'rect': [l, t, r, b]}

    
    #raw_reference: str = ""
    arxiv:str = ""

    # DeLFTが抽出する全タグ（文字列としてそのまま格納）
    author: str = ""
    booktitle: str = ""
    collaboration: str = ""
    date: str = ""
    editor: str = ""
    institution: str = ""
    issue: str = ""
    journal: str = ""
    location: str = ""
    note: str = ""
    pages: str = ""
    publisher: str = ""
    pubnum: str = ""
    series: str = ""
    tech: str = ""
    title: str = ""
    volume: str = ""
    web: str = ""

    def __post_init__(self):
        """インスタンス化された直後に自動で呼ばれる処理"""
        # 現在のカウンターを文字列としてidに代入
        self.id = str(Citation._id_counter)
        # カウンターを1増やす
        Citation._id_counter += 1

    @classmethod
    def reset_id_counter(cls):
        """別のファイルをパースする際などに、IDを0にリセットするためのメソッド"""
        cls._id_counter = 0
    
    #def to_dict(self) -> Dict[str, Any]:
    #    """空文字やNoneを除外して辞書化"""
    #    return {k: v for k, v in self.__dict__.items() if v or isinstance(v, (int, bool))}

    def to_dict(self) -> Dict[str, Any]:
        """空文字やNoneを除外して辞書化（slots対応）"""
        out = {}
        for f in fields(self):
            v = getattr(self, f.name)
            if v is None:
                continue
            if isinstance(v, str) and v == "":
                continue
            out[f.name] = v
        return out
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Citation':
        """辞書からCitationインスタンスを復元する"""
        # データクラスに存在するフィールド名（変数名）のリストを取得
        valid_fields = {f.name for f in fields(cls)}
        
        # 辞書の中から、データクラスに存在するキーのみを抽出
        # (idや内部変数は __init__ に渡せないので除外する)
        init_data = {
            k: v for k, v in data.items() 
            if k in valid_fields and k != 'id' and not k.startswith('_')
        }
        
        # 一旦普通にインスタンス化（ここで __post_init__ が呼ばれ、新しいIDが振られる）
        instance = cls(**init_data)
        
        # もし元の辞書に 'id' が保存されていれば、自動採番されたものを上書きして復元
        if 'id' in data:
            instance.id = str(data['id'])
            
        return instance


    def merge(self, other):
        # テキスト結合（カンマ重複防止）
        if self.raw_reference.endswith(',') and other.raw_reference.startswith(','):
            self.raw_reference += " " + other.raw_reference.lstrip(',').strip()
        else:
            self.raw_reference += " " + other.raw_reference

        # 座標リスト結合（矩形なので、append）
        self.bboxes.extend(other.bboxes)

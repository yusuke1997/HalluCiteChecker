from typing import List, Union, Dict, Any
from HalluCiteChecker import Citation
from pypdf import PdfReader, PdfWriter
from pypdf.annotations import Highlight
from pypdf.generic import ArrayObject, FloatObject


# 判定キーワードを定数として外に出しておく
KEYWORDS = [
    'acl',                       # acl, naacl, eacl, aacl をカバー
    'computationallinguistics',  # 雑誌名、団体名のフルスペルをカバー
    'nlp',                       # ijcnlp, nlp全般 をカバー
    'empiricalmethodsin',        # emnlp のフルスペルをカバー
    'coling',
    'arxiv'                      # arxiv系
]

def is_candidate(citation: Union[Dict[str, Any], Citation, str]) -> bool:
    """
    単一の引用データが条件に合致するかどうかを判定する関数
    
    Args:
        citation: 辞書、ParsedCitationオブジェクト、または生の文字列
        
    Returns:
        bool: キーワードに合致すれば True、しなければ False
    """
    # 要素の型を判定して生の文字列を取り出す
    if isinstance(citation, dict):
        raw_ref = citation.get("raw_reference", "")
        arxiv_val = citation.get("arxiv", "")
    elif isinstance(citation, str):
        # 生の文字列が直接渡された場合にも対応
        raw_ref = citation
        arxiv_val = ""
    else:
        raw_ref = getattr(citation, "raw_reference", "")
        arxiv_val = getattr(citation, "arxiv", "")

    if arxiv_val:
        return True
    
    if not raw_ref:
        return False

    # 空白・ハイフンを除去して小文字化（表記揺れを吸収する最強の処理）
    cand = raw_ref.replace('-', '').replace(' ', '').lower()

    return any(kw in cand for kw in KEYWORDS)


def candidate_extraction(
    citations: List[Union[Dict[str, Any], Citation]]
) -> List[Union[Dict[str, Any], Citation]]:
    """
    引用リスト（バッチ）を処理し、該当するものだけを残す関数
    
    Args:
        citations: パース済みの辞書リスト、または ParsedCitation オブジェクトのリスト
        
    Returns:
        List: is_candidate が True になった要素だけのリスト
    """
    # 内包表記を使うことで、for文でappendするより高速かつシンプルに書けます
    return [elm for elm in citations if is_candidate(elm)]

def highlight_pdf(input_pdf_path: str, output_pdf_path: str, hallucination_list: list):
    """
    pypdf (BSDライセンス) を使用して、ハルシネーション候補にハイライトを引き別名保存する
    """
    reader = PdfReader(input_pdf_path)
    writer = PdfWriter()

    # 1. 全ページを新しいWriterにコピー
    for page in reader.pages:
        writer.add_page(page)

        # 2. 座標を元にハイライト(注釈)を書き込む
    for item in hallucination_list:
        bboxes = item.bboxes
        
        for bbox_info in bboxes:
            # ページ番号 (Doclingは1始まり、pypdfは0始まり)
            page_num = bbox_info.get('page', 1) - 1
            
            if 0 <= page_num < len(writer.pages):
                rect_coords = bbox_info.get('rect')
                
                if rect_coords:
                    x0, y0, x1, y1 = rect_coords
                    
                    # 座標の最小・最大を確実に取る (PDFの仕様に合わせる)
                    x_min, x_max = min(x0, x1), max(x0, x1)
                    y_min, y_max = min(y0, y1), max(y0, y1)
                    
                    rect = (x_min, y_min, x_max, y_max)
                    
                    # PDFの仕様上、ハイライトには「四角形」だけでなく
                    # 「4つの頂点(8つの数値)」(QuadPoints) が必要です
                    # 順番: 左下, 右下, 左上, 右上
                    quad_points = [
                        x_min, y_min, 
                        x_max, y_min, 
                        x_min, y_max, 
                        x_max, y_max
                    ]
                    
                    # Highlightオブジェクトの作成 (色は 16進数 RGB で指定)
                    # ffcc00 = やや濃い黄色, ff0000 = 赤色
                    annotation = Highlight(
                        rect=rect,
                        quad_points=ArrayObject([FloatObject(q) for q in quad_points]),
                        highlight_color="ffcc00" 
                    )
                    
                    # 該当ページに注釈を追加
                    writer.add_annotation(page_number=page_num, annotation=annotation)

    # 3. PDFの保存
    with open(output_pdf_path, "wb") as f:
        writer.write(f)
        
    print(f"Highlighted PDF saved to: {output_pdf_path}")

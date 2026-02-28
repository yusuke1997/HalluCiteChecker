import time
import re
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorOptions
from docling.datamodel.document import SectionHeaderItem

from .base import CitationExtractor
from HalluCiteChecker import Citation

class DoclingCitationExtractor(CitationExtractor):
    def __init__(self):
        self.converter = None

    def initialize(self):
        print("Initializing Docling implementation...")
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        pipeline_options.do_table_structure = False
        pipeline_options.images_scale = 1.0
        pipeline_options.generate_page_images = False
        pipeline_options.accelerator_options = AcceleratorOptions(num_threads=8, device="auto")

        format_options = {
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
        self.converter = DocumentConverter(format_options=format_options)

    def _get_bboxes(self, item):
        bboxes = []
        if hasattr(item, "prov") and item.prov:
            for prov in item.prov:
                if hasattr(prov, "bbox"):
                    bboxes.append({
                        "page": prov.page_no,
                        "rect": [prov.bbox.l, prov.bbox.t, prov.bbox.r, prov.bbox.b]
                    })
        return bboxes

    def extract_references(self, pdf_path):
        if not self.converter:
            raise RuntimeError("Parser not initialized. Call initialize() first.")

        try:
            result = self.converter.convert(pdf_path)
        except Exception as e:
            print(f"Error reading PDF: {e}")
            return []
        
        doc = result.document
        
        raw_items = []
        in_references = False

        # --- 構造データの走査 ---
        for item, level in doc.iterate_items():
            if isinstance(item, SectionHeaderItem):
                text = item.text.lower().strip()
                if any(k in text for k in ["reference", "bibliography", "参考文献"]):
                    # 開始判定
                    in_references = True
                    continue
                elif in_references:
                    # 終了判定
                    break

            if in_references and hasattr(item, "text") and item.text.strip():
                if len(item.text.strip()) > 3:
                    raw_items.append(Citation(
                        paper_name= pdf_path,
                        raw_reference=item.text.strip(),
                        bboxes=self._get_bboxes(item)
                    ))

        if not raw_items:
            print("References section not found.")
            return []

        Citation.reset_id_counter()        
        return self._post_process(raw_items)

    def _post_process(self, raw_items):
        """マージとクリーニング（ここはライブラリ依存しないため共通化も可能）"""
        
        # マージ処理
        merged = []
        current = raw_items[0]
        for next_item in raw_items[1:]:
            if not current.raw_reference.strip().endswith('.') or current.raw_reference.count('.') < 2:
                current.merge(next_item)
            else:
                merged.append(current)
                current = next_item
        merged.append(current)

        ## クリーニング
        #clean_pattern = re.compile(r'^(\[\d+\]|\d+\.|[\*\-])\s*')
        #for item in merged:
        #    item.text = clean_pattern.sub('', item.text)
            
        #return [item.to_dict() for item in merged]
        
        return merged

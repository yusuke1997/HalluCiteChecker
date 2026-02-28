import os
import argparse
from termcolor import colored
from tabulate import tabulate, tabulate_formats
import psutil

from HalluCiteChecker.CitationExtractor import DoclingCitationExtractor
from pprint import pprint
from HalluCiteChecker.CitationRecognizer import DelftCitationRecognizer
from HalluCiteChecker.CitationMatcher import FuzzCitationMatcher
from pprint import pprint
from HalluCiteChecker import utils
from HalluCiteChecker import timer

doc_parser = DoclingCitationExtractor()
doc_parser.initialize()
citation_parser = DelftCitationRecognizer(model_name='grobid-citation-BidLSTM_CRF_FEATURES')
anthology_db = FuzzCitationMatcher(db_path="yusuke1997/anthology-id-title", score_cutoff=90)
arxiv_db = FuzzCitationMatcher(db_path="yusuke1997/arxiv-id-title", score_cutoff=90)
dblp_db = FuzzCitationMatcher(db_path="yusuke1997/dblp-id-title", score_cutoff=90)

def print_memory_usage(prefix=""):
    mem = psutil.virtual_memory()
    proc = psutil.Process()
    
    print(
        f"{prefix}[RAM] Process: {proc.memory_info().rss / 1024**2:.2f} MB | "
        f"System: {mem.percent:.1f}%"
    )

def doc_parse(pdf_path):
    with timer.measure("CitationExtractor") as t:
        #pdf_path = "test/2025.acl-long.1.pdf"
        #pdf_path ='test/2024.emnlp-main.617.pdf'
        references = doc_parser.extract_references(pdf_path)
        t.set_delta_ncalls(len(references))
        
    return references

def citation_parse(citations):
    with timer.measure("CitationRecognizer") as t:
        t.set_delta_ncalls(len(citations))
        return citation_parser.parse_batch(citations, batch_size=4)

def candidate_generation(results):
    with timer.measure("CitationMatcher") as t:
        t.set_delta_ncalls(len(results))
        
        hallucination_list = utils.candidate_extraction(results)
        
        hallucination_list = anthology_db.verify(hallucination_list)
        hallucination_list = arxiv_db.verify(hallucination_list)
        hallucination_list = dblp_db.verify(hallucination_list)
        
    return hallucination_list

def process(pdf_path, output_dir=None):

    with timer.measure("total") as t:
        references = doc_parse(pdf_path)
        citations = citation_parse(references)
        t.set_delta_ncalls(len(citations))
        hallucination_list = candidate_generation(citations)

    print(pdf_path)
    for i, j in enumerate(hallucination_list):
        #print(f'[{i}]')
        pprint(j.to_dict())
        print('-'*40)

    #print(len(references))
    print(len(citations))
    if len(hallucination_list) == 0:
        print(colored("All Clear!", "green"))
    else:
        print(len(hallucination_list))
    # print('='*40)

    # pdfをハイライトする。該当箇所がない場合はスキップ
    if len(hallucination_list) > 0 and output_dir is not None:
        os.makedirs(output_dir, exist_ok=True)
        filename = os.path.basename(pdf_path)
        output_path = os.path.join(output_dir, filename)
        print(f"[FOUND] {len(hallucination_list)} hallucinated citation(s) in: {pdf_path}")
        print(f"[SAVED] Highlighted PDF saved to: {output_path}")
        utils.highlight_pdf(pdf_path, output_path, hallucination_list)

    print('='*40)
    
def main():
    parser = argparse.ArgumentParser(description="Hallucinated Citation Checker Pipeline")
    # nargs='+' とすることで、1つ以上の引数をリストとして受け取れる
    parser.add_argument(
        "-i", "--inputs", 
        nargs='+', 
        required=True, 
        help="Path(s) to PDF file(s) to process. You can pass multiple files separated by space."
    )

    parser.add_argument(
        "-o", "--output",
        default=None,
        help="Output directory (optional). If not specified, saving is skipped."
    )

    parser.add_argument(
        "--quiet",
        default=False,
        help="Output directory (optional). If not specified, saving is skipped."
    )
    
    args = parser.parse_args()

    for pdf_path in args.inputs:
        process(pdf_path, args.output)

    if not args.quiet:
        statistics = timer.aggregate().result(len(args.inputs))
        table = tabulate(
            statistics,
            headers="keys",
            tablefmt="rounded_outline",
            floatfmt=f".1f",
        )
        print(table)
        print_memory_usage(prefix="[TOTAL] ")
        
if __name__ == "__main__":
    main()

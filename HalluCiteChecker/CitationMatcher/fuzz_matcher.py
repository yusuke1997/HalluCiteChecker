import numpy as np
import pandas as pd
from rapidfuzz import process, fuzz
from typing import List, Dict, Any
from .base import BaseCitationMatcher
from HalluCiteChecker import Citation

class FuzzCitationMatcher(BaseCitationMatcher):

    def verify(self, citations: List[Citation]) -> List[Citation]:
        # オブジェクトの title 属性に値が入っているものだけを対象とする
        queries = [cit for cit in citations if getattr(cit, 'title', '')]

        if not queries:
            return []

        # cit.title で直接アクセスできるので非常にクリーン
        queries_norm = [self._normalize(q.title) for q in queries]

        matches = process.cdist(
            queries_norm,
            self.titles_norm,
            scorer=fuzz.ratio,
            score_cutoff=self.score_cutoff,
            dtype=np.uint8,
            workers=self.workers
        )

        bad_indices = np.where(matches.max(axis=1) == 0)[0]
        return [queries[i] for i in bad_indices]


import json
import os
from typing import List, Dict, Set
from app.benchmark.schemas import BenchmarkRecord

class BenchmarkValidator:
    def __init__(self, dataset_path: str, index_metadata_path: str):
        self.dataset_path = dataset_path
        self.index_metadata_path = index_metadata_path

    def validate(self) -> List[str]:
        errors = []
        
        if not os.path.exists(self.dataset_path):
            return ["Dataset file does not exist."]
            
        try:
            with open(self.dataset_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            return [f"Failed to load dataset: {str(e)}"]

        if not os.path.exists(self.index_metadata_path):
            return [f"Index metadata missing at {self.index_metadata_path}"]
            
        with open(self.index_metadata_path, "r", encoding="utf-8") as f:
            chunks = json.load(f)
            valid_chunk_ids = {c["chunk_id"] for c in chunks}
            valid_pages = {c.get("start_page", -1) for c in chunks}
            valid_pages.update({c.get("end_page", -1) for c in chunks})

        seen_qids = set()
        
        valid_categories = {"DIRECT_FACT", "MULTI_HOP", "METHOD", "COMPARATIVE", "QUANTITATIVE", "UNANSWERABLE", "CONTRADICTION", "MULTILINGUAL"}
        valid_statuses = {"SUPPORTED", "PARTIALLY_SUPPORTED", "INSUFFICIENT_EVIDENCE", "CONFLICTED"}

        for i, item in enumerate(data):
            try:
                record = BenchmarkRecord(**item)
            except Exception as e:
                errors.append(f"Record {i} invalid schema: {str(e)}")
                continue

            # Unique QIDs
            if record.question_id in seen_qids:
                errors.append(f"Duplicate question_id: {record.question_id}")
            seen_qids.add(record.question_id)
            
            # valid document
            if record.document_id != "test_document":
                errors.append(f"{record.question_id}: Invalid document_id {record.document_id}")
                
            # valid categories
            if record.category not in valid_categories:
                errors.append(f"{record.question_id}: Invalid category {record.category}")
                
            # valid statuses
            if record.expected_status not in valid_statuses:
                errors.append(f"{record.question_id}: Invalid expected_status {record.expected_status}")
                
            # supporting chunks exist
            for chunk_id in record.supporting_chunk_ids:
                if chunk_id not in valid_chunk_ids:
                    errors.append(f"{record.question_id}: Supporting chunk {chunk_id} not found in index")
                    
            # unanswerable logic
            if not record.answerability:
                if record.expected_status != "INSUFFICIENT_EVIDENCE":
                    errors.append(f"{record.question_id}: Unanswerable question must have expected_status=INSUFFICIENT_EVIDENCE")
                if record.expected_answer is not None and len(record.expected_answer.strip()) > 0:
                    errors.append(f"{record.question_id}: Unanswerable question should not have an expected answer")
            else:
                if not record.supporting_chunk_ids and record.expected_status != "CONFLICTED":
                    errors.append(f"{record.question_id}: Answerable non-conflicted question must have supporting_chunk_ids")
                    
            # check page bounds
            for p in record.supporting_pages:
                if p not in valid_pages and p > 0:
                    errors.append(f"{record.question_id}: Invalid page {p}")

        return errors

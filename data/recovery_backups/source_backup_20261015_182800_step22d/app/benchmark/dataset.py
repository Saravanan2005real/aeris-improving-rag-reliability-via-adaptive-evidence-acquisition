import json
import os
from typing import List, Optional
from app.benchmark.schemas import BenchmarkRecord

class BenchmarkDataset:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.records: List[BenchmarkRecord] = []
        if os.path.exists(file_path):
            self.load()

    def load(self):
        with open(self.file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            self.records = [BenchmarkRecord(**item) for item in data]

    def save(self):
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump([r.model_dump() for r in self.records], f, indent=2)

    def add_record(self, record: BenchmarkRecord):
        self.records.append(record)

    def get_record(self, question_id: str) -> Optional[BenchmarkRecord]:
        for r in self.records:
            if r.question_id == question_id:
                return r
        return None

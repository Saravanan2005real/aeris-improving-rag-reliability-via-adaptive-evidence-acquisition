import json
import os
import time
from typing import List
from datetime import datetime

from app.ablation.schemas import AblationVariant, AblationResult
from app.ablation.config import get_config_for_variant
from app.controller.controller import AERISController
from app.controller.schemas import ControllerRequest
from app.benchmark.dataset import BenchmarkDataset
from app.performance_cache import aeris_cache

class AblationRunner:
    def __init__(self, controller: AERISController):
        self.controller = controller

    def run_experiment(
        self,
        benchmark_path: str,
        output_path: str,
        start_idx: int = 0,
        end_idx: int = None,
        experiment_id: str = None,
        variants_to_run: List[AblationVariant] = None,
        question_ids_to_run: List[str] = None,
    ):
        dataset = BenchmarkDataset(benchmark_path)
        
        if question_ids_to_run is not None:
            records = [r for r in dataset.records if r.question_id in question_ids_to_run]
        elif end_idx is not None:
            records = dataset.records[start_idx:end_idx]
        else:
            records = dataset.records[start_idx:]
            
        variants = variants_to_run if variants_to_run is not None else list(AblationVariant)
            
        results: List[dict] = []
        completed_pairs = set()
        
        if os.path.exists(output_path):
            with open(output_path, "r", encoding="utf-8") as f:
                try:
                    results = json.load(f)
                    for res in results:
                        completed_pairs.add((res["variant"], res["question_id"]))
                except json.JSONDecodeError:
                    pass
                    
        if results and "experiment_id" in results[0]:
            experiment_id = results[0]["experiment_id"]
        elif not experiment_id:
            experiment_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
        manifest_path = output_path.replace(".json", "_manifest.json")
        if not os.path.exists(manifest_path):
            manifest = {
                "experiment_id": experiment_id,
                "timestamp": datetime.now().isoformat(),
                "model_name": "llama3.2",
                "benchmark_path": benchmark_path,
                "benchmark_question_count": len(records),
                "variant_list": [v.value for v in variants],
                "expected_run_count": len(variants) * len(records)
            }
            os.makedirs(os.path.dirname(manifest_path), exist_ok=True)
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)
        
        print(f"Starting Ablation Experiment: {experiment_id}")
        print(f"Total questions: {len(records)}")
        print(f"Total variants: {len(variants)}")
        print(f"Completed pairs: {len(completed_pairs)}")
        
        total_runs = len(variants) * len(records)
        run_count = 0
        
        for variant in variants:
            print(f"\n========================================")
            print(f"Running Variant: {variant.value}")
            print(f"========================================")
            
            # Cache isolation
            aeris_cache.cache_file = f"data/cache_{experiment_id}_{variant.value}.json"
            aeris_cache._load()
            
            config = get_config_for_variant(variant)
            
            for i, record in enumerate(records):
                run_count += 1
                
                if (variant.value, record.question_id) in completed_pairs:
                    print(f"  [{run_count:03d}/{total_runs}] {variant.value} / {record.question_id} (SKIPPED)")
                    continue
                    
                print(f"  [{run_count:03d}/{total_runs}] {variant.value} / {record.question_id} ... ", end="", flush=True)
                
                import app.utils.diagnostics as diag
                diag.current_question_id.set(record.question_id)
                diag.current_variant.set(variant.value)
                
                req = ControllerRequest(
                    document_id=record.document_id,
                    question=record.question,
                    config=config
                )
                
                start_time = time.time()
                try:
                    result = self.controller.run(req)
                    latency = time.time() - start_time
                    
                    expected_chunks = set(record.supporting_chunk_ids)
                    actual_retrieved = set(getattr(result, "retrieved_chunk_ids", []))
                    cited_chunks = set(result.supporting_chunk_ids)
                    
                    # Retriever metrics (evaluated on actual_retrieved)
                    retriever_hit = len(expected_chunks.intersection(actual_retrieved)) > 0
                    retriever_recall = 0.0
                    if expected_chunks:
                        retriever_recall = len(expected_chunks.intersection(actual_retrieved)) / len(expected_chunks)

                    # Citation metrics (evaluated on cited_chunks)
                    citation_hit = len(expected_chunks.intersection(cited_chunks)) > 0
                    citation_recall = 0.0
                    if expected_chunks:
                        citation_recall = len(expected_chunks.intersection(cited_chunks)) / len(expected_chunks)

                    # Provenance defect check
                    provenance_defects = getattr(result, "provenance_defects", [])
                    if not provenance_defects:
                        provenance_defects = [cid for cid in cited_chunks if cid not in actual_retrieved]
                        
                    stage_statuses = {str(stage.stage.value): str(stage.status.value) for stage in result.stages}
                    stage_latencies = {str(stage.stage.value): float(stage.latency_seconds) for stage in result.stages}
                    
                    verified_count = next((s.output_count for s in result.stages if s.stage.value == "VERIFICATION"), 0)
                    selected_count = next((s.output_count for s in result.stages if s.stage.value == "SELECTIVE_VERIFICATION"), 0)
                    contra_count = next((s.output_count for s in result.stages if s.stage.value == "CONTRADICTION"), 0)
                    cross_count = next((s.output_count for s in result.stages if s.stage.value == "CROSS_LINGUAL"), 0)
                    ev_count = next((s.output_count for s in result.stages if s.stage.value == "RETRIEVAL"), 0)
                    
                    error_msg = None
                    if result.status.value == "FAILED" and result.stages:
                        last_stage = result.stages[-1]
                        if last_stage.stage.value == "FAILED":
                            error_msg = last_stage.message
                            print(f"\nInternal Controller Error: {error_msg}")
                            
                    ablation_res = AblationResult(
                        experiment_id=experiment_id,
                        variant=variant,
                        question_id=record.question_id,
                        question=record.question,
                        document_id=record.document_id,
                        question_type=record.category,
                        expected_answerability=record.answerability,
                        final_status=str(result.answer_status) if result.answer_status else str(result.status.value),
                        final_confidence=result.answer_confidence,
                        answer=result.final_answer,
                        supporting_chunk_ids=result.supporting_chunk_ids,
                        supporting_claim_ids=result.supporting_claim_ids,
                        expected_chunk_ids=record.supporting_chunk_ids,
                        retrieved_chunk_ids=list(getattr(result, "retrieved_chunk_ids", [])),
                        retriever_hit=retriever_hit,
                        retriever_recall=retriever_recall,
                        citation_hit=citation_hit,
                        citation_recall=citation_recall,
                        evidence_hit=citation_hit,
                        evidence_recall=citation_recall,
                        provenance_defects=provenance_defects,
                        evidence_count=ev_count,
                        claim_count=result.claim_count,
                        verified_claim_count=verified_count,
                        selected_verification_count=selected_count,
                        contradiction_count=contra_count,
                        cross_lingual_count=cross_count,
                        latency_seconds=latency,
                        stage_latencies=stage_latencies,
                        stage_statuses=stage_statuses,
                        error=error_msg,
                        timestamp=datetime.now().isoformat(),
                        metadata=result.metadata or {},
                        is_answerable=record.answerability,
                        success=(result.status.value == "COMPLETED" or result.status.value == "SUPPORTED")
                    )
                    
                    results.append(ablation_res.model_dump())
                    print(f"Done ({latency:.2f}s) -> {result.status.value}")
                    
                except Exception as e:
                    latency = time.time() - start_time
                    ablation_res = AblationResult(
                        experiment_id=experiment_id,
                        variant=variant,
                        question_id=record.question_id,
                        question=record.question,
                        document_id=record.document_id,
                        question_type=record.category,
                        expected_answerability=record.answerability,
                        final_status="FAILED",
                        retrieved_chunk_ids=[],
                        retriever_hit=False,
                        retriever_recall=0.0,
                        citation_hit=False,
                        citation_recall=0.0,
                        evidence_hit=False,
                        evidence_recall=0.0,
                        provenance_defects=[],
                        latency_seconds=latency,
                        error=str(e),
                        timestamp=datetime.now().isoformat(),
                        is_answerable=record.answerability,
                        success=False
                    )
                    results.append(ablation_res.model_dump())
                    print(f"FAILED ({latency:.2f}s) -> {e}")
                    
                temp_path = f"{output_path}.tmp"
                with open(temp_path, "w", encoding="utf-8") as f:
                    json.dump(results, f, indent=2)
                os.replace(temp_path, output_path)
                    
        print(f"\nDONE! Saved {len(results)} records to {output_path}")

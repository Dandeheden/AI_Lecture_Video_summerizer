"""
Reproducible Empirical Experiment Runner for LectureAI.
Compares:
1. Method A: Single-Pass Direct Summarization
2. Method B: Chunk-Based Hierarchical Summarization with Sentence Boundary Preservation

Evaluates on benchmark educational lectures using:
- ROUGE-1, ROUGE-2, ROUGE-L (Precision, Recall, F1)
- Inference Execution Time (seconds)
- Question Generation Metrics: Distinct Options Rate, Groundedness, Duplicate Rate
Saves real measured outputs to research/results/.
"""

import sys
import json
import time
import csv
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from research.evaluation import (
    compute_rouge_n,
    compute_rouge_l,
    compute_word_error_rate,
    evaluate_question_generation,
)
from backend.app.services.summarization_service import (
    generate_nlp_extractive_summary,
    generate_lecture_summaries,
    chunk_text_by_sentences,
)
from backend.app.services.quiz_service import generate_mcqs_from_text


def run_benchmarks():
    data_path = PROJECT_ROOT / "research" / "experiments" / "sample_lectures.json"
    results_dir = PROJECT_ROOT / "research" / "results"
    results_dir.mkdir(parents=True, exist_ok=True)

    if not data_path.exists():
        raise FileNotFoundError(f"Benchmark dataset not found at {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        lectures = json.load(f)

    print(f"Loaded {len(lectures)} benchmark educational lectures.")
    print("=" * 70)

    summary_records = []
    qg_records = []

    for lec in lectures:
        lec_id = lec["id"]
        title = lec["title"]
        transcript = lec["transcript"]
        ref_summary = lec["reference_summary"]

        print(f"\nEvaluating Lecture: '{title}' ({lec_id})")

        # ---------------- Method A: Single-Pass Direct Summarization ----------------
        t0 = time.perf_counter()
        # Direct extraction without sentence-aware chunking
        method_a_summary = generate_nlp_extractive_summary(transcript, target_ratio=0.25, min_sentences=2, max_sentences=4)
        t_a = round(time.perf_counter() - t0, 4)

        r1_a = compute_rouge_n(method_a_summary, ref_summary, n=1)
        r2_a = compute_rouge_n(method_a_summary, ref_summary, n=2)
        rl_a = compute_rouge_l(method_a_summary, ref_summary)

        summary_records.append({
            "lecture_id": lec_id,
            "title": title,
            "method": "Single-Pass Direct",
            "time_sec": t_a,
            "rouge1_f1": r1_a["f1"],
            "rouge1_p": r1_a["precision"],
            "rouge1_r": r1_a["recall"],
            "rouge2_f1": r2_a["f1"],
            "rouge2_p": r2_a["precision"],
            "rouge2_r": r2_a["recall"],
            "rougel_f1": rl_a["f1"],
            "rougel_p": rl_a["precision"],
            "rougel_r": rl_a["recall"],
        })

        # ---------------- Method B: Hierarchical Chunk-Based Summarization ----------------
        t0 = time.perf_counter()
        summ_b_res = generate_lecture_summaries(transcript)
        method_b_summary = summ_b_res["detailed_summary"]
        t_b = round(time.perf_counter() - t0, 4)

        r1_b = compute_rouge_n(method_b_summary, ref_summary, n=1)
        r2_b = compute_rouge_n(method_b_summary, ref_summary, n=2)
        rl_b = compute_rouge_l(method_b_summary, ref_summary)

        summary_records.append({
            "lecture_id": lec_id,
            "title": title,
            "method": "Hierarchical Chunk-Based",
            "time_sec": t_b,
            "rouge1_f1": r1_b["f1"],
            "rouge1_p": r1_b["precision"],
            "rouge1_r": r1_b["recall"],
            "rouge2_f1": r2_b["f1"],
            "rouge2_p": r2_b["precision"],
            "rouge2_r": r2_b["recall"],
            "rougel_f1": rl_b["f1"],
            "rougel_p": rl_b["precision"],
            "rougel_r": rl_b["recall"],
        })

        print(f"  [Method A - Single Pass]    ROUGE-1 F1: {r1_a['f1']:.4f} | ROUGE-2 F1: {r2_a['f1']:.4f} | ROUGE-L F1: {rl_a['f1']:.4f} ({t_a}s)")
        print(f"  [Method B - Chunk-Based]    ROUGE-1 F1: {r1_b['f1']:.4f} | ROUGE-2 F1: {r2_b['f1']:.4f} | ROUGE-L F1: {rl_b['f1']:.4f} ({t_b}s)")

        # ---------------- Question Generation Evaluation ----------------
        mcqs = generate_mcqs_from_text(transcript, method_b_summary, num_questions=5, difficulty="Medium")
        qg_eval = evaluate_question_generation(mcqs, transcript)

        qg_records.append({
            "lecture_id": lec_id,
            "title": title,
            "questions_generated": qg_eval["total_questions"],
            "distinct_options_rate": qg_eval["distinct_options_rate"],
            "duplicate_rate": qg_eval["duplicate_question_rate"],
            "grounded_consistency_rate": qg_eval["grounded_consistency_rate"],
        })
        print(f"  [MCQ Generation]            Count: {qg_eval['total_questions']} | 4-Options Rate: {qg_eval['distinct_options_rate'] * 100:.1f}% | Grounded: {qg_eval['grounded_consistency_rate'] * 100:.1f}%")

    # Write summary_metrics.csv
    summary_csv = results_dir / "summary_metrics.csv"
    with open(summary_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summary_records[0].keys()))
        writer.writeheader()
        writer.writerows(summary_records)
    print(f"\nSaved summarization benchmark results to: {summary_csv}")

    # Write qg_metrics.csv
    qg_csv = results_dir / "qg_metrics.csv"
    with open(qg_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(qg_records[0].keys()))
        writer.writeheader()
        writer.writerows(qg_records)
    print(f"Saved QG benchmark results to: {qg_csv}")

    # Compute Averages
    methods = ["Single-Pass Direct", "Hierarchical Chunk-Based"]
    avg_report = {}
    for m in methods:
        recs = [r for r in summary_records if r["method"] == m]
        avg_report[m] = {
            "avg_rouge1_f1": round(sum(r["rouge1_f1"] for r in recs) / len(recs), 4),
            "avg_rouge2_f1": round(sum(r["rouge2_f1"] for r in recs) / len(recs), 4),
            "avg_rougel_f1": round(sum(r["rougel_f1"] for r in recs) / len(recs), 4),
            "avg_latency_sec": round(sum(r["time_sec"] for r in recs) / len(recs), 4),
        }

    qg_report = {
        "avg_distinct_options_rate": round(sum(r["distinct_options_rate"] for r in qg_records) / len(qg_records), 4),
        "avg_grounded_rate": round(sum(r["grounded_consistency_rate"] for r in qg_records) / len(qg_records), 4),
        "avg_duplicate_rate": round(sum(r["duplicate_rate"] for r in qg_records) / len(qg_records), 4),
    }

    full_report = {
        "experiment_name": "Comparative Evaluation of Lecture Summarization & Grounded Question Generation",
        "benchmark_dataset": "Educational Lecture Subset (CS482, CS584, CS401)",
        "sample_count": len(lectures),
        "summarization_comparison": avg_report,
        "question_generation_metrics": qg_report,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    report_json = results_dir / "experiment_report.json"
    with open(report_json, "w", encoding="utf-8") as f:
        json.dump(full_report, f, indent=2)
    print(f"Saved full experiment report to: {report_json}")
    print("\nBenchmark experiment execution completed successfully.")


if __name__ == "__main__":
    run_benchmarks()

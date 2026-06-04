# Zakres PR: `feature/full-comparison-pipeline`



## Bazuje na



- `main` + niezmergowany PR #2 (ParEGO / BoTorch)



## Co ten PR dodaje



| Element raportu | Implementacja |

|-----------------|---------------|

| ParEGO vs MO-CMA-ES | `algorithms/parego.py`, configi porównawcze |

| 55 funkcji BBOB-BIOBJ | `function_ids: all`, `configs/full_benchmark.yaml` |

| D ∈ {2, 3, 5, 10} | `full_benchmark.yaml`, `medium_comparison.yaml` |

| Budżet mały (10D–100D) / duży (1000D+) | mnożniki 10–1000, `full_benchmark.yaml` (100D), `full_benchmark_large.yaml` (1000D) |

| 30 niezależnych uruchomień | `configs/seeds_full.csv` |

| ERT, data profiles | `analyze_results.py`, `analysis/data_profiles.py` |

| Sweep budżetu | `run_budget_sweep.py` |

| Resume / checkpoint | `--resume`, zapis przyrostowy CSV |

| Pełny runner 55 funkcji | `run_full_benchmark.py` (chunki po 5 funkcjach) |

| Logowanie COCO → cocopp | `coco_logging.py`, `coco_output_dir` w YAML |

| Raport cocopp | `generate_cocopp_report.py` |

| Friedman, Wilcoxon, Holm, Wilson | `analysis/statistics.py`, `run_statistics.py` |

| Orchestrator całego studium | `run_study.py` + `configs/study_plan.yaml` |

| Testy pytest | `tests/` (config, metryki, statystyka) |



## Uruchomienie

Szczegółowa instrukcja: [`URUCHOMIENIE.md`](URUCHOMIENIE.md).

```bash

pip install -e ".[dev]"



# Pilot / średni zakres

python scripts/run_experiment.py --config configs/pilot_comparison.yaml --resume



# Pełny benchmark 55 funkcji (wznawialny, chunki)

python scripts/run_full_benchmark.py --config configs/full_benchmark.yaml --resume --dry-run

python scripts/run_full_benchmark.py --config configs/full_benchmark.yaml --resume



# Cały plan z raportu (fazy po kolei)

python scripts/run_study.py --plan configs/study_plan.yaml --dry-run

python scripts/run_study.py --phase pilot



# Analiza + statystyka + cocopp

python scripts/analyze_results.py --input results/raw/full_comparison_b100.csv

python scripts/run_statistics.py --input results/raw/full_comparison_b100.csv

python scripts/generate_cocopp_report.py --data-dir exdata/coco/full_b100

```



## Szacowany czas pełnego benchmarku



`full_benchmark.yaml`: 2 algorytmy × 30 seedów × 55 funkcji × 4 wymiary ≈ **13 200** uruchomień problemu (przy budżecie 100×D). Uruchamiaj nocą; `--resume` pozwala kontynuować po przerwaniu.



## Poza zakresem



- Pełny SMAC3 / GPflowOpt zamiast ParEGO

- Automatyczny eksport LaTeX raportu końcowego (dane + wykresy są w `results/processed/`)



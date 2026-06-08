# WAE project 4: MO-CMA-ES vs EGO

Projekt z przedmiotu Wstep do algorytmow ewolucyjnych.

Temat: porownanie dzialania algorytmu MO-CMA-ES z algorytmem EGO na benchmarku BBOB-BIOBJ z frameworku COCO.

Klasyczny EGO jest algorytmem jednocelowym, dlatego w tym projekcie dla benchmarku bi-objective stosowany jest ParEGO, czyli wielokryterialny wariant EGO oparty na scalarizacji celow.

## Struktura projektu

- `docs/` - dokumentacja projektowa ([instrukcja uruchomienia](docs/URUCHOMIENIE.md)).
- `src/` - kod zrodlowy projektu.
- `scripts/` - skrypty uruchomieniowe.
- `configs/` - konfiguracje eksperymentow.
- `results/` - wyniki eksperymentow generowane lokalnie.

## Setup

Projekt jest przygotowany jako pakiet Pythonowy. Zalecana wersja Pythona to 3.10 lub nowsza.

Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## COCO check

Po instalacji zaleznosci mozna sprawdzic, czy backend COCO dla `bbob-biobj` jest dostepny:

```bash
python scripts/check_coco_install.py
```

## MO-CMA-ES smoke experiment

Minimalny eksperyment MO-CMA-ES jest zdefiniowany w `configs/smoke.yaml`.

Uruchomienie:

```bash
python scripts/run_experiment.py --config configs/smoke.yaml
```

Wyniki surowe sa zapisywane do:

```text
results/raw/mo_cma_es_smoke.csv
```

Podsumowanie i wykres frontu:

```bash
python scripts/summarize_results.py --input results/raw/mo_cma_es_smoke.csv
```

Pliki przetworzone sa zapisywane w `results/processed/`.

## Comparison smoke experiment

Porownanie MO-CMA-ES i ParEGO jest zdefiniowane w `configs/comparison_smoke.yaml`.

Uruchomienie:

```bash
python scripts/run_experiment.py --config configs/comparison_smoke.yaml
```

Wyniki surowe sa zapisywane do:

```text
results/raw/comparison_smoke.csv
```

Podsumowanie i wykres frontow:

```bash
python scripts/summarize_results.py --input results/raw/comparison_smoke.csv
```

Najwazniejsze pliki wynikowe:

- `results/raw/comparison_smoke.csv` - wszystkie ewaluacje obu algorytmow.
- `results/processed/comparison_smoke_summary.csv` - tabela podsumowania.
- `results/processed/comparison_smoke_fronts.png` - wykres punktow i frontow niezdominowanych.

## Analiza porownawcza (ERT, data profiles)

```bash
python scripts/analyze_results.py --input results/raw/comparison_smoke.csv
```

Generuje m.in.: `*_ert.csv`, `*_data_profiles.csv`, wykresy profili i boxploty ERT.

## Sweep budzetu (10D, 50D, 100D, ...)

```bash
python scripts/run_budget_sweep.py --config configs/comparison_smoke.yaml --multipliers 10,50,100
python scripts/analyze_results.py --input results/raw/budget_sweep
```

## Konfiguracje eksperymentow

| Plik | Opis |
|------|------|
| `configs/comparison_smoke.yaml` | Minimalny porownanie 2 algorytmow |
| `configs/pilot_comparison.yaml` | Pilot 3 funkcje, D=2 |
| `configs/medium_comparison.yaml` | 10 funkcji, D=2,3,5, budzet 100D |
| `configs/full_benchmark.yaml` | **55 funkcji**, D=2,3,5,10, 30 seedow, budzet 100D, COCO log |
| `configs/full_benchmark_large.yaml` | Jak wyzej, budzet 1000D |
| `configs/study_plan.yaml` | Orchestrator wszystkich faz z raportu |

## Pelny benchmark (55 funkcji BBOB-BIOBJ)

Uruchomienie wznawialne, podzielone na chunki po 5 funkcjach:

```bash
python scripts/run_full_benchmark.py --config configs/full_benchmark.yaml --resume --dry-run
python scripts/run_full_benchmark.py --config configs/full_benchmark.yaml --resume
```

Wyniki: `results/raw/full_comparison_b100.csv`, logi COCO: `exdata/coco/full_b100/`.

## Caly plan eksperymentow

```bash
python scripts/run_study.py --plan configs/study_plan.yaml --dry-run
python scripts/run_study.py --phase full_small_budget
```

## Statystyka (Friedman, Wilcoxon, Holm)

```bash
python scripts/run_statistics.py --input results/raw/pilot_comparison.csv
```

## Raport COCO (cocopp)

Po eksperymencie z `coco_output_dir` w YAML:

```bash
python scripts/generate_cocopp_report.py --data-dir exdata/coco/full_b100
```

## Testy

```bash
pytest tests/ -v
```

**Pelna instrukcja uruchomienia:** [`docs/URUCHOMIENIE.md`](docs/URUCHOMIENIE.md)  
Szczegoly zakresu PR: `docs/PR_SCOPE.md`.

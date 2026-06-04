# Instrukcja uruchomienia — MO-CMA-ES vs ParEGO (BBOB-BIOBJ)

Przewodnik krok po kroku: od instalacji do pełnego benchmarku (55 funkcji) i analizy wyników.

---

## 1. Wymagania

- Python **3.10+**
- Windows lub Linux
- Dla pełnego benchmarku: dużo czasu CPU (szacunkowo wiele godzin–dni przy 13 200 uruchomieniach)

---

## 2. Instalacja

W katalogu repozytorium:

**Windows (PowerShell):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

**Linux:**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

---

## 3. Sprawdzenie COCO

```bash
python scripts/check_coco_install.py
```

Oczekiwany komunikat: `COCO backend OK`.  
Jeśli błąd importu: `python -m pip install coco-experiment cocopp comocma botorch`.

---

## 4. Szybki test (smoke)

### 4.1 Tylko MO-CMA-ES

```bash
python scripts/run_experiment.py --config configs/smoke.yaml
python scripts/summarize_results.py --input results/raw/mo_cma_es_smoke.csv
```

### 4.2 Porównanie MO-CMA-ES + ParEGO

```bash
python scripts/run_experiment.py --config configs/comparison_smoke.yaml
python scripts/summarize_results.py --input results/raw/comparison_smoke.csv
```

Wyniki: `results/raw/*.csv`, wykresy: `results/processed/`.

---

## 5. Eksperymenty pośrednie (przed pełnym benchmarkiem)

| Cel | Config | Polecenie |
|-----|--------|-----------|
| Pilot (3 funkcje, D=2) | `pilot_comparison.yaml` | `python scripts/run_experiment.py --config configs/pilot_comparison.yaml --resume` |
| Średni (10 funkcji, D=2,3,5) | `medium_comparison.yaml` | `python scripts/run_experiment.py --config configs/medium_comparison.yaml --resume` |

Analiza po zakończeniu:

```bash
python scripts/analyze_results.py --input results/raw/pilot_comparison.csv
python scripts/run_statistics.py --input results/raw/pilot_comparison.csv
```

---

## 6. Sweep budżetu (10D, 50D, 100D, 1000D)

```bash
python scripts/run_budget_sweep.py --config configs/medium_comparison.yaml --multipliers 10,50,100,1000 --resume
python scripts/analyze_results.py --input results/raw/budget_sweep
python scripts/run_statistics.py --input results/raw/budget_sweep
```

---

## 7. Pełny benchmark — 55 funkcji BBOB-BIOBJ

Konfiguracja: `configs/full_benchmark.yaml`

- 55 funkcji (`function_ids: all`)
- wymiary **D ∈ {2, 3, 5, 10}**
- **30** niezależnych seedów (`seeds_full.csv`)
- budżet **100×D** ewaluacji
- logowanie do formatu COCO (`exdata/coco/full_b100/`)

### 7.1 Podgląd zakresu (bez liczenia)

```bash
python scripts/run_full_benchmark.py --dry-run
```

Wyświetli liczbę chunków i runów (~13 200 łącznie).

### 7.2 Uruchomienie właściwe (wznawialne)

```bash
python scripts/run_full_benchmark.py --config configs/full_benchmark.yaml --resume
```

- Wyniki CSV: `results/raw/full_comparison_b100.csv`
- Po przerwaniu (Ctrl+C, restart komputera) uruchom **to samo polecenie** z `--resume` — pominięte zostaną już zapisane runy.
- Domyślnie chunki po **5 funkcjach** (11 chunków). Jeden chunk:

```bash
python scripts/run_full_benchmark.py --chunk-index 0 --resume
```

### 7.3 Duży budżet (1000×D)

```bash
python scripts/run_full_benchmark.py --config configs/full_benchmark_large.yaml --resume
```

Wyniki: `results/raw/full_comparison_b1000.csv`.

---

## 8. Cały plan eksperymentów (jednym skryptem)

Plik planu: `configs/study_plan.yaml` (pilot → medium → sweep → full).

```bash
# Podgląd kolejności faz
python scripts/run_study.py --dry-run

# Jedna faza, np. pilot
python scripts/run_study.py --phase pilot

# Wszystkie fazy (długo!)
python scripts/run_study.py
```

Analiza po każdej fazie jest uruchamiana automatycznie (chyba że `--skip-analysis`).

---

## 9. Analiza wyników (raport)

Dla dowolnego pliku CSV z eksperymentu:

```bash
python scripts/analyze_results.py --input results/raw/full_comparison_b100.csv
```

Powstaje m.in. w `results/processed/`:

- `*_final_hypervolume.csv`
- `*_ert.csv`, `*_data_profiles.csv`
- wykresy PNG (profile, boxploty)

Statystyka (Wilcoxon, Holm, Wilson — przy 2 algorytmach Friedman jest pomijany):

```bash
python scripts/run_statistics.py --input results/raw/full_comparison_b100.csv
python scripts/run_statistics.py --input results/raw/full_comparison_b100.csv --metric ert
```

---

## 10. Raport COCO (cocopp)

Wymaga wcześniejszego eksperymentu z `coco_output_dir` w YAML (np. `full_benchmark.yaml`).

```bash
python scripts/generate_cocopp_report.py --data-dir exdata/coco/full_b100
```

Raport HTML/LaTeX generuje się w katalogu roboczym (standard cocopp).

---

## 11. Testy automatyczne

```bash
pytest tests/ -v
```

---

## 12. Typowe problemy

| Problem | Rozwiązanie |
|---------|-------------|
| Brak modułu `cocoex` / `comocma` / `botorch` | `pip install -e ".[dev]"` |
| Przerwany benchmark | Ponów z `--resume` |
| Za długi czas | Zacznij od `pilot_comparison.yaml` lub `--chunk-index N` |
| Pusty katalog cocopp | Najpierw uruchom eksperyment z `coco_output_dir` w configu |

---

## 13. Mapa plików wynikowych

| Etap | Lokalizacja |
|------|-------------|
| Surowe ewaluacje | `results/raw/<nazwa_eksperymentu>.csv` |
| Tabele i wykresy | `results/processed/` |
| Logi COCO | `exdata/coco/<podfolder>/` |
| Zakres PR / funkcji | `docs/PR_SCOPE.md` |

---

## Skrócona ścieżka „od zera do raportu”

```bash
pip install -e ".[dev]"
python scripts/check_coco_install.py
python scripts/run_experiment.py --config configs/comparison_smoke.yaml
python scripts/summarize_results.py --input results/raw/comparison_smoke.csv
python scripts/analyze_results.py --input results/raw/comparison_smoke.csv
```

Pełny benchmark (nocny run):

```bash
python scripts/run_full_benchmark.py --resume
python scripts/analyze_results.py --input results/raw/full_comparison_b100.csv
python scripts/run_statistics.py --input results/raw/full_comparison_b100.csv
python scripts/generate_cocopp_report.py --data-dir exdata/coco/full_b100
```

# WAE project 4: MO-CMA-ES vs EGO

Projekt z przedmiotu Wstep do algorytmow ewolucyjnych.

Temat: porownanie dzialania algorytmu MO-CMA-ES z algorytmem EGO na benchmarku BBOB-BIOBJ z frameworku COCO.

## Struktura projektu

- `docs/` - dokumentacja projektowa.
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

## Smoke experiment

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

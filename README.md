# MML1 – HW2: Zpracování dat, split a benchmark

V rámci klíče +16, může složení skupiny (class a spec hráčů) předpovědět dobu průchodu Pit of Saron nad rámec toho, co vysvětluje průměrný item level skupiny?
## Popis

Regresní úloha postavená na datech z Raider.IO API. Každý záznam představuje jeden run (tank, healer, 3x dps) s atributy skupiny jako třída (class), specializace (spec) a item level (úroveň vybavení). 
Cílová proměnná je `clear_time_ms`, což je skutečná doba průchodu dungeonem v milisekundách. 

### Struktura repozitáře

```
HW2/
├── README.md
├── dataprocessing.ipynb        # popis dat, leakage audit, split, preprocessing
├── dataprocessing.html         # exportovaná záloha ipynb
├── benchmark.ipynb             # naivní baseline + Ridge benchmark na validační sadě
├── benchmark.html              # exportovaná záloha ipynb
├── data/
│   ├── train.csv               # trénovací sada (~70 %, nejstarší podle completed_at)
│   ├── validation.csv          # validační sada (~15 %)
│   └── test.csv                # testovací sada (~15 %, odložena pro finální model)
├── src/
│   ├── pyWowStats.py           # Tady je scraper z Raider.IO API - volá nejnovější runy, nevrátí už stejná nejstarší data.
│   └── pyWowClean.py           # Odstranění duplicit a vložení chybějících ilvl hodnot
├── raiderio_runs_saron_final.csv   # surová scrapovaná data
└── raiderio_runs_saron_clean.csv   # očištěná data (vstup do dataprocessing.ipynb)
```

## Jak spustit

### Závislosti

* Python 3.13
* `pandas`, `requests`, `scikit-learn`, `jupyter`

### Spuštění

Kroky je nutné spouštět v pořadí:

* **Krok 1** sběr dat (přeskočit, pokud `raiderio_runs_saron_final.csv` již existuje)
```
python src/pyWowStats.py
```
* **Krok 2** čištění dat (přeskočit, pokud `raiderio_runs_saron_clean.csv` již existuje)
```
python src/pyWowClean.py
```
* **Krok 3** spustit všechny buňky v `dataprocessing.ipynb`
* **Krok 4** spustit všechny buňky v `benchmark.ipynb`

## Zdroj dat

Raider.IO veřejné API (`/mythic-plus/runs` a `/mythic-plus/run-details`), region EU, sezóna Midnight 1, pouze dungeon Pit of Saron. Všechny runy pocházejí z top-ranked části EU populace. Výběrový bias je záměrný (API ani jiná data neposkytne..).

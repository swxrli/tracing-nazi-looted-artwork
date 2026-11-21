# Tracing Nazi-Looted Art
### Computational Reconstruction of Fragmented Provenance Networks

A data-driven project exploring the provenance of artworks recorded by the **ERR (Einsatzstab Reichsleiter Rosenberg)** during World War II.

This project combines data processing, data structures, algorithms, object-oriented programming, and data visualization to reconstruct fragmented artwork ownership histories and identify gaps in provenance records.

---

## Project Overview

During World War II, the Nazi organization ERR systematically confiscated artworks across occupied Europe. Historical records documenting these artworks and their ownership are often fragmented, incomplete, or inconsistent.

This project analyzes records from the ERR Jeu de Paume database to organize artwork information, reconstruct provenance relationships, and identify missing or incomplete historical documentation.

## Objectives

- Collect and organize historical artwork records.
- Clean and preprocess raw provenance data.
- Apply data structures and algorithms to organize and analyze relationships.
- Implement object-oriented concepts using C++.
- Identify gaps and inconsistencies in provenance timelines.
- Visualize findings through Tableau dashboards.

## Key Components

### 1. Data Collection and Preprocessing

- Collects artwork records from the ERR Jeu de Paume database.
- Processes raw JSON records into structured CSV datasets.
- Standardizes artwork and provenance statement identifiers.
- Classifies dates based on completeness and validity.
- Preserves source information for further analysis.

### 2. Data Structures and Algorithms

- **Hash Tables:** Efficient data retrieval.
- **Inverted Indexes:** Searching and indexing textual information.
- **Graphs:** Representing relationships between artworks and locations.
- **BFS and DFS:** Graph traversal and relationship exploration.
- **Date Indexing:** Organizing provenance information chronologically.
- **Performance Benchmarking:** Evaluating implemented operations.

### 3. Object-Oriented Programming (C++)

Implements classes to represent:

- `Artwork`
- `ProvenanceStatement`
- `PlaceStatement`
- `DateStatement`
- `GeneralStatement`
- `ProvenanceRecord`

Demonstrates encapsulation, inheritance, abstraction, and runtime polymorphism.

### 4. Data Visualization

Tableau dashboards and stories present insights into:

- Artwork provenance patterns.
- Geographic distribution of recorded locations.
- Chronological patterns in ownership histories.
- Completeness of provenance dates.
- Gaps in historical documentation.

## Technology Stack

| Area | Technologies |
|---|---|
| Programming Languages | Python, C++ |
| Data Processing | Pandas, Python Standard Library |
| Data Structures | Hash Tables, Inverted Indexes, Graphs |
| Algorithms | BFS, DFS, Searching and Indexing |
| Data Visualization | Tableau |
| C++ Compiler | GCC (g++) |
| Data Formats | JSON, CSV |

## Dataset

The project uses historical records from the **ERR Jeu de Paume database**.

The processed dataset contains approximately:

- **41,343 artwork records**
- **150,168 provenance statements**

The data is organized into raw and processed formats to support preprocessing and subsequent analysis.

Historical records may contain incomplete dates, missing ownership information, and inconsistent descriptions. These limitations are considered during analysis.

## Repository Structure

```text
tracing-nazi-looted-artwork/
│
├── data structures/
│   ├── algorithms.py
│   ├── analysis.py
│   ├── benchmark.py
│   ├── data_index.py
│   ├── graph.py
│   ├── main.py
│   └── test_project.py
│
├── data viz/
│   ├── data viz mini project.twb
│   └── data viz mini project.twbx
│
├── oops/
│   ├── main.cpp
│   ├── models.cpp
│   └── models.h
│
├── shared data/
│   ├── data/
│   │   ├── raw/
│   │   └── processed/
│   └── python/
│       ├── collect_err.py
│       └── prepare_data.py
│
├── outputs/
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

- Python 3
- GCC or another compatible C++ compiler
- Tableau Desktop or Tableau Public

### Python Setup

Install the data-processing dependency:

```bash
python -m pip install pandas
```

The optional web data collection script additionally requires:

```bash
python -m pip install requests beautifulsoup4 urllib3 truststore
```

These additional packages are only required if you intend to run the web data collection script.

### C++ Compilation and Execution

The project uses GCC (`g++`) to compile the C++ source files.

From the repository root directory, run:

```powershell
g++ -std=c++17 "oops/main.cpp" "oops/models.cpp" -o provenance.exe
```

Execute the program:

```powershell
.\provenance.exe
```

**Important:** Run the executable from the repository root directory so it can locate the processed CSV datasets.

### Python Data Preprocessing

The preprocessing script converts the raw JSON dataset into structured CSV files.

Run it from the repository root:

```bash
python "shared data/python/prepare_data.py"
```

## Project Outputs

The `outputs/` directory contains generated analytical results, including:

- Artwork provenance summaries.
- Chronological provenance records.
- Connected artwork records.
- Date completeness analysis.
- Location frequency analysis.
- Performance benchmarking results.
- Provenance gap analysis.

## Limitations

- Historical records may be incomplete or inconsistent.
- Some artwork ownership timelines cannot be fully reconstructed.
- Automated analysis is limited by the information available in the source records.
- Identified provenance connections reflect relationships documented in the available records and do not independently establish legal ownership.

## Future Improvements

- Improve search efficiency and indexing.
- Develop more detailed provenance network visualizations.
- Enhance handling of incomplete and uncertain historical dates.
- Expand analytical capabilities for identifying provenance gaps.

## Academic Project

**Project Title:** Tracing Nazi-Looted Art: Computational Reconstruction of Fragmented Provenance Networks

**Author:** Swarali Tambe

An academic mini-project integrating data structures, algorithms, object-oriented programming, data processing, and data visualization.
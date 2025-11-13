# Academic Paper Processing Toolkit

A comprehensive toolkit for downloading, processing, and analyzing academic papers from arXiv and conference proceedings.

## Overview

This toolkit provides automated workflows for:
- **PDF Collection**: Downloading conference papers from arXiv using DBLP metadata
- **Citation Processing**: Extracting citations and author information using GROBID
- **Metadata Management**: Creating structured datasets from processed papers
- **Data Organization**: Maintaining clean, organized file structures

## Quick Start

### 1. Download Conference PDFs from arXiv

```bash
# Activate virtual environment
source .venv/bin/activate

# Download PDFs from all supported conferences
python3 src/download_arxiv_pdfs.py
```

### 2. Process PDFs with GROBID (Optional)

```bash
# Start GROBID server
sudo docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0

# Process PDFs to extract citations and metadata
python src/run_grobid.py
```

### 3. Extract Structured Metadata

```bash
# Convert GROBID XML output to CSV format
python3 src/parse_grobid_to_csv.py
```

## Data Organization

The toolkit maintains a clean, organized data structure:

```
data/
├── arxiv_pdfs/           # Raw PDF files by conference/year
│   ├── aaai/2015/...
│   ├── icml/2023/...
│   └── neurips/2024/...
├── parsed_jsons/         # Processed citation data by conference/year
│   ├── aaai/2015/...
│   ├── icml/2023/...
│   └── neurips/2024/...
├── dblp_conferences/     # DBLP conference metadata
│   ├── AAAI/
│   ├── ICML/
│   └── NEURIPS/...
├── xml_files/            # GROBID XML outputs
├── outputs/
│   ├── legacy/           # Archived processing outputs
│   └── xml_files/        # Current XML processing results
└── arxiv_metadata.csv    # Structured metadata (optional)
```

## Installation

1. **Clone the repository**
2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional: Install GROBID for citation processing**
   ```bash
   # For GPU acceleration (recommended)
   sudo docker run --rm --gpus all --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0

   # For CPU-only
   sudo docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.0
   ```

## Core Scripts

### PDF Downloader (`src/download_arxiv_pdfs.py`)

Downloads conference papers from arXiv using DBLP conference metadata.

**Features:**
- Multi-conference support (AAAI, ICML, ICLR, FACCT, NEURIPS)
- Fuzzy title matching with configurable thresholds
- Automatic author name cleaning (removes DBLP numeric suffixes)
- Resume capability for interrupted downloads
- Progress tracking and detailed logging

**Usage:**
```bash
# Download all conferences
python3 src/download_arxiv_pdfs.py

# Download with custom settings
python3 src/download_arxiv_pdfs.py --max-papers 10 --match-threshold 90 --delay 5
```

**Outputs:**
- `data/arxiv_pdfs/conference/year/` - Organized PDF files
- `arxiv_papers_metadata.json` - Download metadata and statistics
- `arxiv_download_progress.log` - Detailed progress logs

### GROBID Processing (`src/run_grobid.py`)

Processes PDFs with GROBID to extract citations, authors, and metadata.

**Requirements:** Running GROBID Docker container
**Outputs:** XML files in TEI format stored in `data/xml_files/`

### Metadata Extraction (`src/parse_grobid_to_csv.py`)

Converts GROBID XML outputs to structured CSV format.

**Features:**
- Extracts paper titles, authors, and affiliations
- Filters to main paper authors (excludes citations)
- Handles missing data gracefully
- Processes thousands of XML files efficiently

**Output:** `data/arxiv_metadata.csv` (tab-separated)

### Citation Analysis (`src/citation_pipeline.py`)

Validates and cross-references citation authors against multiple databases.

**Features:**
- Cross-referencing against arXiv, DBLP, Semantic Scholar
- Fuzzy author name matching
- Confidence scoring for matches
- Rate limiting and error handling

## Supported Conferences

- **AAAI** (2015-2025): Association for the Advancement of Artificial Intelligence
- **ICML** (2015-2024): International Conference on Machine Learning
- **ICLR** (2015-2025): International Conference on Learning Representations
- **FACCT** (2021-2025): ACM Conference on Fairness, Accountability, and Transparency
- **NEURIPS** (2014-2024): Neural Information Processing Systems

## Configuration

Edit `config/config.json` for GROBID settings:

```json
{
    "grobid_server": "http://localhost:8070",
    "batch_size": 1000,
    "sleep_time": 5,
    "timeout": 60,
    "coordinates": ["persName", "figure", "ref", "biblStruct", "formula", "s"]
}
```

## Dependencies

- `arxiv==1.4.8` - arXiv API access
- `nameparser==1.1.3` - Author name parsing
- `fuzzywuzzy==0.18.0` - Fuzzy string matching
- `requests>=2.31.0` - HTTP requests
- `backoff==2.2.1` - Retry logic
- `tqdm>=4.66.0` - Progress bars

## Limitations

- **API Rate Limits**: arXiv and DBLP APIs have request limits
- **Matching Accuracy**: Success depends on title similarity thresholds
- **Coverage**: Only papers with arXiv versions can be downloaded
- **Processing Time**: Large-scale processing can take several hours
- **GROBID**: Requires Docker and significant computational resources

## License

MIT License

---

## Development Diary

### 2025-11-13 (5) - Advanced Author Name Matching and Output Organization

Refined citation validation to handle complex name variations and improve result organization:

- **Enhanced Initial Matching**: Fixed initial matching to properly handle accented characters (e.g., "Ł Kaiser" now matches "Lukasz Kaiser")
- **Improved Accent Detection**: Better detection of accent differences when one name uses initials (e.g., "A Hyvarinen" vs "Aapo Hyvärinen" now classified as accents_missing)
- **Flexible Initial-Name Matching**: Authors with initials now properly match full names starting with the same letter (e.g., "S Corff" matches "Sylvain Le Corff")
- **Output Organization**: Parsing errors are now sorted to the bottom of mismatch results for better prioritization

**Technical Changes:**
- Modified `get_initials()` in `analyze_matches.py` to normalize accented characters before extracting initials
- Enhanced accent detection logic in validation to handle initial-full name combinations
- Added initial matching logic for both first and last name comparisons
- Implemented sorting of mismatch results to prioritize non-parsing errors

**Impact:** More accurate author matching for citations using various naming conventions, better error classification, and improved result organization for easier analysis of validation issues.

### 2025-11-13 (2) - Parsing Error Detection in Citation Validation

Enhanced the citation validation system to detect and flag systematic parsing errors where author names are shifted or mixed up:

- **Added parsing error detection to `src/validate_citations.py`**:
  - Detects when first names and last names are mixed up between adjacent authors
  - Checks if reference author's last name matches DBLP author's first name (or vice versa)
  - Flags entire reference as `parsing_error` when this pattern is detected
  - Short-circuits further error analysis when parsing error is found (since all other errors are likely consequences of the parsing issue)

- **Reorganized output structure**:
  - Output JSON now separates `mismatches` (author_mismatch status) and `matches` (matched status) into distinct top-level sections
  - Mismatches appear first in the output file for easier inspection
  - Added counts to analysis section: `mismatch_count` and `match_count`

- **Test results** (20 files, 825 references):
  - **50 parsing errors detected** - systematic name shifting issues
  - 105 author_not_found errors
  - 35 first_name_mismatch errors
  - 27 last_name_mismatch errors
  - 14 accents_missing errors
  
- **Example parsing errors found**:
  - BERT paper: "Kenton", "Lee Kristina" parsed instead of "Kenton Lee", "Kristina Toutanova"
  - "William Yang", "Wang" split instead of "William Yang Wang"
  - "Christophe Hoa T Le" parsed instead of "Hoa T. Le" (first author's first name becoming previous author's last name)

The parsing error detection helps identify systematic issues in PDF parsing that affect entire reference lists, making it easier to prioritize which citation extraction errors need fixing at the parser level vs. minor variations in author name formatting.

### 2025-11-13 (1) - Enhanced Citation Validation System

Improved the citation validation system with better error detection and classification:

- **Enhanced `src/validate_citations.py`** with new features:
  - **Title similarity filtering**: Only considers DBLP matches if string similarity >= 90% (configurable via `--title-similarity-threshold`)
  - **Minimum author list comparison**: Compares only the minimum length of reference and DBLP author lists, handling cases where authors don't include full author lists
  - **Error classification**: Categorizes mismatches into specific types:
    - `first_name_mismatch`: First names differ
    - `last_name_mismatch`: Last names differ
    - `accents_missing`: Names differ only by accents/diacritics
    - `author_order_wrong`: Authors match but order differs
    - `author_not_found`: Author not found in DBLP list
  - Uses `rapidfuzz` for accurate title similarity calculation
  - Tracks title similarity scores in results for analysis

- **Enhanced `src/analyze_validation_results.py`**:
  - Analyzes error classifications and patterns
  - Identifies common mistakes (low title similarity, order issues, accent problems)
  - Provides statistics on author list length differences
  - Generates detailed analysis JSON with examples

- **Key improvements**:
  - More accurate matching by filtering low-similarity titles
  - Better handling of partial author lists (common in citations)
  - Detailed error classification for easier debugging
  - Comprehensive analysis tools for understanding validation results

The enhanced validation system provides more accurate citation validation and better insights into citation errors.

### 2025-01-11 - Citation Validation System

Added a comprehensive citation validation system to check author citations in parsed JSON files against DBLP database:

- **New script `src/validate_citations.py`**: Processes JSON files from `data/parsed_jsons/` and validates each reference by:
  - Querying DBLP database using paper titles
  - Comparing author lists between references and DBLP entries
  - Using existing name matching logic from `analyze_matches.py` to handle variations (initials, reversed names, etc.)
  - Flagging incorrect citations with detailed mismatch information

- **Analysis tool `src/analyze_validation_results.py`**: Provides detailed statistics and insights:
  - Overall match/mismatch rates
  - Categorization of mismatch types (missing authors, extra authors, list differences)
  - Examples of problematic citations
  - Files with most mismatches

- **Key features**:
  - Processes multiple JSON files (default: 20 files for testing)
  - Uses DBLP parser with BM25 search for efficient title matching
  - Leverages existing author name normalization and matching functions
  - Generates comprehensive JSON output with validation results
  - Handles edge cases (missing titles, parsing errors, etc.)

- **Initial test results** (20 files, 952 references):
  - 53.2% match rate (correct citations)
  - 46.8% mismatch rate (potential errors or variations)
  - Detects real errors (e.g., wrong author names) as well as minor variations (abbreviations, middle initials)

The validation system helps identify citation errors in academic papers, enabling quality control and data cleaning workflows.

### 2025-11-11 - README Organization and Cleanup

Completely reorganized and cleaned up the README to reflect the current state of the project:

- **Removed outdated content**: Eliminated redundant sections, confusing explanations, and outdated file paths
- **Simplified structure**: Streamlined from verbose documentation to clear, actionable information
- **Updated data organization**: Documented the current clean folder structure with `parsed_jsons/`, organized outputs, etc.
- **Focused on core functionality**: Emphasized the main workflows (PDF downloading, GROBID processing, metadata extraction)
- **Added clear data structure diagram**: Shows how files are organized across the project
- **Removed development diary**: Consolidated into a single, clean document rather than maintaining separate diary entries

The README now serves as a clear guide for users to understand and use the toolkit effectively.
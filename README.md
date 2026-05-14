# logslice

Fast log filtering and time-range slicing utility for structured and unstructured log files.

---

## Installation

```bash
pip install logslice
```

---

## Usage

```bash
# Slice logs between two timestamps
logslice --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" app.log

# Filter by keyword within a time range
logslice --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" --filter "ERROR" app.log

# Output results to a file
logslice --start "2024-01-15 08:00:00" --end "2024-01-15 09:00:00" app.log -o output.log
```

You can also use `logslice` as a Python library:

```python
from logslice import slice_logs

results = slice_logs(
    filepath="app.log",
    start="2024-01-15 08:00:00",
    end="2024-01-15 09:00:00",
    filter_term="ERROR"
)

for line in results:
    print(line)
```

---

## Features

- Supports structured (JSON, CSV) and unstructured (plain text) log formats
- Fast binary-search-based time range slicing for large files
- Flexible timestamp format detection
- Keyword and regex filtering
- CLI and Python API

---

## License

This project is licensed under the [MIT License](LICENSE).
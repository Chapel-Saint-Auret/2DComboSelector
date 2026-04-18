# Accepted File Format

Files must be uploaded in **.csv**, **.xls**, or **.xlsx** format.

## Retention time data

- The **first column** must contain **compound names**.
- The following columns must contain **retention time values**.
- Each **column header** must correspond to one tested condition.

## 1D peak capacity data

- The file must contain **one row of peak capacity values**.
- Each **column header** must correspond to one tested condition.
- The row must contain the corresponding **experimental 1D peak capacity values**.
- A clear and simple condition naming format is recommended, but not mandatory:

**Mode - Column - Mobile Phase - pH**

*Example: HILIC - BEH Amide - EtOH - pH 7*

## Examples

### Retention Time Table

| Compound | HILIC - BEH Amide - EtOH - pH 7 | RPLC - C18 - ACN/H₂O - pH 3 |
|----------|----------------------------------|-------------------------------|
| Caffeine | 1.25                             | 3.87                          |
| Quinine  | 2.41                             | 5.12                          |
| Rutin    | 4.86                             | 7.45                          |

### 1D peak capacity table

| | HILIC - BEH Amide - EtOH - pH 7 | RPLC - C18 - ACN/H₂O - pH 3 |
|---|---|---|
| Peak capacity | 85 | 112 |
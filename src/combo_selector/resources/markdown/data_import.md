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


A clear and simple condition naming format is recommended, but not mandatory:

**Mode - Column - Mobile Phase - pH**

*Example: HILIC - BEH Amide - EtOH - pH 7*

The row must contain the corresponding experimental 1D peak capacity value, calculated as:
**nc = 1 + (tr,max − tr,min) / ω4σ**
where:

- **nc**: 1D peak capacity 
- **tr,max**: retention time of the latest eluting compound 
- **tr,min**: retention time of the earliest eluting compound 
- **ω4σ**: representative peak width measured at 4σ, in minutes


## Elution-composition range data

- The file must contain **one row of elution-composition range values**.
- Each **column header** must correspond to one tested condition.
- The row must contain the corresponding **elution-composition range value**, calculated as:
  
**ΔΦe = Φe,max – Φe,min**
  
where **Φe,max** and **Φe,min** are the elution compositions of the most retained and least retained compounds, respectively, under the considered condition.
  
The **elution composition** of each compound must be calculated as:
  
**Φe = Φi + (ΔΦgrad / tG) × (tr − t0 − tD)**
  
where:

  - **Φe**: elution composition
  - **Φi**: initial gradient composition in strong solvent
  - **ΔΦgrad**: programmed gradient range in strong solvent
  - **tG**: gradient time
  - **tr**: compound retention time
  - **t0**: column dead time
  - **tD**: instrument dwell time

## Examples

### Retention Time Table

| Compound Name| HILIC - BEH Amide - EtOH - pH 7 | RPLC - C18 - ACN/H₂O - pH 3 |
|--------------|----------------------------------|-------------------------------|
| Caffeine     | 1.25                             | 3.87                          |
| Quinine      | 2.41                             | 5.12                          |
| Rutin        | 4.86                             | 7.45                          |

### 1D peak capacity table

| | HILIC - BEH Amide - EtOH - pH 7 | RPLC - C18 - ACN/H₂O - pH 3 |
|---|---|---|
| Peak capacity | 85 | 112 |

### Elution-Composition Range Table 

| | HILIC - BEH Amide - EtOH - pH 7 | RPLC - C18 - ACN/H₂O - pH 3 |
|---|---|---|
| Elution-Composition Ranges | 45 | 60 |
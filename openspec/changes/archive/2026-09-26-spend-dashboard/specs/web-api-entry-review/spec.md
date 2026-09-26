## ADDED Requirements

### Requirement: Vouchers SHALL be filterable by the state of their document

`GET /api/v1/erp-entries/vouchers` and its summary SHALL accept `document`, taking `failed` (vouchers whose invoice's document could not be read) or `mismatch` (vouchers whose invoice's document total disagrees with the ERP beyond the reconciliation tolerance). Any other value SHALL be 422. The filter SHALL combine with every other filter.

#### Scenario: Documents that failed

- **WHEN** vouchers are listed with `document=failed`
- **THEN** only vouchers whose invoice's document status is failed are listed

#### Scenario: Totals that disagree

- **WHEN** vouchers are listed with `document=mismatch`
- **THEN** only vouchers whose invoice's document total disagrees with its ERP total are listed

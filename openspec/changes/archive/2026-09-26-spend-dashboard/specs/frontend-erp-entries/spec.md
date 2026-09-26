## ADDED Requirements

### Requirement: Spend Lines SHALL be filterable by the state of the voucher's document

Spend Lines SHALL carry a `document` filter in the URL (`failed` or `mismatch`), offered in the filter bar as "Document failed" and "Total disagrees" and cleared with the other filters, so the dashboard's "Needs attention" counts can open the vouchers they count.

#### Scenario: From the dashboard

- **WHEN** the user opens Spend Lines from the dashboard's "3 totals disagree"
- **THEN** Spend Lines lists the vouchers whose document total disagrees with the ERP, with the filter shown as applied

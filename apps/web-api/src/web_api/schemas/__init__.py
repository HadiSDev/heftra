"""Pydantic response schemas for the web API (wire contract, not ORM)."""
from .accounts import OrganizationRead, OrganizationUpdate, UserRead
from .audit import AuditLogRead, VoucherAuditRead
from .common import CurrencyCode, CurrencyMode, Page, Report
from .companies.company import CompanyCreate, CompanyRead, CompanyUpdate
from .companies.deletion import (
    CompanyDeleteBlocked,
    CompanyDeleteResult,
    CompanyRecordCounts,
)
from .companies.maintenance import FxRecomputeResult, RecategorizeResult
from .companies.results import CompanyCreateResult, CompanyUpdateResult
from .companies.runs import PipelineRunCreate, PipelineRunRead
from .erp.accounts import ErpAccountRead, ErpAccountUpdate
from .erp.actions import ConnectionTestResult, RefreshAccountsResult
from .erp.catalog import CredentialFieldRead, ErpTypeRead
from .erp.coverage import SpendCoverageRow
from .erp.entries import ErpEntryRead, VoucherDetailRead, VoucherGroupRead
from .erp.integration_replace import (
    IntegrationReplace,
    IntegrationReplaceBlocked,
    IntegrationSpec,
)
from .erp.integrations import (
    ErpIntegrationCreate,
    ErpIntegrationRead,
    ErpIntegrationUpdate,
)
from .invoices.invoice import DocumentRead, InvoiceDetailRead, InvoiceRead
from .invoices.invoice_edits import InvoiceUpdate, InvoiceVerify
from .invoices.line_edits import InvoiceLineCreate, InvoiceLineUpdate
from .invoices.lines import InvoiceLineRead, InvoiceLineVerify
from .reports.entries import EntryAccountRow, EntrySummaryRow
from .reports.spend import CategorySpendRow, VendorSpendRow
from .reports.breakdown import CategorySpendRead, SpendBreakdown, SpendBreakdownRow, SupplierSpendRead
from .reports.insights import SpendInsights, SpendInsightsRow, SupplierInsight, UncategorizedInsight
from .reports.overview import AttentionCounts, MonthSpend, SpendOverview, SpendOverviewRow
from .reports.period import PeriodRead, ReportPeriods
from .reports.trend import SpendTrend, SpendTrendRow, TrendSeries
from .spend_trees.categories import (
    SpendCategoryCreate,
    SpendCategoryRead,
    SpendCategoryUpdate,
)
from .spend_trees.imports import SpendTreeImportError, SpendTreeImportResult
from .spend_trees.suggestions import (
    SpendCategorySuggestionRead,
    SuggestionEvidenceRead,
    SuggestionResolveResult,
)
from .spend_trees.tree_edits import SpendTreeCreate, SpendTreeUpdate
from .spend_trees.trees import SpendTreeDeleteResult, SpendTreeDetailRead, SpendTreeRead
from .vendors import VendorRead
from .vendor_detail import VendorCategorySpendRead, VendorDetailRead, VendorInvoiceRead
from .vendor_overview import VendorOverviewRead, VendorSpendRead

__all__ = [
    "AttentionCounts",
    "AuditLogRead",
    "CategorySpendRead",
    "CategorySpendRow",
    "CompanyCreate",
    "CompanyCreateResult",
    "CompanyDeleteBlocked",
    "CompanyDeleteResult",
    "CompanyRead",
    "CompanyRecordCounts",
    "CompanyUpdate",
    "CompanyUpdateResult",
    "ConnectionTestResult",
    "CredentialFieldRead",
    "CurrencyCode",
    "CurrencyMode",
    "DocumentRead",
    "EntryAccountRow",
    "EntrySummaryRow",
    "ErpAccountRead",
    "ErpAccountUpdate",
    "ErpEntryRead",
    "ErpIntegrationCreate",
    "ErpIntegrationRead",
    "ErpIntegrationUpdate",
    "ErpTypeRead",
    "FxRecomputeResult",
    "IntegrationReplace",
    "IntegrationReplaceBlocked",
    "IntegrationSpec",
    "InvoiceDetailRead",
    "InvoiceLineCreate",
    "InvoiceLineRead",
    "InvoiceLineUpdate",
    "InvoiceLineVerify",
    "InvoiceRead",
    "InvoiceUpdate",
    "InvoiceVerify",
    "MonthSpend",
    "OrganizationRead",
    "OrganizationUpdate",
    "Page",
    "PeriodRead",
    "PipelineRunCreate",
    "PipelineRunRead",
    "RecategorizeResult",
    "RefreshAccountsResult",
    "Report",
    "ReportPeriods",
    "SpendBreakdown",
    "SpendBreakdownRow",
    "SpendCategoryCreate",
    "SpendCategoryRead",
    "SpendCategorySuggestionRead",
    "SpendCategoryUpdate",
    "SpendCoverageRow",
    "SpendInsights",
    "SpendInsightsRow",
    "SpendOverview",
    "SpendOverviewRow",
    "SpendTreeCreate",
    "SpendTreeDeleteResult",
    "SpendTreeDetailRead",
    "SpendTreeImportError",
    "SpendTreeImportResult",
    "SpendTreeRead",
    "SpendTreeUpdate",
    "SpendTrend",
    "SpendTrendRow",
    "SuggestionEvidenceRead",
    "SuggestionResolveResult",
    "SupplierInsight",
    "SupplierSpendRead",
    "TrendSeries",
    "UncategorizedInsight",
    "UserRead",
    "VendorCategorySpendRead",
    "VendorDetailRead",
    "VendorInvoiceRead",
    "VendorOverviewRead",
    "VendorRead",
    "VendorSpendRead",
    "VendorSpendRow",
    "VoucherAuditRead",
    "VoucherDetailRead",
    "VoucherGroupRead",
]

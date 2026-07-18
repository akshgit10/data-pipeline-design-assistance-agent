# Corporate Data Pipeline Standards & Naming Conventions

This document outlines the mandatory architectural standards, naming schemas, and design constraints for all ingestion pipelines across enterprise data platforms.

## 1. Environment and Storage Layer Prefixes
All storage targets (buckets, staging tables, and data warehouse structures) must follow the tiering taxonomy:
*   **stg_**: Staging layer. Raw, un-validated data landed directly from source files or APIs. Minimal schema modification allowed.
*   **int_**: Intermediate/Transformation layer. Cleansed, deduplicated, and conformed data structures. Joins between entities happen here.
*   **fct_**: Fact tables. Numerical metrics, transaction logs, and time-series operational events.
*   **dim_**: Dimension tables. Descriptive attributes, master data lookups, and slowly changing dimensions (SCD Type 2).

## 2. Table and Column Naming Schema
*   **Snake Case Only**: All object names must be strictly lowercase using underscores (e.g., `customer_orders`, not `CustomerOrders` or `customerOrders`).
*   **Timestamp Suffixes**: Every pipeline must append standard metadata fields to target tables:
    *   `inserted_at_utc`: The timestamp when the record landed in the system.
    *   `updated_at_utc`: The timestamp of the last operational modification.
*   **Datatype Standards**: 
    *   Monetary values must strictly use `DECIMAL(18, 4)`. Never use floating-point types (`FLOAT`/`DOUBLE`) for financial data.
    *   Primary keys generated internally should use standard `UUID` strings or auto-incrementing `BIGINT`.

## 3. Data Retention and Lifecycle Policies
*   **Staging Tier**: Retained for a maximum of 14 days before automated archival or purging.
*   **Production Warehouse Tier**: Permanent retention unless bounded by specific regional compliance rules (e.g., GDPR right-to-be-forgotten sweeps executed every 30 days).
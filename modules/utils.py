"""
Shared UI Helpers Module - Reusable Utility Functions
======================================================

This module contains small, page-agnostic helper functions used by multiple
page modules. These utilities were extracted from the original monolithic
main.py to promote code reuse and consistency across the application.

Purpose:
--------
- Provides reusable UI components for consistent styling
- Handles large dataset sampling for performance optimization
- Ensures consistent heading patterns across all pages
- Improves code maintainability by centralizing common functions

Key Functions:
--------------
- section(label, title): Renders standardized page headings
  - Creates the small-uppercase-label + large-title pattern
  - Used by most pages for consistent visual hierarchy
  - Example: label='ANALYSIS', title='Statistical Summary'

- sample_df_for_speed(frame, enabled, n): Performance optimization for large datasets
  - Returns random sample when dataset is large and sampling is enabled
  - Returns full dataset when sampling is disabled or dataset is small
  - Uses fixed random_state=42 for consistent samples across reruns
  - Default sample size: 50,000 rows

Performance Optimization:
--------------------------
Large datasets (100,000+ rows) can slow down statistics and visualizations.
The sampling function allows users to work with a representative subset
for faster exploration while maintaining statistical validity.

Integration:
------------
- section() used by: statistics.py, visualizations.py, prediction.py, etc.
- sample_df_for_speed() used by: statistics.py, visualizations.py
- Both functions help maintain consistent UI and performance across pages
"""

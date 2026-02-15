JHU Software Concepts - Graduate School Applicant Database
===========================================================

A comprehensive Flask-based web application for analyzing graduate school application data from GradCafe, featuring PostgreSQL database integration, web scraping, data cleaning, and analytical queries.

.. image:: https://img.shields.io/badge/python-3.11+-blue.svg
   :alt: Python Version

.. image:: https://img.shields.io/badge/coverage-100%25-brightgreen.svg
   :alt: Test Coverage

.. image:: https://img.shields.io/badge/tests-166-brightgreen.svg
   :alt: Test Count

**Key Features:**

* **Web Dashboard**: Flask application with JHU branding displaying 11 analytical queries
* **Data Pipeline**: ETL process for scraping, cleaning, and loading GradCafe data
* **Database**: PostgreSQL backend with optimized queries
* **Testing**: 166 tests with 100% code coverage
* **Environment Management**: Flexible configuration via environment variables

Project Overview
----------------

This project (Module 4) implements a complete data pipeline for analyzing graduate school application results:

1. **Web Scraping** (:mod:`scrape`) - Extracts data from The GradCafe
2. **Data Cleaning** (:mod:`clean`) - Normalizes and standardizes the data
3. **Database Loading** (:mod:`load_data`) - Loads data into PostgreSQL
4. **Analytical Queries** (:mod:`query_data`) - Executes statistical analyses
5. **Web Interface** (:mod:`app`) - Displays results via Flask dashboard

API Documentation
-----------------

.. toctree::
   :maxdepth: 2

   api

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Graduate School Applicant Database Analysis System
====================================================

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

Quick Links
-----------

* :doc:`setup` - Get started with installation and configuration
* :doc:`architecture` - Understand the system architecture
* :doc:`operational` - Operational notes and troubleshooting
* :doc:`api` - API reference for all modules
* :doc:`testing` - Testing guide and conventions

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   setup
   architecture

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api

.. toctree::
   :maxdepth: 2
   :caption: Operations Guide

   operational

.. toctree::
   :maxdepth: 2
   :caption: Developer Guide

   testing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

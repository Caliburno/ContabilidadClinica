# ContabilidadClinica

Python rewrite of ClinApp with enhanced features and improved user experience for managing psychology clinic operations.

## About

Second iteration of clinic management software, rebuilt from the ground up in Python. Maintains all core functionality of ClinApp while adding new features like PDF report generation and database management tools.

## Key Improvements Over ClinApp

- **Patient-Centric Interface**: Patient list sidebar with integrated tab system
- **PDF Export**: Generate printable accounting reports
- **Flexible Data Export**: Selective CSV export (choose which tables to export)
- **Database Management**: Built-in backup and restore functionality
- **Simplified Deployment**: Single executable via PyInstaller

## Features

### Core Functionality
All features from ClinApp including:
- Patient management (regular, monthly, diagnosis types)
- Session tracking with multiple session types
- Medical report generation and tracking
- Payment processing and recording
- Comprehensive accounting summaries

### Enhanced Features

**Accounting Reports**
- Monthly revenue breakdown by patient type
- Outstanding debt summary with patient details
- Export reports to PDF for printing or archival
- Visual presentation optimized for readability

**Data Management**
- Manual database save/load functionality
- Selective CSV export (patients, sessions, reports, payments, accounting)
- Planned: Automatic Google Drive backup integration (in development)

**User Interface**
- Patient list sidebar for quick navigation
- Tab-based patient detail view
- Four main action buttons: Add Patient, Accounting Reports, Save Database, Load Database

## Tech Stack

- Python
- Tkinter (GUI)
- SQLite
- PyInstaller
- VS Code

## Status

Feature-complete and functional. Currently undergoing final tweaks before production deployment. ClinApp remains in production use until migration is complete.

## Upcoming Features

- Automatic Google Drive backup integration
- GUI personalization

## Architecture

Improved separation of concerns compared to ClinApp, with clear distinction between business logic and presentation layer. Designed for easier maintenance and future enhancements.

## Screenshots

![01_new_payment](https://github.com/user-attachments/assets/842aa6b9-c958-4e99-a426-e15ca6eadbcd)
![02_debt](https://github.com/user-attachments/assets/0ee222df-fbac-45f8-9c05-2fc652c809f6)
![03_new_payment_apply](https://github.com/user-attachments/assets/522c302b-8750-4cf9-b775-63547b1b4c3e)
![04_summary](https://github.com/user-attachments/assets/f00a2d13-460b-4f9c-bcdf-49b261fb7c4b)
![05_in_favour](https://github.com/user-attachments/assets/48c9884d-db15-4d1f-aca7-b1eb5e86a00e)
![06_financial_report](https://github.com/user-attachments/assets/808bfbd0-79c6-4b38-8035-af8ae6da939d)
![07_financial_report_cont](https://github.com/user-attachments/assets/5e67b1b6-d67a-47e7-842f-9696b4bc1da5)
![08_export_database](https://github.com/user-attachments/assets/a708da1f-af12-43b0-9279-f7c84c5e2993)
![09_export_database_to_cvs](https://github.com/user-attachments/assets/433f762d-d171-43be-a2fa-87b2fadbc24e)

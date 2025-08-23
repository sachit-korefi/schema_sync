# Schema Sync - Excel and CSV Data Transformation Utility

## Description

Schema Sync is a powerful web application built with FastAPI that provides seamless data transformation capabilities. It allows users to upload Excel or CSV files and convert them to a predefined schema, enabling easy data standardization and manipulation.

## Features

- 📄 Support for Excel (.xlsx) and CSV file uploads
- 🔄 Dynamic schema transformation
- 📋 Sheet name retrieval for Excel files
- 🔒 Secure file handling with FastAPI
- 💾 Database integration for persistent data management

## Installation

### Prerequisites

- Python 3.10+
- pip (Python Package Manager)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd schema-sync
   ```

2. **Create a virtual environment:**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate
   
   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the database:**
   ```bash
   alembic upgrade head
   ```

## Usage

### Running the Application

```bash
uvicorn main:app --reload
```

### API Endpoints

#### Schema Management
- `GET /schema/{schema_uuid}` - Get Schema
- `PUT /schema/{schema_uuid}` - Update Schema
- `DELETE /schema/{schema_uuid}` - Delete Schema
- `GET /schema/get_all_schemas/{user_uuid}` - Get All Schemas
- `POST /schema/{user_uuid}` - Create Schema

#### User Management
- `GET /user/` - Get All Users
- `POST /user/` - Create User
- `GET /user/{user_uuid}` - Get User Details
- `PUT /user/{user_uuid}` - Update User Details

#### Data Synchronization
- `GET /sync/` - Sync Schema
- `POST /sync/get_excel_sheets` - Get Excel Sheet Names

#### Health & Monitoring
- `GET /` - Read Root
- `GET /health_check` - Health Check

### Example Usage

```bash
# Health check
curl -X GET "http://localhost:8000/health_check"

# Get Excel sheet names
curl -X POST "http://localhost:8000/sync/get_excel_sheets" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@your_file.xlsx"

# Sync schema
curl -X GET "http://localhost:8000/sync/"
```

## Technologies Used

- 🐍 **Python** - Core programming language
- 🚀 **FastAPI** - Modern web framework for building APIs
- 🐼 **Pandas** - Data manipulation and analysis
- 📊 **SQLAlchemy** - SQL toolkit and ORM
- 🗄️ **Alembic** - Database migration tool

## Project Structure

```
schema-sync/
├── main.py
├── requirements.txt
├── alembic/
├── dependencies/
└── ...
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please open an issue on GitHub.
# TPC-DS Item Rental Management System

## How to get this running (indev, TODO: remove this and refactor README)

### 1. Clone the Repository
```bash
git clone https://github.com/TPC-DS.git proj.git
cd proj.git
```

### 2. Install dependencies
Install python and make sure to pip install maridb.

### 3. Download Data Files & Credentials Template
Since `tpcds_data/` and `MARIADB_CREDS.py` are in .gitignore:
*   **Download Link:** [Project Files (zip)](https://ufl.instructure.com/courses/554442/files/105639818?wrap=1)
*   Extract the zip and move the `tpcds_data` folder and the `MARIADB_CREDS.py` file into your local `proj.git` root directory.

### 4. Configure Credentials
Open `MARIADB_CREDS.py` and update it with your local MariaDB username and password. Should be 'root' for both.

### 5. Initialize the Database
Run:
```bash
python setup_db.py ./tpcds_data/
```

### 6. Verify Installation
Run main to see if it starts and you can see the menu (won't work rn, indev)
```bash
python main.py
```

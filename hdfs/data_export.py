# hdfs/data_export.py
import pandas as pd
from datetime import datetime


def export_tables_to_hdfs(db_connection, hdfs_client):
    """Export all tables from SQLite to HDFS"""

    # Define tables to export
    tables = ['admins', 'customers', 'stocks']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for table in tables:
        try:
            # Read table from SQLite
            df = pd.read_sql_query(f"SELECT * FROM {table}", db_connection)

            # Define HDFS path
            hdfs_path = f'/inventory_data/{table}/{timestamp}/{table}.parquet'

            # Create directory structure
            dir_path = f'/inventory_data/{table}/{timestamp}'
            hdfs_client.create_directory(dir_path)

            # Upload to HDFS
            hdfs_client.upload_parquet(df, hdfs_path)

            print(f"Successfully exported {table} to HDFS: {hdfs_path}")

            # Also save as backup locally
            backup_path = f'/data/hdfs_export/{table}_{timestamp}.parquet'
            df.to_parquet(backup_path)

        except Exception as e:
            print(f"Failed to export {table}: {e}")
            continue

    return True


def export_to_csv_backup(db_connection):
    """Create CSV backups locally"""
    tables = ['admins', 'customers', 'stocks']
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    for table in tables:
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table}", db_connection)
            backup_path = f'/data/hdfs_export/{table}_{timestamp}.csv'
            df.to_csv(backup_path, index=False)
            print(f"CSV backup created: {backup_path}")
        except Exception as e:
            print(f"Failed to create CSV backup for {table}: {e}")
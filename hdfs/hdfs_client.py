# hdfs/hdfs_client.py
import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from pyhdfs import HdfsClient
import os
from datetime import datetime


class HDFSClient:
    def __init__(self, namenode_url='hdfs://namenode:9000'):
        self.namenode_url = namenode_url
        self.host = namenode_url.replace('hdfs://', '').split(':')[0]
        self.port = int(namenode_url.split(':')[-1])
        self.client = HdfsClient(hosts=f'{self.host}:{self.port}')

    def upload_parquet(self, df, hdfs_path):
        """Upload DataFrame to HDFS as Parquet file"""
        # Create local temporary file
        local_path = f'/tmp/temp_{datetime.now().strftime("%Y%m%d_%H%M%S")}.parquet'

        # Convert to Parquet
        table = pa.Table.from_pandas(df)
        pq.write_table(table, local_path)

        # Upload to HDFS
        with open(local_path, 'rb') as f:
            self.client.create(hdfs_path, f.read(), overwrite=True)

        # Clean up
        os.remove(local_path)
        return True

    def list_files(self, hdfs_path):
        """List files in HDFS directory"""
        return self.client.listdir(hdfs_path)

    def create_directory(self, hdfs_path):
        """Create directory in HDFS if it doesn't exist"""
        if not self.client.exists(hdfs_path):
            self.client.mkdirs(hdfs_path)
        return True
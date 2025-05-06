#!/usr/bin/env python3

"""Script for downloading and importing Garmin data."""

import sys
import os
import logging
import datetime
import json
from garmindb import Download, Copy, Import, Analyze

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_config():
    """Return the configuration."""
    config_file = os.path.expanduser('GarminConnectConfig.json')
    try:
        with open(config_file) as f:
            config = json.load(f)
        return config
    except FileNotFoundError:
        logger.error(f"Could not find configuration file {config_file}")
        sys.exit(-1)

def main():
    """Main function that handles downloading and importing of Garmin data."""
    config = get_config()
    
    # 데이터 다운로드
    download = Download()
    if not download.login(config['credentials']['user'], config['credentials']['password']):
        logger.error("Failed to login to Garmin Connect")
        sys.exit(-1)

    # 활동 데이터 다운로드
    start_date = datetime.datetime.strptime(config['data']['start_date'], '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(config['data']['end_date'], '%Y-%m-%d').date()
    
    download.get_activity_files(start_date, end_date)
    download.get_monitoring_files(start_date, end_date)
    download.get_sleep_files(start_date, end_date)
    download.get_weight_files(start_date, end_date)
    download.get_rhr_files(start_date, end_date)
    
    # 데이터베이스 생성 및 데이터 임포트
    db_params = {
        'db_type': 'sqlite',
        'db_path': os.path.expanduser('garmin.db')
    }
    
    # 데이터 복사
    copy = Copy(db_params)
    copy.copy_data()
    
    # 데이터 임포트
    import_data = Import(db_params)
    import_data.import_data()
    
    # 데이터 분석
    analyze = Analyze(db_params)
    analyze.analyze()
    
    logger.info("Data import completed successfully")

if __name__ == "__main__":
    main() 
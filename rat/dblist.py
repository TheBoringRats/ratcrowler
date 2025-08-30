from typing import Optional, List, Dict, Any
from config import config
import json
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

class DBList:
    def __init__(self, config=config):
        self.loaddb = config.JSONCONFIG_PATH
        # Handle both direct list and nested dictionary structure
        if isinstance(self.loaddb, dict) and 'databases' in self.loaddb:
            self.dbdata = self.loaddb['databases']
        elif isinstance(self.loaddb, list):
            self.dbdata = self.loaddb
        else:
            self.dbdata = []

        print(f"📊 Loaded {len(self.dbdata)} database configurations")
        self.crowdb = []  # Changed to list to store multiple DBs
        self.backlink = []
        self.crawler_enginelist = []
        self.backlink_enginelist = []

    def crowldbgrab(self):
        """Get all crawler databases (cat=2)"""
        self.crowdb = []
        for db in self.dbdata:
            if db.get("cat") == 2:
                db_config = {
                    "name": db.get("name"),
                    "url": db.get("url"),
                    "auth_token": db.get("auth_token"),
                    "apikey": db.get("apikey"),
                    "organization": db.get("organization"),
                    "monthly_write_limit": db.get("monthly_write_limit"),
                    "storage_quota_gb": db.get("storage_quota_gb")
                }
                self.crowdb.append(db_config)
        return self.crowdb

    def backlinkdbgrab(self):
        """Get all backlink databases (cat=1)"""
        self.backlink = []
        for db in self.dbdata:
            if db.get("cat") == 1:
                db_config = {
                    "name": db.get("name"),
                    "url": db.get("url"),
                    "auth_token": db.get("auth_token"),
                    "apikey": db.get("apikey"),
                    "organization": db.get("organization"),
                    "monthly_write_limit": db.get("monthly_write_limit"),
                    "storage_quota_gb": db.get("storage_quota_gb")
                }
                self.backlink.append(db_config)
        return self.backlink

    def webcrawldbengine(self):
       dblist=self.crowldbgrab()
       for db in dblist:
           db['name'] = create_engine(
               f"sqlite+{db['url']}?secure=true",
               connect_args={"auth_token": db['auth_token']}
           )
           self.crawler_enginelist.append(db['name'])
       return self.crawler_enginelist

    def backlinkdbengine(self):
       dblist=self.backlinkdbgrab()
       for db in dblist:
           db['name'] = create_engine(
               f"sqlite+{db['url']}?secure=true",
               connect_args={"auth_token": db['auth_token']}
           )
           self.backlink_enginelist.append(db['name'])
       return self.backlink_enginelist

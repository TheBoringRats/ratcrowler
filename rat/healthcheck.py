from rat.dblist import DBList
from sqlalchemy.exc import OperationalError
from typing import List, Dict,Optional,Any
import requests


class Health:
  def __init__(self):
    self.dblist = DBList()
    self.crawler_databases = self.dblist.crowldbgrab()
    self.backlink_databases = self.dblist.backlinkdbgrab()
    self.internal_link_databases = self.dblist.backlinkdbengine()
    self.external_link_databases = self.dblist.webcrawldbengine()
    self.useable_databases_crawler = []
    self.useable_databases_backlink = []

  def __dbfindhealth(self,dbname:str,orgname:str,authkey:str):
       headers={
          "Authorization": f"Bearer {authkey}",
          "Content-Type": "application/json"
       }
       response=requests.get(f"https://api.turso.tech/v1/organizations/{orgname}/databases/{dbname}/usage",
                             headers=headers,
                             timeout=10)
       return response.json()

  def useabledbdata(self):
     for db in self.crawler_databases:
        dbname=db.get("name")
        apikey=db.get("apikey")
        orgname=db.get("organization")
        healthinfo=self.__dbfindhealth(dbname,orgname,apikey)
        uses=healthinfo.get("total",{})

        # Ensure values are not None before comparison
        rows_read = uses.get("rows_read", 0)
        storage_bytes = uses.get("storage_bytes", 0)
        if rows_read is None:
            rows_read = 0
        if storage_bytes is None:
            storage_bytes = 0

        if rows_read<9000000 and storage_bytes<4000000000:
              self.useable_databases_crawler.append(db)
        else:
              self.useable_databases_crawler.append(None)
     for dbw in self.backlink_databases:
         dbname=dbw.get("name")
         apikey=dbw.get("apikey")
         orgname=dbw.get("organization")
         healthinfo=self.__dbfindhealth(dbname,orgname,apikey)
         uses=healthinfo.get("total",{})

         # Ensure values are not None before comparison
         rows_read = uses.get("rows_read", 0)
         storage_bytes = uses.get("storage_bytes", 0)
         if rows_read is None:
             rows_read = 0
         if storage_bytes is None:
             storage_bytes = 0

         if rows_read<9000000 and storage_bytes<4000000000:
              self.useable_databases_backlink.append(dbw)
         else:
              self.useable_databases_backlink.append(None)

  def current_limit(self,dbname:str,orgname:str,authkey:str)->Optional[Dict[str,Any]]:
     health=self.__dbfindhealth(dbname,orgname,authkey)
     return health.get("total",{})

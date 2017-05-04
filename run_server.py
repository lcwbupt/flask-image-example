# -*- coding: utf-8 -*-
#!/usr/bin/python                        
##################################################
# AUTHOR : Yandi LI
# CREATED_AT : 2016-10-11
# LAST_MODIFIED : 2017-05-04 11:21:20
# USAGE : python run_server.py
# PURPOSE : Start flask application
##################################################
from src import app

if __name__ == "__main__":
  app.run(host="0.0.0.0", port=7777)

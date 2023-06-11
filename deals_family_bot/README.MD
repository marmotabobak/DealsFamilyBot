# Family costs bot

## Deploy
1. create schema 'family_cost_bot'
2. create tables:
   <br />2.1. uncomment in run.py after postgres_engine creation (currently str # 53):
   ```postgres_engine.drop_and_create_all_tables()```
   ONLY FOR FIRST START AND IF TABLES DO NOT EXIST! OTHERWISE ALL DATA WILL BE ERASED!!! **_DON'T FORGET TO DELETE/COMMENT THIS CODE RIGHT AFTER FIRST START!_**


## Start

```nohup python3 deals_family_bot/run.py -c configs/dev.yml > /root/pythonProjects/CostsTelegramBot/log.log 2>/root/pythonProjects/CostsTelegramBot/error.log &```
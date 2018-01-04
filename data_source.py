# -*- coding: utf-8 -*-

import pandas as pd

URL = 'URL'
DTYPE = 'DTYPE'
OBJ = 'OBJ'
HOST='HOST'
PORT='PORT'
DB='DB'
AUTH='AUTH'

SQLALCHEMY = 1
REDIS = 2
MONGODB = 3

__DNS = {
'DNDS':{
    URL:'mssql+pymssql://reader:reader@10.15.97.127:1433/dnds',
    DTYPE:SQLALCHEMY
},
'PI_FCDB':{
    URL:'mssql+pymssql://read:read@192.168.100.154:1433/PI_FCDB',
    DTYPE:SQLALCHEMY
},
'FACTORS':{
    URL:'mysql+mysqlconnector://root:123@10.15.97.128:3306/factors',
    DTYPE:SQLALCHEMY
},
'FACTORS_MSSQL':{
    URL:'mssql+pymssql://reader:reader@10.15.97.127:1433/factor',
    DTYPE:SQLALCHEMY
},
'INEEQ':{
    URL:'mssql+pymssql://ineeq_read:ineeq_read@120.26.104.48:3433/ineeq',
    DTYPE:SQLALCHEMY
},
'KLINE':{
    DTYPE:REDIS,
    HOST:'10.10.15.179',
    PORT:6379,
    DB:14
}
}

def __getSqlAlchemyEngine( source ):
    if not OBJ in __DNS[source].keys():
        import sqlalchemy as sa
        __DNS[source][OBJ] = sa.create_engine( __DNS[source][URL] )

    return __DNS[source][OBJ]

def __getRedisConn( source ):
    import redis
    if not OBJ in __DNS[source].keys():
        if AUTH in __DNS[source].keys():
            __DNS[source][OBJ] = redis.ConnectionPool( host=__DNS[source][HOST], port=__DNS[source][PORT], password=__DNS[source][AUTH], db=__DNS[source][DB] )
        else:
            __DNS[source][OBJ] = redis.ConnectionPool( host=__DNS[source][HOST], port=__DNS[source][PORT], db=__DNS[source][DB] )

    conn = redis.Redis( connection_pool = __DNS[source][OBJ] )
    return conn

def GetDataEngine( source ):
    engine = None
    if source in __DNS.keys():
        if __DNS[source][DTYPE] == SQLALCHEMY:
            return __getSqlAlchemyEngine( source )
        elif __DNS[source][DTYPE] == REDIS:
            return __getRedisConn( source )
    else:
        raise Exception("未知的数据源 -- '{0}'")

    return engine

if __name__ == "__main__":
    db_engine = GetDataEngine('DNDS')
    df = pd.read_sql('SELECT * from dnds.dbo.TQ_QT_SKDAILYPRICE where SECODE = 2010000565 and TRADEDATE = 19901220', db_engine)
    print (df)

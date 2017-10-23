import time
from orm import Model, StringField, BooleanField, IntegerField


class Proxy(Model):
    ''' 代理数据对象类 '''
    __table__ = 'proxy'
    url = StringField(primary_key=True, ddl='varchar(30)')
    ip = StringField(ddl='varchar(15)')
    port = StringField(ddl='varchar(5)')
    address = StringField(ddl='varchar(25)')
    types = StringField(ddl='varchar(5)')
    speed = BooleanField(default=1.0)
    response_time = BooleanField(default=1.0)
    success_times = IntegerField(default=0)
    failure_times = IntegerField(default=0)
    source_url = StringField(ddl='varchar(255)')
    verification_time = BooleanField(default=0.0)

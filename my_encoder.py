# -*- coding=utf-8 -*-
# 
import json
import datetime
from db_schema import DBSchema
from db_table import DBTable
from db_field import DBField

class MyEncoder(json.JSONEncoder):
	def default(self, o):
		print(type(o))
		if isinstance(o, DBSchema):
			return json.dumps(obj=o.__dict__)
		elif isinstance(o, datetime.datetime):
			return o.strptime('%Y-%M-%d %H:%m:%s')
		elif isinstance(o, datetime.date):
			return o.strptime('%Y-%M-%d')
		else:
			return json.JSONEncoder.default(self, o)
# -*- coding=utf-8 -*-
class DBSchema:
	def __init__(self, schema_name):
		self.schema_name = schema_name
		self.table_dict = dict()
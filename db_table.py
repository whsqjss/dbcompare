# -*- coding=utf-8 -*-


class DBTable:
	def __init__(self, table_name, table_type, table_engine, table_comment, data_length):
		self.table_name = table_name
		self.table_type = table_type
		self.table_engine = table_engine
		self.table_comment = table_comment
		self.data_length = data_length
		self.field_dict = dict()
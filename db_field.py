# -*- coding=utf-8 -*-

class DBField:
	def __init__(self, field_name, position, default_value, nullable, \
		data_type, field_comment, data_length, data_precision, data_scale):
		self.field_name = field_name
		self.position = position
		self.default_value = default_value
		self.nullable = nullable
		self.data_type = data_type
		self.field_comment = field_comment
		self.data_length = data_length
		self.data_precision = data_precision
		self.data_scale = data_scale
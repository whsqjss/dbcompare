# -*- coding=utf-8 -*-


class DBIndexField:
	def __init__(self, column_name, non_unique, seq_in_index, index_type, is_visible):
		self.column_name = column_name
		self.non_unique = non_unique
		self.seq_in_index = seq_in_index
		self.index_type = index_type
		self.is_visible = is_visible
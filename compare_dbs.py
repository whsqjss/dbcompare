# -*- coding=utf-8 -*-
import yaml
import pymysql
import sql_const
from db_schema import DBSchema
from db_table import DBTable
from db_field import DBField
from my_encoder import MyEncoder
import json
import pickle
import sys

def getConfig():
	print("********************Get Config********************")

	config_data = None
	with open('config.yaml', 'r', encoding="utf-8") as f:
		file_data = f.read()
		config_data = yaml.load(file_data, Loader=yaml.Loader)

	print('basedb:', config_data['basedb'])
	print('destdb:', config_data['destdb'])
	print('compare_dbs:', config_data['compare_dbs'])
	return config_data


def getDBSchema(db_config, compare_dbs):
	url = db_config['url']
	port = db_config['port']
	username = db_config['username']
	password = db_config['password']
	# get database connection
	mysql_conn = pymysql.connect(host=url, port=port, user=username, password=password)
	mysql_cursor = mysql_conn.cursor()
	try:
		# get all schemas
		schema_list = dict()
		mysql_cursor.execute(sql_const.SHOW_ALL_SCHEMA % ("','".join(compare_dbs)))
		schema_rows = mysql_cursor.fetchall()
		for row in schema_rows:
			schema_name = row[0]
			db_schema = DBSchema(schema_name)
			# get all tables
			mysql_cursor.execute(sql_const.SHOW_ALL_TABLE % (schema_name))
			table_rows = mysql_cursor.fetchall()
			for table_db_row in table_rows:
				table_name = table_db_row[0]
				db_table = DBTable(table_db_row[0], table_db_row[2], table_db_row[3], table_db_row[5], table_db_row[6])
				# get all fields
				mysql_cursor.execute(sql_const.SHOW_ALL_FIELD % (schema_name, table_name))
				field_rows = mysql_cursor.fetchall()
				for field_row in field_rows:
					field_name = field_row[0]
					db_field = DBField(field_row[0], field_row[1], field_row[2], field_row[3], field_row[4], field_row[5], field_row[6], field_row[7], field_row[8])
					db_table.field_dict[field_name] = db_field

				db_schema.table_dict[table_name] = db_table
			schema_list[schema_name] = db_schema
		# print(schema_list)
		return schema_list
		# print(json_str = json.dumps(schema_list, cls=MyEncoder, indent=4))
	except Exception as e:
		print(e)
	finally:
		if mysql_cursor is not None:
			mysql_cursor.close()
		if mysql_conn is not None:
			mysql_conn.close()

def compareSchema(base_dict, dest_dict):
	for base_schema in base_dict:
		if base_schema not in dest_dict:
			print('Schema to Add:', base_schema)

def compareTable(base_dict, dest_dict):
	schema_diff_summary = dict()
	sql_list = []
	for base_schema in base_dict:
		if base_schema in dest_dict:
			to_add_tables = []
			to_modify_tables = dict()
			add_column_sql = []
			dest_schema_obj = dest_dict[base_schema]
			base_schema_obj = base_dict[base_schema]
			base_table_dict = base_schema_obj.table_dict
			dest_table_dict = dest_schema_obj.table_dict
			for table_name in base_table_dict:
				if table_name not in dest_table_dict:
					#add_table_list = to_add_tables[base_schema]
					#if add_table_list is None:
					#	add_table_list = []
					to_add_tables.append(table_name)
					# print('Table to Add:', table_name)
				else:
					table_dest = dest_table_dict[table_name]
					table_base = base_table_dict[table_name]
					to_add_field, to_modify_field, to_add_filed_sql, to_modify_filed_sql = compareFields(base_schema, table_name, table_base, table_dest)
					if len(to_add_field) > 0 or len(to_modify_field) > 0:
						to_modify_tables[table_name] = dict()
						to_modify_tables[table_name]['add'] = to_add_field
						to_modify_tables[table_name]['modify'] = to_modify_field
						to_modify_tables[table_name]['sql'] = to_add_filed_sql + to_modify_filed_sql
						sql_list = sql_list + to_modify_tables[table_name]['sql']
			if len(to_add_tables) > 0 or len(to_modify_tables) > 0:
				schema_diff_summary[base_schema] = {'add_tables': to_add_tables, 'modify_tables': to_modify_tables}
	return schema_diff_summary, sql_list

def compareFields(schema, table_name, table_base, table_dest):
	base_field_dict = table_base.field_dict
	dest_field_dict = table_dest.field_dict
	to_add_field = []
	to_modify_field = []
	to_add_filed_sql = []
	to_modify_filed_sql = []
	for field_name in base_field_dict:
		if field_name not in dest_field_dict:
			field_info = base_field_dict[field_name]
			add_str = '%s %s %s %s %s %s %s %s' % (field_info.field_name, field_info.default_value, field_info.nullable, field_info.data_type, field_info.field_comment, field_info.data_length, field_info.data_precision, field_info.data_scale)
			to_add_field.append(add_str)
			nullable = 'NOT NULL' if field_info.nullable == 'N' else ''
			default_value = ("DEFAULT '" + field_info.default_value + "'") if field_info.default_value is not None else (' DEFAULT NULL' if field_info.nullable == 'Y' else '')
			field_comment = field_info.field_comment if field_info.field_comment is not None else ''
			to_add_filed_sql.append(sql_const.ADD_COLUMN % (schema, table_name, field_info.field_name, field_info.data_type, nullable, default_value, field_info.field_comment))
		else:
			base_field = base_field_dict[field_name]
			dest_field = dest_field_dict[field_name]
			is_modify = False
			if base_field.default_value != dest_field.default_value:
				# print('Field to modify default_value:', table_name + "-", field_name)
				diff_detail = '%s -> %s' % (dest_field.default_value, base_field.default_value)
				to_modify_field.append(field_name + ' - default_value:' + diff_detail)
				is_modify = True
			elif base_field.nullable != dest_field.nullable:
				#print('Field to modify nullable:', table_name + "-", field_name)
				diff_detail = '%s -> %s' % (dest_field.nullable, base_field.nullable)
				to_modify_field.append(field_name + ' - nullable:' + diff_detail)
				is_modify = True
			elif base_field.data_type != dest_field.data_type:
				#print('Field to modify data_type:', table_name + "-", field_name)
				diff_detail = '%s -> %s' % (dest_field.data_type, base_field.data_type)
				to_modify_field.append(field_name + ' - data_type:' + diff_detail)
				is_modify = True
			elif base_field.data_length != dest_field.data_length:
				#print('Field to modify data_length:', table_name + "-", field_name)
				diff_detail = '%s -> %s' % (dest_field.data_length, base_field.data_length)
				to_modify_field.append(field_name + ' - data_length:' + diff_detail)
				is_modify = True
			elif base_field.data_precision != dest_field.data_precision:
				#print('Field to modify data_precision:', table_name + "-", field_name)
				diff_detail = '%s -> %s' % (dest_field.data_precision, base_field.data_precision)
				to_modify_field.append(field_name + ' - data_precision:' + diff_detail)
				is_modify = True
			elif base_field.data_scale != dest_field.data_scale:
				#print('Field to modify data_scale:', table_name + "-", field_name)
				diff_detail = '%s -> %s' % (dest_field.data_scale, base_field.data_scale)
				to_modify_field.append(field_name + ' - data_scale:' + diff_detail)
				is_modify = True

			if is_modify:
				# schema table_name, field_name, field_name, dataType nullable default comment 
				nullable = 'NOT NULL' if base_field.nullable == 'N' else ''
				default_value = ("DEFAULT '"  + base_field.default_value + "'") if base_field.default_value is not None else (' DEFAULT NULL' if base_field.nullable == 'Y' else '')
				field_comment = base_field.field_comment if base_field.field_comment is not None else ''
				to_modify_filed_sql.append(sql_const.MODIFY_COLUMN % (schema, table_name, field_name, field_name, base_field.data_type, nullable, default_value, field_comment))
	return to_add_field, to_modify_field, to_add_filed_sql, to_modify_filed_sql


def compareDB(base_dict, dest_dict):
	print("********************Result********************")
	compareSchema(base_dict, dest_dict)

	schema_diff_summary, sql_list = compareTable(base_dict, dest_dict)

	with open('./result.json', 'w', encoding='utf-8') as f:
		json.dump(schema_diff_summary, f, indent=4, ensure_ascii=False)

	with open('./update.sql', 'w', encoding='utf-8') as f:
		json.dump(sql_list, f, indent=4, ensure_ascii=False)
	print('Tables to modify:', json.dumps(schema_diff_summary, indent=4))



if __name__ == '__main__':
	opera_type = sys.argv[1]
	print(opera_type)
	config_data = getConfig()
	if opera_type == '0':
		basedb = config_data['basedb']
		compare_dbs = config_data['compare_dbs']
		base_schema_dict = getDBSchema(basedb, compare_dbs)
		base = open('./base.pickle', 'wb')
		pickle.dump(base_schema_dict, base)
	elif opera_type == '1':
		destdb = config_data['destdb']
		compare_dbs = config_data['compare_dbs']
		dest_schema_dict = getDBSchema(destdb, compare_dbs)
		with open('./dest.pickle', 'wb') as dest:
			pickle.dump(dest_schema_dict, dest)
	elif opera_type == '2':
		#config_data = getConfig()
		#basedb = config_data['basedb']
		#destdb = config_data['destdb']
		#compare_dbs = config_data['compare_dbs']
		base_schema_dict = None#getDBSchema(basedb, compare_dbs)
		with open('./base.pickle', 'rb') as base:
			base_schema_dict = pickle.load(base)
		dest_schema_dict = None#getDBSchema(destdb, compare_dbs)
		with open('./dest.pickle', 'rb') as dest:
			dest_schema_dict = pickle.load(dest)
		compareDB(base_schema_dict, dest_schema_dict)
import sys

class sql_const:
    # 自定义异常处理
    class ConstError(PermissionError):
        pass
    class ConstCaseError(ConstError):
        pass
    # 重写 __setattr__() 方法
    def __setattr__(self, name, value):
        if name in self.__dict__:  # 已包含该常量，不能二次赋值
            raise self.ConstError("Can't change const {0}".format(name))
        if not name.isupper():  # 所有的字母需要大写
            raise self.ConstCaseError("const name {0} is not all uppercase".format(name))
        self.__dict__[name] = value

# 将系统加载的模块列表中的 constant 替换为 _const() 实例
sql_const = sql_const()

sql_const.SHOW_ALL_SCHEMA = '''
    SELECT lower(schema_name) schema_name
      FROM information_schema.schemata
     WHERE schema_name IN ('%s')
'''

sql_const.SHOW_ALL_TABLE = '''
    SELECT table_name, create_time updated_at, table_type, engine, table_rows num_rows, table_comment,
         concat(truncate(data_length / 1024 / 1024, 2), ' MB') store_capacity
      FROM information_schema.TABLES
     WHERE table_schema = '%s'
'''

sql_const.SHOW_ALL_FIELD = '''
    SELECT lower(column_name) column_name, ordinal_position position, column_default dafault_value, substring(is_nullable, 1, 1) nullable,
            column_type data_type, column_comment, character_maximum_length data_length, numeric_precision data_precision, numeric_scale data_scale
      FROM information_schema.COLUMNS
     WHERE table_schema = '%s'
       AND table_name = '%s'
     ORDER BY position ASC
'''

sql_const.ADD_COLUMN = "ALTER TABLE %s.%s ADD COLUMN %s %s %s %s COMMENT '%s';"

sql_const.MODIFY_COLUMN = "ALTER TABLE `%s`.`%s` CHANGE COLUMN `%s` `%s` %s %s %s COMMENT '%s';"

sys.modules[__name__] = sql_const
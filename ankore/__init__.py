# ankore/__init__.py
import pymysql
import sys

# Override the version to satisfy Django's requirement
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"

# Install as MySQLdb
pymysql.install_as_MySQLdb()

# Also patch the version in the module itself
sys.modules['MySQLdb'] = pymysql
sys.modules['MySQLdb'].version_info = (2, 2, 1, "final", 0)
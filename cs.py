import pyodbc

def Con():
    cnxn_str = 'DRIVER={SQL Server};SERVER=JOSE\\SQLEXPRESS;DATABASE=Proyecto_CS50_1;Trusted_Connection=yes'
    cnxn = pyodbc.connect(cnxn_str)
    return cnxn

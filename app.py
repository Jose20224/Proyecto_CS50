from flask import Flask, render_template, request,redirect, session
from flask_session import Session
from helpers import login_required
from werkzeug.security import generate_password_hash,check_password_hash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename

from cs import Con

import random
import string
import re
import mimetypes
import pyodbc


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



app.config['MAIL_SERVER'] = 'smtp-mail.outlook.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'josefina123456_7@outlook.com'
app.config['MAIL_PASSWORD'] = 'MAMUEL123'
app.config["MAIL_DEFAULT_SENDER"] = 'josefina123456_7@outlook.com'
mail = Mail(app)




cnxn = Con()

@app.route('/')
@login_required
def index():
    if session.get("activo") == 0:
        return redirect('/digitos')
    else:
        # Obtener archivos del usuario actual (ID 1 en este ejemplo)
        cursor = cnxn.cursor()
        cursor.execute(""" select ID From Usuarios where Usuario = ? """,session["userName"])
        usuario_id = cursor.fetchone()[0]

                
        cursor.execute('''
            SELECT ID, NombreArchivo, TipoArchivo, FechaSubida
            FROM Archivos
            WHERE UsuarioID = ?
            ORDER BY FechaSubida DESC
        ''',usuario_id)

        archivos = cursor.fetchall()
        cursor.close()

        # print(archivos)

        return render_template("/index.html",archivos=archivos)
            # return render_template('index.html')



@app.route("/login",methods=["GET","POST"])
def login():
     session.clear()
     if request.method == "GET":
         return render_template("/login.html")
     else:
        user = request.form.get("user")
        passw = request.form.get("pass")

        print(user)
        print(passw)

        if not user:
            return render_template("/login.html")
        elif not passw:
            return render_template("/login.html")

        cursor = cnxn.cursor()

        try:
            cursor.execute("""  select top 1 hash from usuarios where Usuario = ?""",user)
            password = cursor.fetchone()[0]

            cursor.execute("""  select top 1 Activo from usuarios where Usuario = ?""",user)
            activo = cursor.fetchone()[0]
        except:
            error_message = "Credenciales No Validas"
            return render_template("/login.html", error=error_message)
            
        print(password)

        if len(password) ==0:
            return render_template("/login.html")

        elif not passw:
            return render_template("/login.html")

        elif check_password_hash(password,passw):
            session["userName"]=user
            session["activo"] = activo

            if session["activo"] == 1:  # Usuario activo
                return redirect('/')
            return redirect('/digitos')
        else:
            return render_template("login.html", error="Credenciales incorrectas.")
        


@app.route("/register",methods=["GET","POST"])
def register():
    if request.method == "POST":
        User= request.form.get("Username")
        passw=request.form.get("password")
        conf_passw= request.form.get("confir_password")
        correo=request.form.get("Email")

       # Verifica si el nombre de usuario ya existe en la base de datos
        cursor = cnxn.cursor()
        cursor.execute("""SELECT COUNT(*) FROM Usuarios WHERE Usuario = ?""", User)
        user_count = cursor.fetchone()[0]

        if user_count > 0:
            # El nombre de usuario ya está en uso
            error_message = "El nombre de usuario ya está en uso. Por favor, elige otro."
            return render_template("/register.html", error=error_message)
        #genera un patron para verificar si la variable tiene letras,numeros y signos
        # patron = re.compile(r'^(?=.\d)(?=.[a-zA-Z])(?=.*\W).+$')
        # resultado = patron.match(passw)

        if not User:
             return render_template("/register.html")
        elif not passw:
             return render_template("/register.html")
         #contraseña menor de 8 digitos no valido
        # elif len(passw) < 8:
        #     return  render_template("/register.html")
        #aqui validacion del resultado del patron
        # elif not resultado:
        #     return render_template("/register.html")

        elif not conf_passw:
            return render_template("/register.html")
        elif passw != conf_passw:
            return render_template("/register.html")



        #genera el codigo de 8 digitos
        caracteres = string.ascii_letters + string.digits
        Digitos8 = ''.join(random.choice(caracteres) for i in range(8))

        verification_code = Digitos8  # Genera un código de 8 dígitos

        msg = Message('Verificación de correo electrónico', sender='josefina123456_7@outlook.com', recipients=[correo])
        msg.body = f'Tu código de verificación es: {verification_code}'

        mail.send(msg)
        cursor = cnxn.cursor()

        cursor.execute("""  INSERT INTO Usuarios (Usuario,Hash,Correo,Digitos8)
                           VALUES(?,?,?,?)""",User,generate_password_hash(passw),correo,Digitos8)
        cursor.commit()
        cursor.close()
        return redirect("/login")


    else:
        return render_template("/register.html")


@app.route("/logout")
def logout():
    
    session.clear()
   
    return redirect("/login")


@app.route("/digitos", methods=["GET", "POST"])
def si():
    if session.get("userName") is None:
      return redirect("/login")

    if session.get("activo") == 1:
        return redirect("/")

    if request.method == "GET":
      return render_template("digitos.html")
    else:
      cursor = cnxn.cursor()

      cursor.execute("""  SELECT TOP 1 [Digitos8] FROM Usuarios WHERE Usuario = ?  """, session["userName"])
      digitos = cursor.fetchone()[0]

      digitosUser = request.form.get("digitos")

      if digitos == digitosUser:
          cursor.execute("""  UPDATE Usuarios SET Activo = 1 WHERE Usuario = ?  """, session["userName"])
          cursor.commit()
          session["activo"] = 1
      else:
            # El código ingresado es incorrecto, muestra un mensaje de error
            error_message = "Código incorrecto. Por favor, ingrésalo nuevamente."
            return render_template("digitos.html", error=error_message)

      cursor.close()
      return redirect("/")
    


@app.route('/subirArchivo', methods=['POST','GET'])
@login_required
def subirAchivo():
     if request.method == "GET":
      return render_template("subirArchivo.html")
     
     else:

        if 'file' not in request.files:
            return 'No file part'
        file = request.files['file']
        if file.filename == '':
            return 'No selected file'
        if file:
            filename = secure_filename(file.filename)
            file_type = mimetypes.guess_type(filename)[0]
            file_content = file.read()
            file_size = len(file_content)
            

            cursor = cnxn.cursor()
            cursor.execute(""" select ID From Usuarios where Usuario = ? """,session["userName"])
            usuario_id = cursor.fetchone()[0]

            # Guardar en la base de datos
            cursor.execute('''
                INSERT INTO Archivos (NombreArchivo, TipoArchivo, Contenido, Tamaño, UsuarioID)
                VALUES (?, ?, ?, ?, ?)
            ''', (filename, file_type, file_content, file_size, usuario_id))
            cursor.commit()
            cursor.close()
    
            return redirect("/")
    
   

# @app.route("/")
# @login_required
# def MostrarArchivo():
#     # Obtener archivos del usuario actual (ID 1 en este ejemplo)
#     cursor = cnxn.cursor()
#     cursor.execute(""" select ID From Usuarios where Usuario = ? """,session["userName"])
#     usuario_id = cursor.fetchone()[0]

            
#     cursor.execute('''
#          SELECT ID, NombreArchivo, TipoArchivo, FechaSubida
#          FROM Archivos
#          WHERE UsuarioID = ?
#          ORDER BY FechaSubida DESC
#      ''',usuario_id)

#     archivos = cursor.fetchall()
#     cursor.close()

#     print(archivos)

#     return render_template("/index.html", archivos=archivos)



if __name__ == '__main__':
   app.run(host='127.0.0.1', port=8000, debug=True)
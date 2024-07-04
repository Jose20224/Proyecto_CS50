from flask import Flask, render_template, request, redirect, session, abort
from flask_session import Session
from helpers import login_required
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mail import Mail, Message
from werkzeug.utils import secure_filename
import base64
from flask import jsonify, request, send_file
import os
from cs import Con
import io
import random
import string
import re
import mimetypes
import pyodbc


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


app.config["MAIL_SERVER"] = "smtp-mail.outlook.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "josefina123456_7@outlook.com"
app.config["MAIL_PASSWORD"] = "MAMUEL123"
app.config["MAIL_DEFAULT_SENDER"] = "josefina123456_7@outlook.com"
mail = Mail(app)


cnxn = Con()


@app.route("/")
@login_required
def index():
    if session.get("activo") == 0:
        return redirect("/digitos")
    else:
        # Obtener archivos del usuario actual (ID 1 en este ejemplo)
        cursor = cnxn.cursor()
        cursor.execute(
            """ select ID From Usuarios where Usuario = ? """, session["userName"]
        )
        usuario_id = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT ID, NombreArchivo, TipoArchivo, FechaSubida
            FROM Archivos
            WHERE UsuarioID = ?
            ORDER BY FechaSubida DESC
        """,
            usuario_id,
        )

        archivos = cursor.fetchall()
        cursor.close()

        # print(archivos)

        return render_template("/index.html", archivos=archivos)
        # return render_template('index.html')


@app.route("/login", methods=["GET", "POST"])
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
            cursor.execute(
                """  select top 1 hash from usuarios where Usuario = ?""", user
            )
            password = cursor.fetchone()[0]

            cursor.execute(
                """  select top 1 Activo from usuarios where Usuario = ?""", user
            )
            activo = cursor.fetchone()[0]
        except:
            error_message = "Credenciales No Validas"
            return render_template("/login.html", error=error_message)

        print(password)

        if len(password) == 0:
            return render_template("/login.html")

        elif not passw:
            return render_template("/login.html")

        elif check_password_hash(password, passw):
            session["userName"] = user
            session["activo"] = activo

            if session["activo"] == 1:  # Usuario activo
                return redirect("/")
            return redirect("/digitos")
        else:
            return render_template("login.html", error="Credenciales incorrectas.")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        User = request.form.get("Username")
        passw = request.form.get("password")
        conf_passw = request.form.get("confir_password")
        correo = request.form.get("Email")

        # Verifica si el nombre de usuario ya existe en la base de datos
        cursor = cnxn.cursor()
        cursor.execute("""SELECT COUNT(*) FROM Usuarios WHERE Usuario = ?""", User)
        user_count = cursor.fetchone()[0]

        if user_count > 0:
            # El nombre de usuario ya está en uso
            error_message = (
                "El nombre de usuario ya está en uso. Por favor, elige otro."
            )
            return render_template("/register.html", error=error_message)
        # genera un patron para verificar si la variable tiene letras,numeros y signos
        # patron = re.compile(r'^(?=.\d)(?=.[a-zA-Z])(?=.*\W).+$')
        # resultado = patron.match(passw)

        if not User:
            return render_template("/register.html")
        elif not passw:
            return render_template("/register.html")
        # contraseña menor de 8 digitos no valido
        # elif len(passw) < 8:
        #     return  render_template("/register.html")
        # aqui validacion del resultado del patron
        # elif not resultado:
        #     return render_template("/register.html")

        elif not conf_passw:
            return render_template("/register.html")
        elif passw != conf_passw:
            return render_template("/register.html")

        # genera el codigo de 8 digitos
        caracteres = string.ascii_letters + string.digits
        Digitos8 = "".join(random.choice(caracteres) for i in range(8))

        verification_code = Digitos8  # Genera un código de 8 dígitos

        msg = Message(
            "Verificación de correo electrónico",
            sender="josefina123456_7@outlook.com",
            recipients=[correo],
        )
        msg.body = f"Tu código de verificación es: {verification_code}"

        mail.send(msg)
        cursor = cnxn.cursor()

        cursor.execute(
            """  INSERT INTO Usuarios (Usuario,Hash,Correo,Digitos8)
                           VALUES(?,?,?,?)""",
            User,
            generate_password_hash(passw),
            correo,
            Digitos8,
        )
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

        cursor.execute(
            """  SELECT TOP 1 [Digitos8] FROM Usuarios WHERE Usuario = ?  """,
            session["userName"],
        )
        digitos = cursor.fetchone()[0]

        digitosUser = request.form.get("digitos")

        if digitos == digitosUser:
            cursor.execute(
                """  UPDATE Usuarios SET Activo = 1 WHERE Usuario = ?  """,
                session["userName"],
            )
            cursor.commit()
            session["activo"] = 1
        else:
            # El código ingresado es incorrecto, muestra un mensaje de error
            error_message = "Código incorrecto. Por favor, ingrésalo nuevamente."
            return render_template("digitos.html", error=error_message)

        cursor.close()
        return redirect("/")


@app.route("/subirArchivo", methods=["POST", "GET"])
@login_required
def subirAchivo():
    if request.method == "GET":
        return render_template("subirArchivo.html")
    else:
        if "file" not in request.files:
            return render_template(
                "/subirArchivo.html", error="No se ha seleccionado ningún archivo."
            )

        file = request.files["file"]
        if file.filename == "":
            return render_template(
                "/subirArchivo.html", error="No se ha seleccionado ningún archivo."
            )

        if file:
            filename = secure_filename(file.filename)
            file_type = mimetypes.guess_type(filename)[0]
            file_content = file.read()
            file_size = len(file_content)

            # Verificar el tamaño del archivo
            if file_size > 5 * 1024 * 1024:  # 5 MB
                return render_template(
                    "/subirArchivo.html", error="El archivo supera el límite de 5 MB."
                )

            cursor = cnxn.cursor()
            cursor.execute(
                """SELECT ID FROM Usuarios WHERE Usuario = ?""", session["userName"]
            )
            usuario_id = cursor.fetchone()[0]

            try:
                # Intentar insertar el archivo en la base de datos
                cursor.execute(
                    """
                    INSERT INTO Archivos (NombreArchivo, TipoArchivo, Contenido, Tamaño, UsuarioID)
                    VALUES (?, ?, ?, ?, ?)
                """,
                    (
                        filename,
                        file_type,
                        pyodbc.Binary(file_content),
                        file_size,
                        usuario_id,
                    ),
                )
                cursor.commit()
                cursor.close()

                return redirect("/")
            except pyodbc.Error as e:
                error_message = f"Error al subir archivo: {str(e)}"
                return render_template("/subirArchivo.html", error=error_message)


@app.route("/archivo/<int:id>", methods=["GET", "DELETE", "PUT"])
@login_required
def archivo(id):
    if request.method == "GET":
        cursor = cnxn.cursor()
        cursor.execute(
            """
            SELECT NombreArchivo, TipoArchivo, Contenido
            FROM Archivos
            WHERE ID = ?
            """,
            id,
        )
        archivo = cursor.fetchone()
        cursor.close()

        if archivo:
            nombre_archivo, tipo_archivo, contenido = archivo
            contenido_base64 = base64.b64encode(contenido).decode("utf-8")
            return jsonify(
                {
                    "nombre": nombre_archivo,
                    "tipo": tipo_archivo,
                    "contenido": contenido_base64,
                }
            )
        else:
            return jsonify({"error": "Archivo no encontrado"}), 404

    elif request.method == "DELETE":
        cursor = cnxn.cursor()
        cursor.execute(
            """
            SELECT NombreArchivo
            FROM Archivos
            WHERE ID = ?
            """,
            id,
        )
        archivo = cursor.fetchone()

        if archivo:
            nombre_archivo = archivo[0]

            # Eliminar el archivo de la base de datos
            cursor.execute(
                """
                DELETE FROM Archivos
                WHERE ID = ?
                """,
                id,
            )
            cnxn.commit()

            # Eliminar también el archivo físico si está almacenado localmente
            ruta_archivo = os.path.join(app.config["UPLOAD_FOLDER"], nombre_archivo)
            if os.path.exists(ruta_archivo):
                os.remove(ruta_archivo)

            return jsonify({"message": "Archivo eliminado correctamente"})
        else:
            return jsonify({"error": "Archivo no encontrado"}), 404

    elif request.method == "PUT":
        nuevo_nombre = request.json.get("nuevoNombre")
        if not nuevo_nombre:
            return jsonify({"error": "Debe proporcionar un nuevo nombre"}), 400

        cursor = cnxn.cursor()
        cursor.execute(
            """
            UPDATE Archivos
            SET NombreArchivo = ?
            WHERE ID = ?
            """,
            (nuevo_nombre, id),
        )
        cnxn.commit()

        return jsonify({"message": "Nombre del archivo cambiado correctamente"})


@app.route("/buscar_archivos")
@login_required
def buscar_archivos():
    query = request.args.get("q", "").lower()
    cursor = cnxn.cursor()
    cursor.execute(
        """
        SELECT ID, NombreArchivo, TipoArchivo, FechaSubida
        FROM Archivos
        WHERE LOWER(NombreArchivo) LIKE ?
        """,
        f"%{query}%",
    )
    archivos = cursor.fetchall()
    cursor.close()

    archivos_list = [
        {
            "ID": archivo.ID,
            "NombreArchivo": archivo.NombreArchivo,
            "TipoArchivo": archivo.TipoArchivo,
            "FechaSubida": archivo.FechaSubida,
        }
        for archivo in archivos
    ]

    return jsonify(archivos_list)


@app.route("/configuracion", methods=["GET", "POST"])
@login_required
def configuracion():
    cursor = cnxn.cursor()
    cursor.execute(
        """SELECT Usuario, Correo FROM Usuarios WHERE Usuario = ?""",
        session["userName"],
    )
    usuario_data = cursor.fetchone()
    cursor.close()

    if request.method == "GET":
        return render_template(
            "configuracion.html", userName=usuario_data[0], userEmail=usuario_data[1]
        )
    else:
        new_username = request.form.get("username")
        new_email = request.form.get("email")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if "profile_picture" in request.files:
            profile_picture = request.files["profile_picture"]
            profile_picture_content = profile_picture.read()
        else:
            profile_picture_content = None

        updates = []
        update_values = []

        # Verifica si el nombre de usuario ha cambiado
        if new_username and new_username != usuario_data[0]:
            updates.append("Usuario = ?")
            update_values.append(new_username)
            session["userName"] = new_username

        # Verifica si el correo ha cambiado
        if new_email and new_email != usuario_data[1]:
            updates.append("Correo = ?")
            update_values.append(new_email)

        # Verifica si se ha cargado una nueva foto de perfil
        if profile_picture_content:
            updates.append("FotoPerfil = ?")
            update_values.append(profile_picture_content)

        # Verifica la contraseña actual si se está cambiando la contraseña
        if current_password and new_password and confirm_password:
            cursor = cnxn.cursor()
            cursor.execute(
                """SELECT hash FROM Usuarios WHERE Usuario = ?""", session["userName"]
            )
            current_hash = cursor.fetchone()[0]

            if not check_password_hash(current_hash, current_password):
                error_message = "La contraseña actual es incorrecta."
                return render_template(
                    "configuracion.html",
                    userName=usuario_data[0],
                    userEmail=usuario_data[1],
                    error=error_message,
                )

            if new_password != confirm_password:
                error_message = "La nueva contraseña y la confirmación no coinciden."
                return render_template(
                    "configuracion.html",
                    userName=usuario_data[0],
                    userEmail=usuario_data[1],
                    error=error_message,
                )

            new_password_hash = generate_password_hash(new_password)
            updates.append("Hash = ?")
            update_values.append(new_password_hash)

        if updates:
            # Realiza la actualización solo si hay cambios
            update_query = f"UPDATE Usuarios SET {', '.join(updates)} WHERE Usuario = ?"
            update_values.append(session["userName"])
            cursor = cnxn.cursor()
            cursor.execute(update_query, update_values)
            cursor.commit()
            cursor.close()

        return redirect("/configuracion")


@app.route("/archivo/<int:id>/descargar", methods=['GET'])
@login_required
def descargar_archivo(id):
    try:
        cursor = cnxn.cursor()
        cursor.execute("""
            SELECT NombreArchivo, TipoArchivo, Contenido
            FROM Archivos
            WHERE ID = ?
        """, id)
        archivo = cursor.fetchone()
        cursor.close()

        if archivo:
            nombre_archivo, tipo_archivo, contenido = archivo
            return send_file(
                io.BytesIO(contenido),
                mimetype=tipo_archivo,
                as_attachment=True,
                download_name=nombre_archivo
            )
        else:
            return jsonify({"error": "Archivo no encontrado"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

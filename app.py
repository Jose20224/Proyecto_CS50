from flask import Flask, render_template, request, redirect, session,url_for
from werkzeug.security import generate_password_hash, check_password_hash
from condicionales import condi_subirArchivos,codi_colores
from flask import jsonify, request, send_file
from PIL import Image, ImageDraw, ImageFont
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from helpers import login_required
from flask_session import Session
from cs import Con

import mimetypes
import base64
import random
import string
import pyodbc
import os
import io



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
            SELECT ID, NombreArchivo, formatoAchi, FechaSubida
            FROM Archivos
            WHERE UsuarioID = ?
            ORDER BY FechaSubida DESC
        """,
            usuario_id,
        )

        archivos = cursor.fetchall()
        cursor.close()
        return render_template("/index.html", archivos=archivos,usuario=session["userName"])



@app.route('/perfil/foto')
@login_required
def perfil_foto():
    cursor = cnxn.cursor()
    cursor.execute(
            """ SELECT FotoPerfil FROM Usuarios WHERE Usuario = ?""", session["userName"]
    )
    row = cursor.fetchone()
    if row and row.FotoPerfil:
        return send_file(io.BytesIO(row.FotoPerfil), mimetype='image/jpeg')
    else:
        # Generar una imagen con la inicial del usuario
        cursor.execute('SELECT Usuario FROM Usuarios WHERE Usuario = ?',session["userName"])
        usuario = cursor.fetchone().Usuario
        inicial = usuario[0].upper()
        # Aquí puedes generar una imagen con la inicial (usar PIL o similar)
        from PIL import Image, ImageDraw, ImageFont
        img = Image.new('RGB', (100, 100), color = (73, 109, 137))
        d = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 80)
        d.text((10, 10), inicial, fill=(255, 255, 0), font=font)
        img_io = io.BytesIO()
        img.save(img_io, 'JPEG')
        img_io.seek(0)
        return send_file(img_io,mimetype='image/jpeg')


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
        
        cursor = cnxn.cursor()
        cursor.execute("""SELECT COUNT(*) FROM Usuarios WHERE Correo = ?""", correo)
        Correo_count = cursor.fetchone()[0]
        
        if Correo_count > 0:
            # El nombre de usuario ya está en uso
            error_message = (
                "El Correo del usuario ya está en uso. Por favor, elige otro."
            )
            return render_template("/register.html", error=error_message)


        if not User:
            return render_template("/register.html")
        elif not passw:
            return render_template("/register.html")
        elif not conf_passw:
            return render_template("/register.html")
        elif passw != conf_passw:
            return render_template("/register.html")
        elif not correo:
            return  render_template("/register.html")

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
def subirArchivo():
    if request.method == "GET":
        return render_template("subirArchivo.html", usuario=session["userName"])
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

            tipo = condi_subirArchivos(file_type)
            cursor = cnxn.cursor()
            cursor.execute(
                """SELECT ID FROM Usuarios WHERE Usuario = ?""", session["userName"]
            )
            usuario_id = cursor.fetchone()[0]

            try:
                # Intentar insertar el archivo en la base de datos
                cursor.execute(
                    """
                    INSERT INTO Archivos (NombreArchivo, TipoArchivo,formatoAchi, Contenido, Tamaño, UsuarioID)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        filename,
                        file_type,
                        tipo,
                        pyodbc.Binary(file_content),
                        file_size,
                        usuario_id,
                    ),
                )
                cnxn.commit()  # Confirmar la transacción
                cursor.close()

                return redirect("/")
            except pyodbc.Error as e:
                print(e)
                error_message = f"Error al subir archivo"
                return render_template("/subirArchivo.html", error=error_message)
            

@app.route('/imagen_formato/<formato>')
def imagen_formato(formato):
    if formato == "Imagen":
        letra = "Img"
    elif formato == "PowerPoint":
        letra="PW"
    else:
        letra = formato[0].upper()
    
    colorFondo = codi_colores(formato)
    
    # Crear una imagen
    img = Image.new('RGB', (100, 100), color=colorFondo)
    d = ImageDraw.Draw(img)

    try:
        if formato == "Imagen" or formato == "PowerPoint":
            font = ImageFont.truetype("verdana.ttf", 45)
        else:
            font = ImageFont.truetype("verdana.ttf", 50)
    except IOError:
        font = ImageFont.load_default()

    # Dibujar la sombra de la letra en la imagen
    shadow_offset = 4
    shadow_color = (0, 0, 0)
    bbox = d.textbbox((0, 0), letra, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    d.text(
        ((100 - text_width) / 2 + shadow_offset, (100 - text_height) / 2 + shadow_offset - 10),
        letra,
        fill=shadow_color,
        font=font
    )

    # Dibujar la letra en la imagen
    bbox = d.textbbox((0, 0), letra, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    d.text(
        ((100 - text_width) / 2, (100 - text_height) / 2 - 10),
        letra,
        fill=(255, 255, 255),
        font=font
    )

    # Guardar la imagen en un objeto BytesIO
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png')
    



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
    cursor.execute("""SELECT ID FROM Usuarios WHERE Usuario = ?""",session["userName"])
    user_count = cursor.fetchone()[0]
    print(user_count)
    cursor = cnxn.cursor()
    cursor.execute(
        """
        SELECT ID, NombreArchivo, TipoArchivo, FechaSubida,formatoAchi
        FROM Archivos
        WHERE UsuarioID = ? and LOWER(NombreArchivo) LIKE ?
        """,user_count,
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
            "formatoAchi": archivo.formatoAchi,     
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
            "configuracion.html", userName=usuario_data[0], userEmail=usuario_data[1],usuario=session["userName"]
        )
    else:
        new_username = request.form.get("username")
        # new_email = request.form.get("email")
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


MIME_TO_EXTENSION = {
    "application/pdf": ".pdf",
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "application/vnd.ms-excel": ".xls",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
    "application/zip": ".zip",  
    "application/x-rar-compressed": ".rar",
    "text/plain": ".txt",
    # Añaden cualquier extension de archivos jose y laureano
}

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
            
            # Verificar que el tipo de archivo esté en nuestro mapeo
            extension = MIME_TO_EXTENSION.get(tipo_archivo)
            if not extension:
                return jsonify({"error": "Tipo de archivo no soportado"}), 400

            # Agregar la extensión al nombre del archivo si falta
            if not nombre_archivo.endswith(extension):
                nombre_archivo += extension
            
            # Usar `send_file` para enviar el archivo con el tipo MIME correcto y el nombre de archivo
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

@app.route("/forget", methods=["GET", "POST"])
def forget():
    if request.method == "GET":
        return render_template("forget.html")
    
    else:
        email = request.form.get("correo")

        if not email:
            return render_template("forget.html", error="No se ha proporcionado un correo")
        
        cursor = cnxn.cursor()
        cursor.execute(""" SELECT Correo FROM Usuarios WHERE Correo = ? """, email)
        correo = cursor.fetchone()[0]
        cursor.close()

        if not correo:
            return render_template("forget.html", error="Correo inexistente")
        
        return redirect(url_for("recover", correo=email))

@app.route("/recover/<correo>", methods=["GET", "POST"])
def recover(correo):
    if not correo:
        return redirect("/login")

    if request.method == "GET":
        return render_template("recover.html", mail=correo)
    
    else:
        passw = request.form.get("password")
        confirmation = request.form.get("confir_password")
        code = request.form.get("code")

        if not passw or not confirmation or not code:
            return render_template("recover.html", error="No pueden haber campos vacios")
        
        cursor = cnxn.cursor()
        cursor.execute(""" SELECT Digitos8 FROM Usuarios WHERE Correo = ? """, correo)
        codigo = cursor.fetchone()[0]

        if code != codigo:
            return render_template("recover.html", error="Codigo incorrecto")
        
        cursor.execute(""" UPDATE Usuarios SET hash = ? WHERE Correo = ?""", generate_password_hash(passw), correo)
        cursor.commit()
        cursor.close()

        return redirect("/login")
    
@app.route("/recoverCode/<correo>", methods=["GET", "POST"])
def recoverCode(correo):
    if request.method == "GET":
        session["activo"] = 0

        cursor = cnxn.cursor()

        cursor.execute(""" UPDATE Usuarios SET Activo = 0 WHERE Correo = ? """, correo)
        cursor.commit()

        caracteres = string.ascii_letters + string.digits
        Digitos8 = "".join(random.choice(caracteres) for i in range(8))

        verification_code = Digitos8

        msg = Message(
            "Verificación de correo electrónico",
            sender="josefina123456_7@outlook.com",
            recipients=[correo],
        )
        msg.body = f"Tu nuevo código de verificación es: {verification_code}"

        mail.send(msg)

        cursor.execute(""" UPDATE Usuarios SET Digitos8 = ? WHERE Correo = ? """, verification_code, correo)
        cursor.commit()
        cursor.close()

        return render_template("recoverCode.html")
    
    else:
        code = request.form.get("code")

        cursor = cnxn.cursor()
        cursor.execute(""" SELECT Digitos8 FROM Usuarios WHERE Correo = ? """, correo)
        codigo = cursor.fetchone()[0]

        if code != codigo:
            return render_template("recoverCode.html", error="Codigo invalido, se le envió otro codigo")

        cursor.close()

        return redirect(url_for("recover", correo=correo))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000, debug=True)

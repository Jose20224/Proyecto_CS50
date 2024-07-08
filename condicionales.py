def condi_subirArchivos(dato):
    if (dato == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"):
        return "Word"
    elif(dato == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"):
        return "Excel"
    elif(dato == "application/vnd.openxmlformats-officedocument.presentationml.presentation"):
        return "PowerPoint"
    elif(dato == "application/x-zip-compressed"):
        return "Zip"
    elif (dato == "text/plain"):
        return "txt"
    elif ("image" in dato):
        return "Imagen"
    elif (dato == "application/pdf"):
        return "PDF"
    else:
        return "Archivo"

def codi_colores(dato):
    if (dato == "Word"):
        return 5, 46, 168
    elif(dato == "Excel"):
        return 6, 129, 20
    elif(dato == "Zip"):
        return 235, 85, 5
    elif (dato == "txt"):
        return 105, 114, 100
    elif (dato == "Imagen"):
        return 21, 162, 186
    elif (dato == "PDF"):
        return 168, 24, 5
    elif (dato == "PowerPoint"):
        return 224, 24, 6
    else:
        return 0, 139, 139
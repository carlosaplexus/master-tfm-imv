-DIARIO DE NOTAS TECNICAS-
--------------------------

* Limpiar el Makefile desde Windows (error: Makefile:18: *** missing separator.  Stop.)
    1) Convertir el archivo a formato Linux (LF)
        Con VS Code:
            Cambiar CRLF a LF
            Guarda el archivo
            Esto elimina los \r que rompen Make.

    2) Reemplazar espacios por TAB reales
        Con VS Code:
            Seleccionar todo el archivo
            Pulsar Ctrl+Shift+P
            Escribir: Convert Indentation to Tabs y pulsar enter
            Ahora todas las líneas que empiezan con comandos tendrán TAB reales
            Guardar archivo y probar Make
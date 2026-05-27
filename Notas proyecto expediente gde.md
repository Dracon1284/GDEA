#proyecto #GDE
Objetivo: crear un programa que recepte un archivo zip con PDF, lo procese y genere información analítica así como otros PDF. El programa debe ejecutarse todo en local y que pueda ser portable para llevarlo de un disposito a otro.
Proceso:
Menu de inicio
Cuando se inicia el programa, lo llamaremos GDEA se habré la terminal donde te da la bienvenida, apareciendo los reportes que se realizaran y aparecen tres opciones:
- Presionando 1 iniciar
- Presionando 2 va a menu opciones
- Presionando 3 salir

Cuando inicia el programa te va a pedir la ruta y archivo zip con el que se trabajará, se presiona enter (válida que exista el archivo y que el archivo empiece con "EX-") y luego se escribe la ruta donde se guardarán los reportes. Se toca enter e inicia el programa. Para volver atrás de tendría que tocar escape o poner un valor específico.

Crear un programa que una vez expediente electronico zip, lo comience a trabajar, realizando las siguientes tareas. Primero, extrae la documentación en una carpeta, luego empieza a extraer la información (detalle en ![[Datos extrarer]]), generando una base de datos temporal para la generación de reportes que incluirán:
- informe en archivo txt conteniendo los datos de la carátula expediente (es un archivo PV que dice "Carátula Expediente"), al que se le suma la cantidad de documentos, la cantidad de archivos embebidos y el log de fecha y hora de generación del expediente.
- un archivo cvs que contendrá el índice con la información de los registros de cada documento conteniendo los siguientes campos: número_de_orden, número_de_documento, fecha_documento, referencia, cantidad_de_paginas, cantidad de archivos embebidos cantidad de firmantes, datos del último firmante (UF) que incluyen CUIT_UF, nombre_UF, cargo_UF, area_UF)
- en caso de que existan archivos embebidos se generara una sub carpeta con el nombre del número de orden y se colocarán los archivos embebidos. En caso de haber PDF adentro de los embebidos se tendrá que analizar si ese archivo tiene embebidos, generando otra sub carpeta con el número de orden más un guión y un número de serie ( ejemplo 0001-001), así sucesivamente.
- se generara un archivo sin embebidos que consolide todos los documentos, se le aplicará aplanar y ocr a todas las páginas. En caso de que la cantidad de documentos supere los 100 se preguntara si desea seccionar el total de documentos cada 100.
- reporte cvs que va a contener registro por cada firmante de los documentos que contendrá número_de_orden, codigo_documento, fecha_documento, nombre_firmante, CUIT_firmante, fecha_firma, cargo_firmante y area_firmante
- reporte cvs que para los documentos tipo ME y NO, detallará cada registro de quien recibió la información de cada documento teniendo los campos numero_orden, codigo_documento, fecha_documento, A/COPIA_A, nombre y área 

Cada uno de dichos puntos representa un reporte que puede seleccionarse si se aplica, o no, en el menú de opciones.
Adicionalmente, habría que agregar un validador al iniciar el proceso también verifique que no se haya procesado en el lugar que se decida generar los reportes 
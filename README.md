#Chatbot URC con telegram

Repositorio para crear un bot en telegram basico utilizando la biblioteca TeleBot de python

## Configuracion
1.Clonar el repositorio
2.Instala las dependencias usando 'pip install -r requeriments.txt'
3.Crear el bot en telegrama travex de BotFather y obten el token
4.Reemplaza el token en el fichero
5.ejecutar el bot usando el comando 'python main.py'

## Estructura del codigo
telebot para la comunicación con la API de Telegram, pdfminer para extraer texto de archivos PDF, json para manejar archivos JSON, re para expresiones regulares, unicodedata para normalización de texto, nltk para procesamiento de lenguaje natural, y scikit-learn para vectores TF-IDF y cálculo de similitud coseno.
la funcion normalizar texto toma un textoc como entrada y realiza varias transformaciones para normalizarlo primero se utiliza ##unicodedata para eliminar caracteres acentuados o especiales, luego convierte el texto en minusculas y elimina cualquier caracter que no sea de tipo alfanumerico.

la funcion crear indice, recorre todos los archivos pdf en la ruta, y crea un indice para los archivos pdf, para cada uno de los archivos, se utiliza pdfminer, normalizandolo con la funcion normalizar texto, luego esto se agrega a un diccionario llamado indice pdf y despues. se guarda en un archivio jason papu
 
buscar informacion toma un texto de entrada,(teclado) y busca el indice de los archivos pdf utilizando TF-IDF para encontrar la similutud utilizando algo de cosenos papu, normalizando el texto de entrada, luego esta entrada lse tranforma en un vextor TF-idf y despues se calcula la similitud de las dos matrices, encuentra el indice del documento con la similitud mas alta y devuelve el contenido junto con su nombre
## funciones de botones, preguntas frecuentes
apartir de las funciones basicas de telebot, la definicion de botones para acceder de mejor manera a algunos apartados
import telebot
import os
import json
import re
import unicodedata
from pdfminer.high_level import extract_text
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

# Inicialización del chatbot
TOKEN = '6991585186:AAEeWdsAnHqp2hm_QR6PJpegtrquqGyKukc'
bot = telebot.TeleBot(TOKEN)

# Ruta de la base de datos
DATABASE_PATH = 'C:\\Users\\Daniel Garcia\\Documents\\•Proyecto Prototipico Chat Bot\\database'

# Cargar stopwords en español
stopwords_spanish = stopwords.words('spanish')

# Función para normalizar el texto
def normalize_text(text):
    text = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('utf-8')
    text = text.lower()
    text = re.sub(r'\W+', ' ', text)
    return text

# Función para dividir texto en capítulos
def split_into_chapters(text):
    chapters = {}
    chapter_pattern = re.compile(r'cap[íi]tulo\s+\d+', re.IGNORECASE)
    sections = re.split(chapter_pattern, text)
    headers = re.findall(chapter_pattern, text)

    for i, section in enumerate(sections[1:], start=1):
        chapters[f'capítulo {i}'] = section.strip()

    return chapters

# Función para crear el índice de archivos PDF
def create_pdf_index():
    pdf_index = {}
    locations = {}

    for root, _, files in os.walk(DATABASE_PATH):
        for file in files:
            if file.endswith('.pdf'):
                file_path = os.path.join(root, file)
                try:
                    text = extract_text(file_path)
                    text = normalize_text(text)
                    chapters = split_into_chapters(text)
                    pdf_index[file] = {
                        "content": text,
                        "chapters": chapters,
                        "path": file_path
                    }

                    # Extraer ubicaciones si el archivo está relacionado con ubicaciones
                    if 'ubicacion' in file.lower():
                        for line in text.split('\n'):
                            if 'latitud' in line and 'longitud' in line:
                                match = re.search(r'(.+)\s+latitud:\s+([-+]?\d{1,2}\.\d+)\s+longitud:\s+([-+]?\d{1,3}\.\d+)', line)
                                if match:
                                    name, latitude, longitude = match.group(1).strip(), float(match.group(2)), float(match.group(3))
                                    locations[name] = (latitude, longitude)
                except Exception as e:
                    print(f"Error al leer el archivo PDF {file}: {e}")

    with open('pdf_index.json', 'w') as f:
        json.dump(pdf_index, f)

    with open('locations.json', 'w') as f:
        json.dump(locations, f)

create_pdf_index()

# Cargar el índice de archivos PDF
with open('pdf_index.json', 'r') as f:
    pdf_index = json.load(f)

# Cargar ubicaciones desde el archivo JSON
with open('locations.json', 'r') as f:
    locations = json.load(f)

# Preparar los datos para TF-IDF
documents = [info['content'] for info in pdf_index.values()]
file_names = list(pdf_index.keys())

# Vectorizar el contenido de los documentos
vectorizer = TfidfVectorizer(stop_words=stopwords_spanish)
tfidf_matrix = vectorizer.fit_transform(documents)

# Función para buscar en el índice utilizando TF-IDF y similitud coseno
def search_info(query):
    query = normalize_text(query)
    query_vec = vectorizer.transform([query])
    similarities = cosine_similarity(query_vec, tfidf_matrix).flatten()
    best_match_index = np.argmax(similarities)
    best_match_score = similarities[best_match_index]

    if best_match_score > 0:
        return documents[best_match_index], file_names[best_match_index]
    return None, None

# Función para enviar más información
def send_more_info(message, content, file_name, start_index):
    chunk_size = 500
    end_index = start_index + chunk_size
    text_to_send = content[start_index:end_index]

    markup = telebot.types.InlineKeyboardMarkup()
    if end_index < len(content):
        # Asegurar que el callback_data no exceda los 64 bytes
        callback_data = f"more_info_{end_index}_{file_name[:30]}"
        if len(callback_data) > 64:
            callback_data = callback_data[:64]
        markup.add(telebot.types.InlineKeyboardButton("¿Quieres saber más?", callback_data=callback_data))
    markup.add(telebot.types.InlineKeyboardButton("Página de la Universidad", url="https://rcastellanos.cdmx.gob.mx/"))
    markup.add(telebot.types.InlineKeyboardButton("Ver lista de PDF disponibles", callback_data="list_pdfs"))

    try:
        bot.send_message(message.chat.id, text_to_send, parse_mode='Markdown', reply_markup=markup)
    except telebot.apihelper.ApiException as e:
        # Si se produce un error al enviar el mensaje, dividir el texto en partes más pequeñas
        parts = [content[i:i+chunk_size] for i in range(0, len(content), chunk_size)]
        for part in parts:
            bot.send_message(message.chat.id, part, parse_mode='Markdown', reply_markup=markup)

# Función para manejar los mensajes
@bot.message_handler(func=lambda m: True)
def handle_messages(message):
    text = message.text.lower()
    greetings = ['hola', 'buenos días', 'buenas tardes', 'buenas noches']
    if text in greetings:
        bot.reply_to(message, '¡Hola! ¿En qué puedo ayudarte hoy? ')
        return
    for location in locations:
        if location.lower() in text:
            latitude, longitude = locations[location]
            google_maps_link = f"https://www.google.com/maps/search/?api=1&query={latitude},{longitude}"

            # Create a clickable link for the location using Markdown formatting
            location_link = f"[{location}]({google_maps_link})"  # Wrap location in [] and link in ()
            bot.send_message(message.chat.id, f"Puedes ver la ubicación de {location_link} en el siguiente enlace:", parse_mode='Markdown')
            return
    chapter_match = re.match(r'cap[íi]tulo\s+\d+', text)
    if chapter_match:
        chapter = chapter_match.group(0)
        for file_name, info in pdf_index.items():
            if chapter in info['chapters']:
                content = info['chapters'][chapter]
                bot.send_message(message.chat.id, f"Esto es lo que encontré en {chapter}:\n\n{content[:500]}...", parse_mode='Markdown')
                send_more_info(message, content, file_name, 500)
                return

    response, file = search_info(message.text)
    if response:
        formatted_response = f"Esto es lo que encontré sobre tu consulta:\n\n{response[:500]}..."
        bot.send_message(message.chat.id, formatted_response, parse_mode='Markdown')
        send_more_info(message, response, file, 500)
    else:
        bot.send_message(message.chat.id, 'Lo siento, no encontré información relacionada con tu pregunta. ¿Necesitas algo específico? Si necesitas ayuda, por favor contáctanos.')


# Función para manejar las respuestas de más información
@bot.callback_query_handler(func=lambda call: call.data.startswith("more_info_"))
def handle_more_info_callback(call):
    _, end_index, file_name = call.data.split('_', 2)
    end_index = int(end_index)
    content = pdf_index[file_name]['content']
    send_more_info(call.message, content, file_name, end_index)

# Función para manejar la lista de PDFs disponibles
@bot.callback_query_handler(func=lambda call: call.data == "list_pdfs")
def list_pdfs(call):
    markup = telebot.types.InlineKeyboardMarkup()
    for file_name in pdf_index.keys():
        # Asegurar que el callback_data no exceda los 64 bytes
        callback_data = f"pdf_{file_name[:30]}"
        if len(callback_data) > 64:
            callback_data = callback_data[:64]
        markup.add(telebot.types.InlineKeyboardButton(file_name, callback_data=callback_data))
    bot.send_message(call.message.chat.id, "Lista de PDFs disponibles:", reply_markup=markup)

# Función para manejar la selección de un PDF específico
@bot.callback_query_handler(func=lambda call: call.data.startswith("pdf_"))
def pdf_callback(call):
  file_name = call.data[len("pdf_"):]
  # Check if the file_name exists in the dictionary before accessing it
  if file_name in pdf_index:
      file_path = pdf_index[file_name]['path']
      with open(file_path, 'rb') as f:
          bot.send_document(call.message.chat.id, f, caption=file_name)
  else:
      # Handle the case where the file is not found
      bot.send_message(call.message.chat.id, "Lo sentimos, el archivo solicitado no se encontró. Intenta con otro archivo.")

# Función para manejar el botón de información específica
@bot.message_handler(func=lambda message: message.text == '¿Necesitas algo muy específico?')
def specific_info(message):
    bot.send_message(message.chat.id, "Por favor, dime qué información específica necesitas. Si necesitas ayuda, por favor contáctanos.")

# Función para manejar el botón de la página de la universidad
@bot.message_handler(func=lambda message: message.text == 'Página de la Universidad')
def university_page(message):
    bot.send_message(message.chat.id, "Puedes visitar la página de la Universidad Rosario Castellanos en: https://rcastellanos.cdmx.gob.mx/ Si necesitas ayuda, por favor contáctanos.")

# Función para manejar errores generales
@bot.message_handler(func=lambda message: True)
def handle_error(message):
    try:
        # Aquí va el código que quieres ejecutar
        pass
    except Exception as e:
        # Aquí manejas el error
        bot.reply_to(message, "Oops! Algo salió mal. Si necesitas ayuda, por favor contáctanos.")

bot.polling()

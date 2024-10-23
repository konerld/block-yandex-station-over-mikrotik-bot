import paramiko
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext
from loguru import logger
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()


# Teleagram
TOKEN = os.getenv('TOKEN')
ALLOWED_CHAT_IDS = os.getenv('ALLOWED_CHAT_IDS')
if ALLOWED_CHAT_IDS:
    ALLOWED_CHAT_IDS = list(map(int, ALLOWED_CHAT_IDS.split(',')))

# SSH данные
SSH_HOST = os.getenv('SSH_HOST')
SSH_PORT = os.getenv('SSH_PORT')
SSH_USER = os.getenv('SSH_USER')
SSH_PASSWORD = os.getenv('SSH_PASSWORD')

# Команды для включения и выключения
cmd = '/ip firewall filter {} [find comment="Block YaStNano"]'
# Отключить станцию (включить блокировку)
SSH_COMMAND_OFF = cmd.format('enable')
# Включить станцию (отключить блокировку
SSH_COMMAND_ON = cmd.format('disable')


# Функция для выполнения команды по SSH
def execute_ssh_command(command):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(SSH_HOST, port=SSH_PORT, username=SSH_USER, password=SSH_PASSWORD)

        stdin, stdout, stderr = ssh.exec_command(command)
        logger.info(f'Send cmd: {command}')
        output = stdout.read().decode('utf-8')
        logger.info(f'Output: {output}')
        error = stderr.read().decode('utf-8')

        ssh.close()

        return output if output else error
    except Exception as e:
        logger.error(f"SSH command execution failed: {e}")
        return f"Error: {str(e)}"

# Проверка, имеет ли пользователь доступ
def is_user_allowed(chat_id):
    return chat_id in ALLOWED_CHAT_IDS

# Команда /start
def start(update: Update, context: CallbackContext):
    chat_id = update.message.chat.id

    if not is_user_allowed(chat_id):
        msg = f"У вас нет доступа к этому боту. chat_id: {chat_id}"
        update.message.reply_text(msg)
        logger.error(msg)
        return

    # Создаем кнопки
    keyboard = [
        [
            InlineKeyboardButton("ON ✅\n\n", callback_data='on'),
            InlineKeyboardButton("OFF ❌\n\n", callback_data='off')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text('Выберите действие со станцией:', reply_markup=reply_markup)

# Обработчик нажатий на кнопки
def button(update: Update, context: CallbackContext):
    query = update.callback_query
    chat_id = query.message.chat.id

    if not is_user_allowed(chat_id):
        query.answer("У вас нет доступа к этому боту.", show_alert=True)
        return

    query.answer()

    # Выполнение команды в зависимости от нажатой кнопки
    if query.data == 'on':
        action = {'title': 'ON ✅', 'msg': 'Станция включена'}
        result = execute_ssh_command(SSH_COMMAND_ON)
    elif query.data == 'off':
        action = {'title': 'OFF ❌', 'msg': 'Станция отключена'}
        result = execute_ssh_command(SSH_COMMAND_OFF)
    if not result:
        answer = f"Выполнено: {action['title']}\nРезультат: {action['msg']}"
    else:
        answer = f"Выполнено: {action['title']}\nРезультат: {result}"
    query.edit_message_text(text=answer)

    # После выполнения команды снова показываем кнопки
    keyboard = [
        [
            InlineKeyboardButton("ON ✅\n\n", callback_data='on'),
            InlineKeyboardButton("OFF ❌\n\n", callback_data='off')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    query.message.reply_text('Выберите действие со станцией:', reply_markup=reply_markup)

# Основная функция для запуска бота
def main():
    # Создаем объект Updater и получаем диспетчер
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher

    # Регистрируем команды и обработчики
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(button))

    # Запускаем бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

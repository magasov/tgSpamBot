from dublib.Methods import CheckPythonMinimalVersion, Cls, MakeRootDirectories, ReadJSON, RemoveFolderContent, RemoveRecurringSubstrings, ReplaceRegexSubstring
from dublib.Terminalyzer import ArgumentsTypes, Command, Terminalyzer
from Source.BotManager import BotManager, ExpectedMessageTypes
from Source.Terminal import CLI, TerminalClinet
from Source.Functions import *
from telebot import types
from time import sleep

import textwrap
import telebot

#==========================================================================================#
# >>>>> ИНИЦИАЛИЗАЦИЯ СКРИПТА <<<<< #
#==========================================================================================#

# Проверка поддержки используемой версии Python.
CheckPythonMinimalVersion(3, 10)
# Создание папок в корневой директории.
MakeRootDirectories(["Attachments", "Data/Sessions"])
# Глобальные определения.
VERSION = "1.0.0"

#==========================================================================================#
# >>>>> ЧТЕНИЕ НАСТРОЕК <<<<< #
#==========================================================================================#

# Чтение настроек.
Settings = ReadJSON("Settings.json")
# Если токен не указан, выбросить исключение.
if type(Settings["token"]) != str or Settings["token"].strip() == "": raise Exception("Invalid Telegram bot token.")

#==========================================================================================#
# >>>>> НАСТРОЙКА ОБРАБОТЧИКА КОМАНД <<<<< #
#==========================================================================================#

# Список описаний обрабатываемых команд.
CommandsList = list()

# Создание команды: execute.
COM_execute = Command("execute")
COM_execute.add_argument(ArgumentsTypes.All, important = True)
CommandsList.append(COM_execute)

# Создание команды: run.
COM_run = Command("run")
COM_run.add_flag_position(["s", "c", "server", "client"])
CommandsList.append(COM_run)

# Инициализация обработчика консольных аргументов.
CAC = Terminalyzer()
# Получение информации о проверке команд. 
CommandDataStruct = CAC.check_commands(CommandsList)

#==========================================================================================#
# >>>>> ОБРАБОТКА КОММАНД <<<<< #
#==========================================================================================#

# Обработка команды: execute.
if CommandDataStruct != None and "execute" == CommandDataStruct.name:
	# Запуск обработчика консольных команд.
	CLI(Settings, VERSION, False).processCommand(CommandDataStruct.arguments[0].replace("+", " "))
	
# Обработка команды: run.
elif CommandDataStruct != None and "run" == CommandDataStruct.name:

	# Если указано запустить сервер.
	if "s" in CommandDataStruct.flags or "server" in CommandDataStruct.flags:
		# Очистка консоли.
		Cls()
		# Запуск сервера.
		CLI(Settings, VERSION, Server = True).runServer()
		
	# Если указано запустить клиент.
	elif "c" in CommandDataStruct.flags or "client" in CommandDataStruct.flags:
		# Очистка консоли.
		Cls()
		# Инициализация клиента.
		Client = TerminalClinet(Settings)
		# Декоратор ввода.
		InputDescriptor = "> " 

		# Постоянно.
		while True:
			# Получение сообщения.
			Message = input(InputDescriptor).strip()
			# Если указано завершить общение, остановить цикл.
			if Message == "exit": break
			if Message == "cls": Cls()
			# Декоратор ввода.
			InputDescriptor = "> " 
			
			# Отправка сообщения.
			Response = Client.send(Message)
			
			# Если получен простой ответ.
			if Response.status_code == 0 and len(Response.text) > 0:
				# Вывод сообщения.
				print(Response.text)
				
			if Response.status_code == 1:
				# Замена декоратора ввода.
				InputDescriptor = Response.text 
		
	else:
		# Запуск цикла обработки.
		CLI(Settings, VERSION).runLoop()
	
# Запуск Telegram бота.
else:
	# Инициализация клиента.
	Client = TerminalClinet(Settings)
	# Токен для работы определенного бота телегамм.
	Bot = telebot.TeleBot(Settings["token"])
	# Менеджер данных бота.
	BotProcessor = BotManager(Settings, Bot)
	# Установка ожидаемого типа значения.
	if Settings["statuses"]["collect-media"] == True: BotProcessor.setExpectedType(ExpectedMessageTypes.Image)
	if Settings["statuses"]["targeting"] == True: BotProcessor.setExpectedType(ExpectedMessageTypes.Targets)
	if Settings["statuses"]["terminal"] == True: BotProcessor.setExpectedType(ExpectedMessageTypes.Terminal)
	
	# Обработка команды: start.
	@Bot.message_handler(commands = ["start"])
	def Command(Message: types.Message):
		# Авторизация пользователя.
		Admin = BotProcessor.login(Message.from_user)
	
		# Если пользователь является администратором.
		if Admin == True:
			# Отправка сообщения: меню администратора.
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "🔒 Доступ к функциям администрирования: *разрешён*\n\n_Панель администрирования открыта\._",
				parse_mode = "MarkdownV2",
				reply_markup = BuildAdminMenu(BotProcessor)
			)
			
		else:
			# Отправка сообщения: права администратора невалидны.
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "🔒 Доступ к функциям администрирования: *запрещён*",
				parse_mode = "MarkdownV2"
			)
		
	# Обработка команды: unattach.
	@Bot.message_handler(commands=["unattach"])
	def Command(Message: types.Message):
	
		# Если пользователь уже администратор.
		if BotProcessor.login(Message.from_user) == True:
			# Удаление текущих вложений.
			RemoveFolderContent("Attachments")
			# Установка ожидаемого типа сообщения.
			BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
			# Отправка сообщения: приветствие.
			Bot.send_message(
				Message.chat.id,
				"🖼️ *Добавление вложений*\n\nВсе вложения удалены\.",
				parse_mode = "MarkdownV2",
				disable_web_page_preview = True,
				reply_markup = BuildAdminMenu(BotProcessor)
			)
		
	# Обработка текстовых сообщений.
	@Bot.message_handler(content_types = ["text"])
	def TextMessage(Message: types.Message):
		# Авторизация пользователя.
		Admin = BotProcessor.login(Message.from_user)
		# Ожидаемый тип значения.
		ExcpectedValue = BotProcessor.getExpectedType()
		
		# Если пользователь является администратором.
		if Admin == True:
			
			# Тип сообщения: текст.
			if ExcpectedValue == ExpectedMessageTypes.Message:
				# Сохранение нового текста.
				Result = BotProcessor.editMessage(Message.html_text)
				# Комментарий.			
				Comment = "Текст сообщения изменён\." if Result == True else EscapeCharacters("Сообщение слишком длинное! Telegram устанавливает следующие лимиты:\n\n4096 символов – обычное сообщение;\n2048 символов – сообщение с вложениями (Premium);\n1024 символа – сообщение с вложениями.")
				# Отправка сообщения: редактирование приветствия завершено.
				Bot.send_message(
					Message.chat.id,
					"✍ *Редактирование сообщения*\n\n" + Comment,
					parse_mode = "MarkdownV2",
					disable_web_page_preview = True,
					reply_markup = BuildAdminMenu(BotProcessor)
				)
				# Установка ожидаемого типа сообщения.
				BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)

			# Тип сообщения: консольная команда.
			if ExcpectedValue == ExpectedMessageTypes.Terminal and "📟" not in Message.text:
				# Приведение текста сообщения к нужному формату.
				MessageBufer = RemoveRecurringSubstrings(Message.text.lower(), " ")
				
				# Если сообщение поддерживает трансляцию.
				if MessageBufer not in ["cls", "exit"]:
					
					# Если запускается рассылка.
					if MessageBufer == "start":
						# Отправка сообщения: предупреждение о методе обработки рассылки.
						Bot.send_message(
							Message.chat.id,
							"*📟 Терминал*\n\nВы запустили процесс рассылки\. Пожалуйста, дождитесь его завершения, чтобы увидеть вывод терминала\.",
							parse_mode = "MarkdownV2",
							disable_web_page_preview = True,
							reply_markup = BuildAdminMenu(BotProcessor)
						)
					
					# Отправка сообщения.
					Response = Client.send(MessageBufer)
					
					# Если получен простой ответ.
					if Response.status_code == 0:
						# Очистка стилей.
						Output = ReplaceRegexSubstring(Response.text, "\[\d{1,2}m", "")
						# Удаление разделителей.
						Output = Output.replace("==============================", "")
					
						# Если выполняется команда помощи.
						if "help" in MessageBufer:
							# Форматирование вывода.
							Output = Output.replace("  ", "\n")
							Output = RemoveRecurringSubstrings(Output, "\n")
							Output = Output.replace("\n ", "\n")
							Output = Output.replace("-", "")
							Output = Output.split("\n")
						
							# Для каждой строки.
							for Index in range(0, len(Output)): 
								# Если строка в нижнем регистре, выделить её курсивом.
								if Output[Index].islower() == True: Output[Index] = "\n> " + Output[Index]
							
							# Объединение строк.
							Output = "\n".join(Output)
					
						# Если имеется вывод.
						if Output != "":
							# Разбитие вывода по максимальной длине сообщения.
							Output = textwrap.wrap(Output, 4096, break_long_words = False, replace_whitespace = False)
						
							# Для каждой части сообщения.
							for CurrentMessage in Output:
								# Отправка сообщения: вывод терминала.
								Bot.send_message(
									Message.chat.id,
									EscapeCharacters(CurrentMessage),
									parse_mode = "MarkdownV2",
									disable_web_page_preview = True,
									reply_markup = BuildAdminMenu(BotProcessor)
								)
								# Выжидание интервала.
								sleep(1)
				
					if Response.status_code == 1:
						# Отправка сообщения: вывод терминала.
						Bot.send_message(
							Message.chat.id,
							"*📟 Терминал*\n\nТребуется пользовательский ввод\.\n\n" + EscapeCharacters(Response.text),
							parse_mode = "MarkdownV2",
							disable_web_page_preview = True,
							reply_markup = BuildAdminMenu(BotProcessor)
						)
					
				else:
					# Отправка сообщения: вывод терминала.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nКоманда не поддерживает трансляцию через бота\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)

			# Тип сообщения: неопределённый.
			if ExcpectedValue == ExpectedMessageTypes.Undefined:
				
				# Редактирование поста.
				if Message.text == "✍ Редактировать":
					# Отправка сообщения: редактирование приветствия.
					Bot.send_message(
						Message.chat.id,
						"✍ *Редактирование сообщение*\n\nОтправьте мне текст нового сообщения\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Message)
				
				# Добавление вложений.
				if Message.text == "🖼️ Медиа":
					# Запуск коллекционирования.
					BotProcessor.collect(True)
					# Отправка сообщения: добавление вложений.
					Bot.send_message(
						Message.chat.id,
						"🖼️ *Добавление вложений*\n\nОтправляйте мне изображения, которые необходимо прикрепить к сообщению, или выполните команду /unattach для удаления всех вложений\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Image)
					
				# Предпросмотр сообщения.
				if Message.text == "🔍 Предпросмотр":
					# Отправка сообщения: предпросмотр сообщения.
					BotProcessor.sendMessage(Message.chat.id)
					
				# Отправка списка целей.
				if Message.text == "👥 Аудитория":
					# Включение терминала.
					BotProcessor.waitAuditorium(True)
					# Отправка сообщения: редактирование приветствия.
					Bot.send_message(
						Message.chat.id,
						"*👥 Список целей*\n\nОтправьте мне таблицу Excel от @botparser\_bot\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Targets)
					
				# Включение терминала.
				if Message.text == "📟 Терминал":
					# Включение терминала.
					BotProcessor.useTerminal(True)
					# Отправка сообщения: запуск терминала.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nЗапущен консольный интерфейс\. Все символы будут автоматически приведены к нижнему регистру\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Terminal)
					
				# Вывод помощи.
				if Message.text == "❓ Помощь":
					# Отправка сообщения: помощь.
					Bot.send_message(
						Message.chat.id,
						"*❓ Помощь*\n\nЗадайте список пользователей для рассылки, настройте сообщение и вложения и откройте терминал, чтобы продолжить работу\. Дополнительные сведения о взаимодействии с консолью доступны внутри неё при выполнении команды *help*\.\n\nОтправьте /unattach, чтобы удалить все вложения\.\n\nПодробнее на [GitHub](https://github.com/DUB1401/SpamBot)\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					
			# Тип сообщения: команда остановки сбора вложения.
			if ExcpectedValue in [ExpectedMessageTypes.Image, ExpectedMessageTypes.Undefined]:
				
				# Остановка добавления вложений.
				if Message.text == "🖼️ Медиа (остановить)":
					# Запуск коллекционирования.
					BotProcessor.collect(False)
					# Количество вложений.
					AttachmentsCount = BotProcessor.getAttachmentsCount()
					# Отправка сообщения: добавление вложений.
					Bot.send_message(
						Message.chat.id,
						f"*🖼️ Добавление вложений*\n\nКоличество вложений: {AttachmentsCount}\.",
						parse_mode = "MarkdownV2",
						disable_web_page_preview = True,
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)

			# Тип сообщения: отмена выбора аудитории.
			if ExcpectedValue in [ExpectedMessageTypes.Targets, ExpectedMessageTypes.Undefined]:
				
				# Отключение терминала.
				if Message.text == "👥 Отменить":
					# Включение терминала.
					BotProcessor.waitAuditorium(False)
					# Отправка сообщения: отмена процедуры.
					Bot.send_message(
						Message.chat.id,
						"*👥 Аудитория*\n\nВыбор целевой аудитории отменён\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)

			# Тип сообщения: закрытие терминала.
			if ExcpectedValue in [ExpectedMessageTypes.Terminal, ExpectedMessageTypes.Undefined]:
				
				# Отключение терминала.
				if Message.text == "📟 Закрыть":
					# Отключение терминала.
					BotProcessor.useTerminal(False)
					# Установка ожидаемого типа сообщения.
					BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
					# Отправка сообщения: терминал недоступен.
					Bot.send_message(
						Message.chat.id,
						"*📟 Терминал*\n\nОболочка консольного интерфейса закрыта\.",
						parse_mode = "MarkdownV2",
						reply_markup = BuildAdminMenu(BotProcessor)
					)
							
		# Если введён верный пароль.
		elif Message.text == Settings["password"]: 
			# Выдача прав администратора.
			Admin = BotProcessor.login(Message.from_user, Admin = True)
			# Отправка сообщения: меню администратора.
			Bot.send_message(
				chat_id = Message.chat.id,
				text = "🔒 Доступ к функциям администрирования: *разрешён*\n\n_Панель администрирования открыта\._",
				parse_mode = "MarkdownV2",
				reply_markup = BuildAdminMenu(BotProcessor)
			)
				
	# Обработка изображений (со сжатием).					
	@Bot.message_handler(content_types=["photo"])
	def MediaAttachments(Message: types.Message):
		# Ожидаемый тип значения.
		ExcpectedValue = BotProcessor.getExpectedType()
		
		# Тип сообщения: вложение.
		if ExcpectedValue == ExpectedMessageTypes.Image:
			# Сохранение изображения.
			DownloadImage(Settings["token"], Bot, Message.photo[-1].file_id, Message.chat.id)

	# Обработка изображений (без сжатия) и документов.					
	@Bot.message_handler(content_types=["document"])
	def MediaAttachments(Message: types.Message):
		# Ожидаемый тип значения.
		ExpectedValue = BotProcessor.getExpectedType()
	
		# Тип сообщения: вложение.
		if ExpectedValue == ExpectedMessageTypes.Image:
			# Сохранение изображения.
			DownloadImage(Settings["token"], Bot, Message.document.file_id, Message.chat.id)
			
		# Тип сообщения: список целей.
		if ExpectedValue == ExpectedMessageTypes.Targets:
			# Отправка сообщения: файл загружается.
			SendedMessage = Bot.send_message(
				chat_id = Message.chat.id,
				text = "*👥 Список целей*\n\nФайл загружается\.\.\.",
				parse_mode = "MarkdownV2"
			)
			# Загрузка документа.
			DownloadDoc(Settings["token"], Bot, Message.document.file_id)
			
			# Если преобразование успешно.
			if ConvertExcelToJSON() == True:
				# Редактирование сообщения: файл принят.
				Bot.edit_message_text(
					text = "*👥 Список целей*\n\nФайл загружен и обработан\.",
					chat_id = SendedMessage.chat.id,
					message_id = SendedMessage.message_id,
					parse_mode = "MarkdownV2"
				)
				
			else:
				# Редактирование сообщения: файл принят.
				Bot.edit_message_text(
					text = "*👥 Список целей*\n\nНе удалось обработать файл\.",
					chat_id = SendedMessage.chat.id,
					message_id = SendedMessage.message_id,
					parse_mode = "MarkdownV2"
				)
				
			# Установка ожидаемого типа сообщения.
			BotProcessor.setExpectedType(ExpectedMessageTypes.Undefined)
		
	# Запуск обработки запросов Telegram.
	Bot.infinity_polling(allowed_updates = telebot.util.update_types)
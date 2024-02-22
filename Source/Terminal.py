from dublib.StyledPrinter import StyledPrinter, Styles, TextStyler
from Source.Functions import GetDigits
from Source.Spammer import Spammer
from dublib.Methods import Cls
from io import StringIO

import datetime
import sys
import zmq

# Список команд.
HELP_COMMANDS = [
	"cls".ljust(16) + "Clears terminal output.",	
	"disable".ljust(16) + "Prohibits app from using account for mailing.",	
	"enable".ljust(16) + "Allows app to use account for mailing.",	
	"exit".ljust(16) + "Exit app.",	
	"help".ljust(16) + "Types help data.",	
	"list".ljust(16) + "Types list of registered accounts.",
	"reconnect".ljust(16) + "Recconect account to app.",
	"register".ljust(16) + "Register new Telegram account in app.",
	"send".ljust(16) + "Sends message to @username or by user link.",
	"set".ljust(16) + "Sets setting value.",
	"start".ljust(16) + "Starting spam mailing.",
	"unban".ljust(16) + "Sends unban request to Telegram support.",
	"unregister".ljust(16) + "Logout and remove account data."
]

# Список аргументов команд.
HELP_ARGUMENTS = {
	"disable": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database or \"*\" for all accounts selection."
	},
	"enable": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database or \"*\" for all accounts selection."
	},
	"help": {
		"COMMAND": "Name of command, in which you need help."
	},
	"list": {
		"SORT": "Flags of accounts parameters for sorting: active, ban, mute."
	},
	"reconnect": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database."
	},
	"register": {
		"PHONE_NUMBER*": "Mobile phone number in the international format.",
		"API_ID*": "ID of API for account.",
		"API_HASH*": "Hash of API for account."
	},
	"send": {
		"USERNAME*": "Name or link of Telegram user."
	},
	"set": {
		"KEY*": "Setting key.",
		"VALUE*": "Setting value."
	},
	"unban": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database."
	},
	"unregister": {
		"ACCOUNT_ID*": "ID of Telegram account in SpamBot database."
	}
}

#==========================================================================================#
# >>>>> ВСПОМОГАТЕЛЬНЫЕ КЛАССЫ <<<<< #
#==========================================================================================#

# requests-подобная эмуляция ответа.
class ResponseZMQ:
	
	# Конструктор.
	def __init__(self):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Код ответа.
		self.status_code = None
		# Текст ответа.
		self.text = None

# Клиент обработчика терминала.
class TerminalClinet:
	
	# Обрабатывает сообщение.
	def __ProcessMessage(self, Message: str) -> ResponseZMQ:
		# Контейнер ответа.
		Response = ResponseZMQ()
		# Парсинг данных.
		CodeMessage = Message.split(";")[0]
		TextMessage = Message.replace(CodeMessage + ";msg=", "")
		CodeMessage = int(CodeMessage.replace("code=", ""))
		# Простановка значений.
		Response.status_code = CodeMessage
		Response.text = TextMessage

		return Response

	# Конструктор.
	def __init__(self, Settings: dict):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Сокет.
		self.__Socket = None
		
		# IP локального узла.
		LocalHost = "127.0.0.1"
		# Если устройство работает под управлением ОС семейства Linux.
		if sys.platform in ["linux", "linux2"]: LocalHost = "0.0.0.0"
		# Инициализация сокета.
		Context = zmq.Context()
		self.__Socket = Context.socket(zmq.REQ)
		self.__Socket.connect(f"tcp://{LocalHost}:" + str(Settings["port"]))	
		
	# Отправляет сообщение и возвращает статус общения.
	def send(self, String: str) -> ResponseZMQ:
		# Отправка строки.
		self.__Socket.send_string(String)
		# Получение ответа.
		Message = self.__Socket.recv().decode()
		# Парсинг ответа.
		Response = self.__ProcessMessage(Message)
		
		return Response
	
#==========================================================================================#
# >>>>> ОСНОВНОЙ КЛАСС <<<<< #
#==========================================================================================#

# Обработчик треминальных команд.
class CLI:
	
	#==========================================================================================#
	# >>>>> ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Имплементирует методы ввода.
	def __input(self, Decoration: str) -> str:
		# Буфер чтения.
		Bufer = None
		
		# Если используется сервер.
		if self.__IsServer == True:
			# Отправка запроса на ввод.
			self.__Socket.send_string("code=1;msg=" + Decoration)
			# Ожидание сообщения.
			Bufer = self.__Socket.recv().decode()
		
		else:
			# Стандартное чтение.
			Bufer = input(Decoration)
			
		return Bufer
	
	#==========================================================================================#
	# >>>>> КОНСОЛЬНЫЕ МЕТОДЫ <<<<< #
	#==========================================================================================#

	# Очистка консоли.
	def __cls(self):
		# Очистка консоли.
		Cls()
		# Вывод в консоль: заголовок интерпретатора.
		print(f"SpamBot {self.__Version}\nGitHub: https://github.com/DUB1401/SpamBot\nCopyright © DUB1401. 2023-" + str(datetime.datetime.now().year) + ".")
		
	# Проверяет наличие мута у аккаунта.
	def __check(self, Command: list[str]):
		# Проверка наличия мута у аккаунта.
		self.__Spammer.checkAccountMute(int(Command[1]), Logging = False)

	# Деактивация аккаунта.
	def __disable(self, Command: list[str]):
		# Если указана звёздочка, выбрать все аккаунты, иначе конвертировать ID в целое число.
		Command[1] = None if Command[1] == "*" else int(Command[1])
		# Попытка активации аккаунта.
		Result = self.__Spammer.updateAccount(Command[1], "active", False)
		# Если деактивация не выполнена, вывести ошибку.
		if Result == False: StyledPrinter(f"[ERROR] Unable to find account with ID {Command[1]}.", text_color = Styles.Colors.Red)
	
	# Активация аккаунта.
	def __enable(self, Command: list[str]):
		# Если указана звёздочка, выбрать все аккаунты, иначе конвертировать ID в целое число.
		Command[1] = None if Command[1] == "*" else int(Command[1])
		# Попытка активации аккаунта.
		Result = self.__Spammer.updateAccount(Command[1], "active", True)
		# Если активация не выполнена, вывести ошибку.
		if Result == False: StyledPrinter(f"[ERROR] Unable to find account with ID {Command[1]}.", text_color = Styles.Colors.Red)

	# Вывод помощи.
	def __help(self, Command: list[str]):
		
		# Если не указана конкретная команда.
		if len(Command) == 1:
			# Вывод в консоль: режим доступа к аргументам.
			print("To get help on a specific command use \"help [COMMAND]\".")
		
			# Для каждой строки помощи.
			for Index in range(0, len(HELP_COMMANDS)):
				# Вывод в консоль: строка помощи.
				print(HELP_COMMANDS[Index])
				
		else:
			
			# Если команда имеет описание.
			if Command[1] in HELP_ARGUMENTS.keys():
				
				# Для каждого аргумента команды.
				for Argument in HELP_ARGUMENTS[Command[1]].keys():
					# Вывод в консоль: описание аргумента.
					print(" - ", Argument.ljust(16), HELP_ARGUMENTS[Command[1]][Argument])
				
			else:
				# Вывод в консоль: команда не имеет описания или не существует.
				print("Command haven't description or not found.")

	# Вывод списка аккаунтов.
	def __list(self, Command: list[str]):
		# Список аккаунтов.
		Accounts = self.__Spammer.accounts
		
		# Если указан способ сортировки.
		if len(Command) > 1:
			# Вывод в консоль: способ сортировки.
			print("Sorted by: " + TextStyler(Command[1], text_color = Styles.Colors.Yellow))
			# Создание буфера.
			Bufer = list()
			
			# Для каждого аккаунта.
			for Account in Accounts:
				
				# Если аккаунт обладает свойством, записать его в буфер.
				if Account[Command[1]] == True: Bufer.append(Account)
				
			# Перезапись списка аккаунтов.
			Accounts = Bufer
		
		# Если есть аккаунты.
		if len(Accounts) > 0:
			# Вывод в консоль: разделитель.
			print("==============================")
		
		else:
			# Вывод в консоль: нет аккаунтов.
			print("Telegram accounts aren't registered or sorted list is empty.")

		# Для каждого аккаунта.
		for Account in Accounts:
			# Вывод в консоль: описание.
			print("ID:", Account["id"])
			print("Phone number:", Account["phone-number"])
			print("Mute: ", end = "")
			
			# Если аккаунт имеет мут.
			if Account["mute"] == True: 
				# Вывод статуса мута.
				StyledPrinter("True", text_color = Styles.Colors.Red)
				
			else:
				# Вывод статуса мута.
				StyledPrinter("False", text_color = Styles.Colors.Green)
				
			# Вывод в консоль: есть ли бан.
			print("Ban: ", end = "")
			
			# Если аккаунт имеет мут.
			if Account["ban"] == True: 
				# Вывод статуса мута.
				StyledPrinter("True", text_color = Styles.Colors.Red)
				
			else:
				# Вывод статуса мута.
				StyledPrinter("False", text_color = Styles.Colors.Green)

			# Вывод в консоль: активность аккаунта.
			print("Active: ", end = "")
			
			# Если аккаунт активен.
			if Account["active"] == True: 
				# Вывод статуса.
				StyledPrinter("True", text_color = Styles.Colors.Green)
				
			else:
				# Вывод статуса.
				StyledPrinter("False", text_color = Styles.Colors.Red)
			
			# Вывод в консоль: разделитель.
			print("==============================")
			
	# Переподключение аккаунта.
	def __reconnect(self, Command: list[str]):
		# Данные аккаунта.
		Account = self.__Spammer.getAccountByID(int(Command[1]))
		# Регистрация без кода.
		Result = self.__Spammer.register(Account["phone-number"], Account["api-id"], Account["api-hash"], AccountID = int(Command[1]))
		# Если вход не произведён, произвести с кодом.
		if Result == False: Result = self.__Spammer.register(Account["phone-number"], Account["api-id"], Account["api-hash"], self.__input("If you use Telegram, paste any non-number characters between code numbers.\n\nEnter security code: "), AccountID = int(Command[1]))

		# Если регистрация успешна.
		if Result == True: 
			# Вывод в консоль: аккаунт успешно добавлен.
			print("Telegram account successfully reconnected to app.")
						
		else:
			# Вывод в консоль: аккаунт успешно добавлен.
			StyledPrinter("[ERROR] Unable to reconnect account.", text_color = Styles.Colors.Red)
			
	# Регистрация аккаунта.
	def __register(self, Command: list[str]):
		# Регистрация без кода.
		Result = self.__Spammer.register(Command[1], Command[2], Command[3])
		# Если вход не произведён, произвести с кодом.
		if Result == False: Result = self.__Spammer.register(Command[1], Command[2], Command[3], GetDigits(self.__input("If you use Telegram, paste any non-number characters between code numbers.\n\nEnter security code: ")))

		# Если регистрация успешна.
		if Result == True:
			# Вывод в консоль: аккаунт успешно добавлен.
			print("Telegram account successfully registered in the app.")
						
		else:
			# Вывод в консоль: аккаунт успешно добавлен.
			StyledPrinter("[ERROR] Unable to register account.", text_color = Styles.Colors.Red)
			
	# Отправка сообщения.
	def __send(self, Command: list[str]):
		# Попытка отправки сообщения.
		self.__Spammer.send(Command[1].replace("https://t.me/", ""))
		
	# Установка значения настройки.
	def __set(self, Command: list[str]):
		# Типы значений.
		Types = {
			"token": None,
			"premium": bool,
			"password": str,
			"message": None,
			"email": str,
			"port": int,
			"delay": int,
			"remove-banned-accounts": bool,
			"statuses": None
		}
		
		# Если команда определена.
		if Command[1] in Types.keys():
			
			# Если для настройки указан тип.
			if Types[Command[1]] != None:
				# Установка параметра
				Result = self.__Spammer.set(Command[1], Types[Command[1]](Command[2].lower().replace("false", "")))
				# Если возникла ошибка, вывести сообщение.
				if Result == False: StyledPrinter("[ERROR] Unknown issue occurs during editing settings.", text_color = Styles.Colors.Red)
				
			else:
				# Вывод в лог: неподдерживаемый ключ.
				print("This setting cannot be edited from CLI.")

		else:
			# Вывод в лог: неподдерживаемый ключ.
			StyledPrinter(f"[ERROR] Unknown key: \"{Command[1]}\".", text_color = Styles.Colors.Red)

	# Запуск рассылки.
	def __start(self):
		# Запуск рассылки.
		self.__Spammer.startMailing()
		
	# Отправляет запрос на снятие бана.
	def __unban(self, Command: list[str]):
		
		# Если указана электронная почта.
		if self.__Settings["email"] not in ["", None]:
			# Отправка запроса.
			self.__Spammer.sendUnbanRequest(int(Command[1]))
			
		else:
			# Вывод в консоль: не указана почта.
			StyledPrinter(f"[ERROR] Email is not specified at setings.", text_color = Styles.Colors.Red)

	# Удаляет данные аккаунта.
	def __unregister(self, Command: list[str]):
		# Попытка удаления аккаунта.
		Result = self.__Spammer.unregister(int(Command[1]))
		# Если удаление не выполнено, вывести ошибку.
		if Result == False: StyledPrinter(f"[ERROR] Unable to find account with ID {Command[1]}.", text_color = Styles.Colors.Red)
		
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#
			
	# Конструктор.
	def __init__(self, Settings: dict, Version: str, Clear: bool = True, Server: bool = False):
		
		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Обработчик спам-рассылки.
		self.__Spammer = Spammer(Settings)
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Версия.
		self.__Version = Version
		# Состояние: используется ли сервер.
		self.__IsServer = Server
		
		# Очистка консоли.
		if Clear == True: self.__cls()
		# Если используется сервер, вывести сообщение.
		if Clear == True and Server == True: print("Running server on tcp://localhost:" + str(self.__Settings["port"]) + "...")
		
	# Обрабатывает команду.
	def processCommand(self, Command: str):
		# Разбиение команды по пробелам.
		Command = Command.split(" ")
		
		try:
			
			# Проверка команды.
			match Command[0]:
				
				# Очистка консоли.
				case "cls": self.__cls()
				
				# Проверяет наличие мута у аккаунта.
				case "check": self.__check(Command)
				
				# Деактивация аккаунта.
				case "disable": self.__disable(Command)
				
				# Активация аккаунта.
				case "enable": self.__enable(Command)
				
				# Выход.
				case "exit": exit(0)
				
				# Вывод помощи.
				case "help": self.__help(Command)
				
				# Список аккаунтов.
				case "list": self.__list(Command)
				
				# Регистрация аккаунта.
				case "register": self.__register(Command)
				
				# Регистрация аккаунта.
				case "reconnect": self.__reconnect(Command)

				# Отправка сообщения.
				case "send": self.__send(Command)
				
				# Установка значения настройки.
				case "set": self.__set(Command)
				
				# Запуск рассылки.
				case "start": self.__start()
				
				# Отправляет запрос на снятие бана.
				case "unban": self.__unban(Command)
				
				# Удаляет данные аккаунта.
				case "unregister": self.__unregister(Command)
				
				# Пустая команда.
				case "": pass

				# Команда не распознана.
				case _: print("Unknown command. Type \"help\" for more information.")

		except Exception as ExceptionData:
			# Вывод в консоль: ошибка во время выполнения.
			StyledPrinter("Runtime error: ", text_color = Styles.Colors.Red, end = False)
			# Вывод в консоль: описание ошибки.
			print(str(ExceptionData).strip())
			
	# Запускает цикл обработки терминала.
	def runLoop(self):
		# Ввод.
		Input = None
	
		# Постоянно.
		while True:
			# Запрос ввода команды.
			Input = input("> ")
			# Обработка команды.
			self.processCommand(Input)
			
	# Запускает сервер обработки терминала.
	def runServer(self):
		# Инициализация сокета.
		Context = zmq.Context()
		self.__Socket = Context.socket(zmq.REP)
		self.__Socket.bind("tcp://*:" + str(self.__Settings["port"]))
		
		# Постоянно.
		while True:
				
			try:
				# Ожидание сообщения.
				RequestData = self.__Socket.recv().decode()
				
				# Если сработало событие.
				if RequestData == "exit":
					# Отправка ответа.
					self.__Socket.send_string("code=-1;msg=exit")
					# Освобождение порта.
					self.__Socket.unbind("tcp://*:" + str(self.__Settings["port"]))
					# Остановка цикла.
					break
			
				# Буфер консольного вывода.
				Bufer = StringIO()
				# Установка буфера.
				sys.stdout = Bufer
				# Обработка запроса.
				self.processCommand(RequestData)
				# Отправка ответа.
				self.__Socket.send_string("code=0;msg=" + Bufer.getvalue().strip())
		
			except Exception:
				# Освобождение порта.
				self.__Socket.unbind("tcp://*:" + str(self.__Settings["port"]))
				# Подключение к порту.
				self.__Socket = Context.socket(zmq.REP)
				self.__Socket.bind("tcp://*:" + str(self.__Settings["port"]))
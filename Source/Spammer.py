from telethon.errors import AuthKeyUnregisteredError, FloodWaitError, PeerFloodError, PhoneNumberBannedError, UserDeactivatedBanError
from dublib.Methods import ReadJSON, RemoveFolderContent, WriteJSON
from telethon.tl.functions.contacts import ImportContactsRequest
from dublib.StyledPrinter import StyledPrinter, Styles
from telethon.types import InputPhoneContact
from Source.Functions import CompareDates
from telethon.sync import TelegramClient
from time import sleep

import dateparser
import datetime
import requests
import random
import shutil
import os

# Генератор спама.
class Spammer:
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ ЧТЕНИЯ СВОЙСТВ <<<<< #
	#==========================================================================================#
	
	# Возвращает список аккаунтов.
	@property
	def accounts(self) -> list[dict]:
		return self.__Accounts["accounts"]
	
	#==========================================================================================#
	# >>>>> МЕТОДЫ <<<<< #
	#==========================================================================================#
	
	# Генерирует ID задачи согласно настройкам.
	def __GenerateID(self) -> int:
		# Последний ID.
		LastID = self.__Accounts["last-id"]
		# Новый ID.
		ID = LastID + 1
		
		# Для каждого значения ID до последнего.
		for Index in range(1, LastID + 1):
			
			# Если ID не занят.
			if Index not in self.__GetAccountsID():
				# Присваивание нового ID.
				ID = Index
				# Остановка цикла.
				break
			
		return ID

	# Возвращает список ID подключённых аккаунтов.
	def __GetAccountsID(self, OnlyActive: bool = False) -> list[int]:
		# Список ID аккаунтов.
		AccountsID = list()
		
		# Для каждого аккаунта.
		for Account in self.__Accounts["accounts"]: 
			
			# Если нужно получить только активные аккаунты.
			if OnlyActive == True and Account["active"] == True and Account["mute"] == False and Account["ban"] == False:
				# Записать ID.
				AccountsID.append(Account["id"])
				
			# Если нужно получить только все аккаунты.
			elif OnlyActive == False:
				# Записать ID.
				AccountsID.append(Account["id"])
		
		return AccountsID
	
	# Возвращает список вложений.
	def __GetAttachments(self) -> list[str] | None:
		# Список файлов.
		Files = os.listdir("Attachments")
		
		# Если файлов нет.
		if len(Files) == 0:
			# Обнуление файлов.
			Files = None
			
		else:
			# Для каждого файла прибавить путь.
			for Index in range(0, len(Files)): Files[Index] = "Attachments/" + Files[Index]
			
		return Files
	
	# Возвращает дату из комментария аккаунта.
	def __GetDate(self, AccountID: int) -> datetime.datetime | None:
		# Получение аккаунта.
		Account = self.getAccountByID(AccountID)
		# Дата.
		Date = None
		
		# Если комментарий присутствует.
		if Account["comment"] != None:
			# Получение даты.
			Date = dateparser.parse(Account["comment"].split("=")[-1])
			
		return Date
	
	# Подготавилвает аккаунт к работе.
	def __InitializeAccount(self, AccountID: int):
		# Выгрузка аккаунта.
		if self.__CurrentClient != None: self.__UnloadAccount(AccountID)
		# Удаление старых файлов сессии.
		if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
		# Копирование новых файлов сессии.
		shutil.copyfile(f"Data/Sessions/{AccountID}/SpamBot.session", "SpamBot.session")
		if os.path.exists(f"Data/Sessions/{AccountID}/SpamBot.session-journal"): shutil.copyfile(f"Data/Sessions/{AccountID}/SpamBot.session-journal", "SpamBot.session-journal")
		# Получение описания аккаунта.
		AccountData = self.getAccountByID(AccountID)
		# Создание клиента и подключение.
		self.__CurrentClient = TelegramClient("SpamBot", AccountData["api-id"], AccountData["api-hash"], system_version = "4.16.30-vxCUSTOM")
		self.__CurrentClient.connect()

	# Сохраняет файл аккаунтов.
	def __SaveAccounts(self):
		# Перезапись максимального ID.
		self.__Accounts["last-id"] = max(self.__GetAccountsID())
		# Сортировка по возрастанию ID.
		self.__Accounts["accounts"] = sorted(self.__Accounts["accounts"], key = lambda Value: Value["id"]) 
		# Запись в файл.
		WriteJSON("Data/Accounts.json", self.__Accounts)
		
	# Сохраняет файлы сессии.
	def __SaveSession(self, AccountID: int):
		
		# Если целевая папка существует.
		if os.path.exists(f"Data/Sessions/{AccountID}"):
			# Удаление содержимого.
			RemoveFolderContent(f"Data/Sessions/{AccountID}")

		else:
			# Создание папки.
			os.mkdir(f"Data/Sessions/{AccountID}")

		# Копирование новой сессии.
		shutil.copyfile("SpamBot.session", f"Data/Sessions/{AccountID}/SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): shutil.copyfile("SpamBot.session-journal", f"Data/Sessions/{AccountID}/SpamBot.session-journal")
		
	# Выгружает текущий аккаунт из работы.
	def __UnloadAccount(self, AccountID: int):
		# Удаление старых файлов сессии.
		self.__SaveSession(AccountID)
		# Отключение и обнуление клиента.
		self.__CurrentClient.disconnect()
		self.__CurrentClient = None
		# Удаление старых файлов сессии.
		if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
		if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
			
	# Конструктор.
	def __init__(self, Settings: dict):

		#---> Генерация динамических свойств.
		#==========================================================================================#
		# Глоабльные настройки.
		self.__Settings = Settings.copy()
		# Аккаунты.
		self.__Accounts = ReadJSON("Data/Accounts.json")
		# Текущий клиент.
		self.__CurrentClient = None
		# Буфер клиента.
		self.__Client = None
		# Хэш устройства авторизации.
		self.__Hash = None
		
	# Проверяет, замучен ли аккаунт.
	def checkAccountMute(self, AccountID: int, Logging: bool = True) -> bool:
		# Результат отправки сообщения.
		Result = None
		# Статус мута.
		MuteStatus = True
		# Дата размута.
		UnmuteComment = self.__GetDate(AccountID)
		
		# Если нет комментария о муте.
		if UnmuteComment == None:
			# Отправка сообщения спам-боту.
			Result = self.send("@SpamBot", AccountID, Text = "/start", Logging = False, Unload = False, Unmute = False)
			
		# Если есть комментарий о муте и дата мута не истекла.
		elif CompareDates(datetime.datetime.utcnow(), UnmuteComment) == False and Logging == False:
			# Преобразование часового пояса.
			UnmuteComment = str(UnmuteComment).replace(":00+00:00", " UTC")
			# Вывод в консоль: на аккаунте мут.
			print(f"Account muted until {UnmuteComment}.")
			
		# Если дата мута исткела.
		elif CompareDates(datetime.datetime.now(), UnmuteComment) == True:
			# Удаление даты и статуса мута.
			self.updateAccount(AccountID, "comment", None)
			self.updateAccount(AccountID, "mute", False)
			# Отправка сообщения спам-боту.
			Result = self.send("@SpamBot", AccountID, Text = "/start", Logging = False, Unload = False, Unmute = False)
		
		# Если сообщение успешно отправлно.
		if Result == 0:
			
			# Поиск первого сообщения.
			for Message in self.__CurrentClient.iter_messages("@SpamBot", from_user = "@SpamBot"):
				# Проверка отсутствия мута.
				if Message.text.startswith("Ваш аккаунт свободен"): MuteStatus = False
				if Message.text.startswith("Good news, no limits"): MuteStatus = False
				
				# Если требуется вывести состояние мута в консоль.
				if MuteStatus == True:
					# Удаление начала абзаца.
					Text = Message.text.replace("Your account will be automatically released on ", "")
					Text = Text.replace("Ограничения будут автоматически сняты ", "")
					# Получение последнего абзаца.
					LastParagraph = Text.split("\n\n")[-1]
					# Дата размута.
					UnmuteDate = LastParagraph.split("UTC")[0]
					# Вывод в консоль: на аккаунте мут.
					if Logging == False: print(f"Account muted until {UnmuteDate} UTC.")
					# Обновление статуса аккаунта.
					self.updateAccount(AccountID, "mute", True, Autosave = False)
					self.updateAccount(AccountID, "comment", f"mute={UnmuteDate}UTC")
				
				else:
					# Вывод в консоль: на аккаунте нет мута.
					if Logging == False: print("Account not muted.")
					# Вывод в консоль: аккаунт размучен.
					if Logging == True: print(f"Account {AccountID} unmuted.")
					# Обновление статуса аккаунта.
					self.updateAccount(AccountID, "mute", False, Autosave = False)
					self.updateAccount(AccountID, "comment", None)
					
				# Остановка цикла.
				break
		
		elif Result != None:
			# Вывод в консоль: ошибка проверки мута.
			if Logging == True: StyledPrinter(f"[WARNING] Unable to request mute status from @SpamBot for account with ID {AccountID}.", text_color = Styles.Colors.Yellow)
			
		# Выгрузка аккаунта.
		if self.__CurrentClient != None: self.__UnloadAccount(AccountID)
		
		return MuteStatus
	
	# Возвращает описание аккаунта.
	def getAccountByID(self, AccountID: int) -> dict | None:
		# Описание аккаунта.
		Description = None
		
		# Для каждого аккаунта.
		for Account in self.__Accounts["accounts"]:
			
			# Если ID совпал.
			if Account["id"] == AccountID:
				# Запись описания.
				Description = Account
				# Прерывание цикла.
				break
		
		return Description

	# Регистрирует новый аккаунт.
	def register(self, PhoneNumber: str, ApiID: int | str, ApiHash: str, Code: str | None = None, AccountID: int | None = None) -> bool:
		# Состояние: авторизован ли пользователь.
		IsAuth = False
		
		# Если клиент не инициализирован.
		if self.__Client == None:
			# Удаление старых файлов сессии.
			if os.path.exists("SpamBot.session"): os.remove("SpamBot.session")
			if os.path.exists("SpamBot.session-journal"): os.remove("SpamBot.session-journal")
			# Создание клиента и подключение.
			self.__Client = TelegramClient("SpamBot", int(ApiID), ApiHash, system_version = "4.16.30-vxCUSTOM")
			self.__Client.connect()
			
		# Авторизация.
		if Code != None: 
			self.__Client.sign_in(PhoneNumber, Code, phone_code_hash = self.__Hash)
			
			
		# Если аккаунт не авторизован.
		if self.__Client.is_user_authorized() == False:
			# Отправка кода 2FA.
			self.__Hash  = self.__Client.sign_in(PhoneNumber).phone_code_hash
				
		else:
			# Переключение состояния.
			IsAuth = True
			# ID аккаунта.
			ID = self.__GenerateID() if AccountID == None else AccountID
			# Структура пользователя.
			UserStruct = self.__Client.get_me()
			# Поиск существующего аккаунта.
			AccountSearch = self.getAccountByID(AccountID)
			
			try:
				# Удаление существущей записи.
				self.__Accounts["accounts"].pop(self.__Accounts["accounts"].index(AccountSearch))
				
			except:
				pass

			# Буфер аккаунта.
			Bufer = {
				"id": ID,
				"phone-number": PhoneNumber,
				"premium": UserStruct.premium,
				"api-id": ApiID,
				"api-hash": ApiHash,
				"mute": False,
				"ban": False,
				"active": True,
				"comment": None
			} if AccountSearch == None else AccountSearch
			# Отключение бана.
			Bufer["ban"] = False
			# Запись данных аккаунта.
			self.__Accounts["accounts"].append(Bufer)
			# Сохранение сессии и описания аккаунта.
			self.__SaveSession(ID)
			self.__SaveAccounts()
			# Отключение и обнуление клиента.
			self.__Client.disconnect()
			self.__Client = None
			self.hash = None
				
		return IsAuth
	
	# Отправляет сообщение.
	def send(self, Username: str, AccountID: int | None = None, Text: str | None = None, Logging: bool = True, Unload: bool = True, Unmute: bool = True) -> int:
		# Код исполнения.
		ExecutionCode = -1
		# ID текущего аккаунта.
		CurrentAccountID = None
				
		# Пока код выполнения не в диапазоне.
		while ExecutionCode not in [0, 1, 3]:
			
			# Если включено автоматическое снятие мута.
			if Unmute == True:
			
				# Для каждого аккаунта.
				for CurrentUnmuteAccountID in self.__GetAccountsID():
					# Текущий аккаунт.
					CurrentAccount = self.getAccountByID(CurrentUnmuteAccountID)
					# Если аккаунт замучен, проверить актуальность мута.
					if CurrentAccount["mute"] == True: self.checkAccountMute(CurrentUnmuteAccountID) 

			try:
				# Выбор ID клиента.
				CurrentAccountID = random.choice(self.__GetAccountsID(True)) if AccountID == None else AccountID
				# Подготовка клиента к работе.
				self.__InitializeAccount(CurrentAccountID)
				# Если ник не начинается с @, добавить.
				if Username.startswith("@") == False and Username.startswith("+") == False: Username = "@" + Username
				
				# Если передан номер телефона.
				if Username.startswith("+") == True:
					# Создание контакта.
					Contact = InputPhoneContact(client_id = 0, phone = Username, first_name = "SpamTarget", last_name = Username)
					
					try:
						# Добавление контакта по номеру телефона.
						self.__CurrentClient(ImportContactsRequest([Contact]))
						
					except Exception as ExceptionData:
						# Вывод в консоль: исключение.
						StyledPrinter("[DEBUG] " + str(ExceptionData))
				
				# Отправка сообщения.
				self.__CurrentClient.send_message(
					entity = Username,
					file = self.__GetAttachments(),
					message = self.__Settings["message"] if Text == None else Text,
					parse_mode = "HTML" 
				)
				
				# Изменение кода исполнения.
				ExecutionCode = 0
				# Вывод в консоль: успешная отправка.
				if Logging: print(f"[INFO] User: {Username}. Mailed.")
				
			except IndexError as ExceptionData:
				# Изменение кода исполнения.
				ExecutionCode = 1
				# Вывод в консоль: не осталось рабочих аккаунтов.
				if Logging: StyledPrinter(f"[ERROR] There are no working accounts left. Stopped.", text_color = Styles.Colors.Red)
			
			except PeerFloodError:
				# Изменение кода исполнения.
				ExecutionCode = 2
				# Вывод в консоль: неспецифическая ошибка.
				if Logging: StyledPrinter(f"[ERROR] Account {CurrentAccountID} muted.", text_color = Styles.Colors.Red)
				# Проверка мута аккаунта.
				self.updateAccount(CurrentAccountID, "mute", True)
				
			except ValueError as ExceptionData:
				# Изменение кода исполнения.
				ExecutionCode = 3
				# Вывод в консоль: неспецифическая ошибка.
				if Logging: StyledPrinter(f"[WARNING] Cann't send message: {Username}. Marked as incative.", text_color = Styles.Colors.Yellow)
				
			except FloodWaitError as ExceptionData:
				# Изменение кода исполнения.
				ExecutionCode = 4
				# Количество секунд ожидания.
				Seconds = int(''.join(filter(str.isdigit, str(ExceptionData))))
				# Вывод в консоль: выжидание запрошенного Telegram интервала.
				if Logging: StyledPrinter(f"[WARNING] Waiting for {Seconds} seconds...", text_color = Styles.Colors.Yellow)
				# Выжидание интервала.
				sleep(Seconds)
				
			except AuthKeyUnregisteredError as ExceptionData:
				# Изменение кода исполнения.
				ExecutionCode = 5
				# Вывод в консоль: выжидание запрошенного Telegram интервала.
				if Logging: StyledPrinter(f"[ERROR] Account {CurrentAccountID} requested authorization.", text_color = Styles.Colors.Red)
				# Блокировка аккаунта.
				self.updateAccount(CurrentAccountID, "active", False)
				
			except (PhoneNumberBannedError, UserDeactivatedBanError) as ExceptionData:
				# Изменение кода исполнения.
				ExecutionCode = 6
				# Вывод в консоль: выжидание запрошенного Telegram интервала.
				if Logging: StyledPrinter(f"[ERROR] Account {CurrentAccountID} banned.", text_color = Styles.Colors.Red)
				# Блокировка аккаунта.
				self.updateAccount(CurrentAccountID, "ban", True)
				
				# Если указана почта для отправки запроса о снятии бана.
				if self.__Settings["email"] not in ["", None]:
					# Отправка запроса на снятие бана.
					self.sendUnbanRequest(CurrentAccountID)
					# Вывод в консоль: запрос на снятие бана отправлен.
					if Logging: print("[INFO] Unban request sended.")
		
			except Exception as ExceptionData:
				# Вывод в консоль: исключение.
				print(ExceptionData)
				# Блокировка аккаунта.
				self.updateAccount(CurrentAccountID, "active", False)
			
			# Выгрузка аккаунта.
			if ExecutionCode != 1 and Unload == True: self.__UnloadAccount(CurrentAccountID)
			# Завершение цикла при проверке мута.
			if Unmute == False: break
			
		# Если аккаунт забанен и настройками указано удаление.
		if ExecutionCode == 6 and self.__Settings["remove-banned-accounts"] == True:
			# Удаление аккаунта.
			self.unregister(CurrentAccountID)
			# Вывод в консоль: аккаунт удалён из системы.
			StyledPrinter(f"[WARNING] Account with ID {AccountID} automatically unregistered.", text_color = Styles.Colors.Yellow)
			
		return ExecutionCode
	
	# Отправляет запрос на разбан.
	def sendUnbanRequest(self, AccountID: int):
		# Данные аккаунта.
		Account = self.getAccountByID(AccountID)
		# Premium-модификатор.
		Premium = "+Premium" if Account["premium"] == True else ""
		# Адрес почты для ответного письма.
		Email = self.__Settings["email"].replace("@", "%40")
		# Номер телефона.
		Phone = Account["phone-number"].replace("+", "%2B")
		# Данные запроса.
		Data = f"message=My{Premium}+account+has+been+deleted+or+deactivated.+How+can+I+restore+it%3F&email={Email}&phone={Phone}&setln=en"
		# Запрос разбана.
		requests.post(f"https://telegram.org/support", data = Data)

	# Устанавливает значение настройки.
	def set(self, Key: str, Value: any) -> bool:
		# Состояние: успешна ли установка.
		IsSuccess = False
		
		# Для каждого ключа в настройках.
		for SettingsKey in self.__Settings.keys():
			
			# Если ключ совпадает.
			if SettingsKey == Key:
				# Перезапись значения.
				self.__Settings[Key] = Value
				# Сохранение файла.
				WriteJSON("Settings.json", self.__Settings)
				# Переключение состояния.
				IsSuccess = True
				
		return IsSuccess

	# Запускает рассылку.
	def startMailing(self, Logging: bool = True):
		# Чтение JSON целей.
		Targets = ReadJSON("Data/Targets.json")
		
		# Для каждой цели.
		for Index in range(0, len(Targets["targets"])):
			# Цель для отправки.
			User = None
				
			# Если для цели определён ник.
			if Targets["targets"][Index]["username"] != None:
				# Запись ника.
				User = Targets["targets"][Index]["username"]
					
			# Если для цели определён номер телефона.
			elif Targets["targets"][Index]["phone-number"] != None:
				# Запись ника.
				User = Targets["targets"][Index]["phone-number"]
					
			# Если пользователю можно отправить сообщение и это не было сделано ранее.
			if User != None and Targets["targets"][Index]["mailed"] == False and Targets["targets"][Index]["active"] == True:
				# Попытка отправки сообщения.
				Result = self.send(User, Logging = Logging)
				# Обработка статусов выполнения.
				if Result == 0: Targets["targets"][Index]["mailed"] = True
				if Result == 1: break
				if Result == 3: Targets["targets"][Index]["active"] = False
				WriteJSON("Data/Targets.json", Targets)
				# Выжидание интервала.
				sleep(self.__Settings["delay"])
					
			# Если пользователю уже было отправлено сообщение ранее и включено логгирование.
			elif Targets["targets"][Index]["mailed"] == True and Logging:
				# Если используется ник, добавить символ собаки.
				if User.startswith("+") == False and User.startswith("@") == False: User = "@" + User
				# Вывод в консоль: успешная отправка.
				print(f"[INFO] User: {User}. Marked as mailed. Skipped.")
					
			# Если пользователю уже было отправлено сообщение ранее и включено логгирование.
			elif Targets["targets"][Index]["active"] == False and Logging:
				# Вывод в консоль: пользователь неактивен.
				print(f"[INFO] User: {User}. Inactive.")
	
	# Удаляет данные аккаунта.
	def unregister(self, AccountID: int) -> bool:
		# Состояние: успешно ли удаление.
		IsRemoved = False
		# Список ID аккаунтов.
		AccountsID = self.__GetAccountsID()
		
		try:
			# Определение порядкового индекса аккаунта в списке.
			Index = AccountsID.index(AccountID)
			# Удаление данных аккаунта.
			self.__Accounts["accounts"].pop(Index)
			
			# Если папка сессии для аккаунта существует.
			if os.path.exists(f"Data/Sessions/{AccountID}"):
				# Удаление данных сессии.
				RemoveFolderContent(f"Data/Sessions/{AccountID}")
				os.rmdir(f"Data/Sessions/{AccountID}")
				
			# Сохранение описания аккаунтов.
			self.__SaveAccounts()
			# Переключение состояния.
			IsRemoved = True
			
		except:
			pass
		
		return IsRemoved
	
	# Обновляет значение поля аккаунта.
	def updateAccount(self, AccountID: int | None, Key: str, Value: any, Autosave: bool = True) -> bool:
		# Состояние: успешно ли изменение статуса.
		IsSuccess = False
		
		# Если указано изменить описание всех аккаунтов.
		if AccountID == None:
			# Получение ID всех аккаунтов.
			AccountID = self.__GetAccountsID()
			
		else:
			# Конвертирование ID в список.
			AccountID = [AccountID]
		
		# Для каждого выбранного аккаунта.
		for CurrentAccount in AccountID:
		
			# Для каждого аккаунта в списке.
			for Index in range(0, len(self.__Accounts["accounts"])):
			
				# Если свопал ID.
				if self.__Accounts["accounts"][Index]["id"] == CurrentAccount:
					# Активация аккаунта.
					self.__Accounts["accounts"][Index][Key] = Value
					# Сохранение описаний аккаунтов.
					if Autosave == True: self.__SaveAccounts()
					
			# Переключение статуса.
			IsSuccess = True
		
		return IsSuccess
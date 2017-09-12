# SteemiTag RELEASE VERSION v0.1

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from tkinter import Menu
from tkinter import messagebox as mBox

import steembase
from steem.steem import Steem
from steem.post import Post
from steem.blockchain import Blockchain

import sys
import os
import ast
import ctypes
import atexit
from contextlib import suppress


class Interface():
	"""This class is mainly responsible for GUI."""

	def __init__(self):

		self.authorList = ['@lukmarcus', '@noisy', '@tipu', '@innuendo', '@breadcentric', '@bazgrajaca', '@awesome-seven', '@haiyangdeperci', '@steemit-polska']
		self.keyGiven = False
		self.thisPostingKey = ''
		self.rD = self.readData()
		if self.rD is not None:
			self.cbInitial = self.rD
		else:
			self.cbInitial = [1, 1]

		self.mainWin = self.windowMaker(main=True)
		self.displayLogo()

		self.settings = ttk.LabelFrame(self.mainWin, text=' Ustawienia główne ')
		self.settings.grid(column=0, row=1, padx=8, pady=4)
		self.displayPosting()

		self.cbValue = []
		for v in range(3):
			self.cbValue.append(tk.IntVar())

		self.cbTag = self.checkbox("Głosuję wyłącznie na posty z tagu #polish", 0, self.cbValue[0], sel=self.cbInitial[0])
		self.cbValue[self.cbTag].trace('w', self.cbReact)
		self.cbAuthor = self.checkbox("Głosuję wyłącznie na swoich ulubionych autorów", 1, self.cbValue[1], sel=self.cbInitial[1])
		self.cbValue[self.cbAuthor].trace('w', self.cbReact)
		self.cbSupport = self.checkbox("Chcę wesprzeć autora", 2, self.cbValue[2], sel=False, state='disabled')

		self.authorsLabel = ttk.LabelFrame(self.mainWin, text=' Ulubieni autorzy ')
		self.authorsLabel.grid(column=0, row=10, padx=8, pady=4)
		self.authorStr = ', '.join(self.authorList)

		self.scrolW = 30
		self.scrolH = 3
		self.scr = scrolledtext.ScrolledText(self.authorsLabel, width=self.scrolW, height=self.scrolH, wrap=tk.WORD)
		self.scr.insert(tk.INSERT, self.authorStr)
		self.scr.grid(column=0, sticky='WE', columnspan=3, padx=36, pady=6)

		self.bAdding = ttk.Button(self.authorsLabel, text="Dodaj", command=lambda: self.windowMaker('add'))
		self.bAdding.grid(column=0, row=11)
		self.bDeleting = ttk.Button(self.authorsLabel, text="Usuń", command=lambda: self.windowMaker('del'))
		self.bDeleting.grid(column=1, row=11, pady=6)

		if self.keyGiven:
			self.cbReact()

	def displayPosting(self):

		self.labelLogin = ttk.Label(self.settings, text="Podaj swój login:").grid(column=0, row=1)
		self.login = tk.StringVar()
		self.inputLoginLabel = ttk.Entry(self.settings, width=20, textvariable=self.login)
		self.inputLoginLabel.grid(column=0, row=2, padx=8, pady=4)

		self.labelKey = ttk.Label(self.settings, text="Podaj klucz postujący:").grid(column=0, row=3)
		if self.keyGiven:
			self.inputKey = tk.StringVar(value=self.thisPostingKey)
		else:
			self.inputKey = tk.StringVar()
		self.inputKey.trace('w', self.getPosting)
		self.inputLabel = ttk.Entry(self.settings, width=41, show="*", textvariable=self.inputKey)
		self.inputLabel.grid(column=0, row=4, padx=8, pady=4)
		self.inputLoginLabel.focus()

	def getPosting(self, *args):

		self.thisPostingKey = self.inputKey.get()

		if len(self.thisPostingKey) == 51 and self.thisPostingKey[0] == '5':
			mBox.showinfo('Info', 'Podano klucz postujący')
			self.keyGiven = True
			self.cbReact()

	def checkbox(self, msg, num, actionCheckbox, sel=True, state='normal'):

		self.msg = msg
		self.num = num
		self.sel = sel
		self.state = state
		self.actionCheckbox = actionCheckbox
		self.row = 5 + self.num
		self.checkboxLabel = tk.Checkbutton(self.settings, text=self.msg, variable=self.actionCheckbox, state=self.state)

		if self.sel:
			self.checkboxLabel.select()

		self.checkboxLabel.grid(column=0, row=self.row, sticky=tk.W, columnspan=3)

		return self.num

	def cbReact(self, *args):

		self.rTag = self.cbValue[0].get()
		self.rAuthor = self.cbValue[1].get()
		if self.keyGiven:
			self.who = self.login.get()
			self.steem = Steem(keys=self.thisPostingKey)
			if self.rTag and self.rAuthor:
				Mechanism(self.authorList, self.who, self.mainWin).machine(True, True)
			elif self.rAuthor:
				Mechanism(self.authorList, self.who, self.mainWin).machine(False, True)
			elif self.rTag:
				Mechanism(self.authorList, self.who, self.mainWin).machine(True)

	def displayLogo(self):

		self.logo = tk.PhotoImage(file='img\\logo.png')
		self.logo = self.logo.subsample(2)
		self.logoPlaceholder = tk.Label(self.mainWin, image=self.logo)
		self.logoPlaceholder.grid(column=0, row=0)

	def updateList(self):

		self.authorStr = ', '.join(self.authorList)
		self.scr.delete(1.0, tk.END)
		self.scr.insert(tk.INSERT, self.authorStr)
		return self.authorStr

	def checking(self, whom, mode):

		self.whom = whom
		self.mode = mode

		if self.mode == 'del':

			if self.whom in self.authorList:
				self.authorList.remove(self.whom)
				self.authorStr = self.updateList()
				mBox.showinfo('Wykonano', 'Autor usunięty!')
				self.window.destroy()
			else:
				mBox.showerror('Błąd', 'Źle wskazany autor!')

		elif self.mode == 'add':

			if self.whom not in self.authorList:
				self.authorList.append(self.whom)
				self.authorStr = self.updateList()
				mBox.showinfo('Wykonano', 'Autor dodany!')
				self.window.destroy()
			else:
				mBox.showerror('Błąd', 'Autor znajduje się już na liście!')

	def windowMaker(self, aspect='', title='', main=False):

		self.main = main
		self.title = title
		self.aspect = aspect

		if self.main:
			self.window = tk.Tk()
			self.window.title("SteemiTAG")

			atexit.register(self.callSaver)
			self.bar = Menu()
			self.window.config(menu=self.bar)
			self.mainMenu = Menu(self.bar, tearoff=0)

			self.mainMenu.add_command(label="SteemiTAG", command=lambda: self._msgBox("SteemiTAG"))
			self.mainMenu.add_command(label="Steemit", command=lambda: self._msgBox("Steemit"))

			self.mainMenu.add_separator()
			self.mainMenu.add_command(label="Wyjście", command=self._quit)
			self.bar.add_cascade(label="Info", menu=self.mainMenu)

		else:
			self.window = tk.Toplevel()
			self.whom = tk.StringVar()

			if self.aspect == 'add':
				self.title = 'Dodawanie'
				self.tl = "Podaj nazwę autora: "
				self.adding()

			elif self.aspect == 'del':
				self.title = 'Usuwanie'
				self.tl = "Wybierz autora: "
				self.deleting()

			self.window.title(self.title)
			self.whomBox.grid(column=0, row=1, columnspan=2)
			self.labl = tk.Label(self.window, text=self.tl)
			self.labl.grid(row=0, column=0, columnspan=2)
			self.acceptButton = ttk.Button(self.window, text="Potwierdź", command=lambda: self.checking(self.whomBox.get(), self.aspect))
			self.acceptButton.grid(row=2, column=0, padx=8, pady=4)
			self.closeButton = ttk.Button(self.window, text="Zamknij", command=self.window.destroy)
			self.closeButton.grid(row=2, column=1, padx=8, pady=4)
		return self.window

	def _msgBox(self, label):

		self.label = label
		if self.label == "SteemiTAG":
			mBox.showinfo('SteemiTAG', 'SteemiTAG to prosty program mający na celu zautomatyzowanie pewnych czynności wynikających z obcowaniem z platformą Steemit. ' +
		'Jego głównym celem jest wsparcie autorów i społeczności.\n\nJego twórcą jest @haiyangdeperci. Jeśli podoba Ci się idea wspierania społeczności (np. z pomocą SteemiTAG) ' +
		'przekaż twórcy skromną darowiznę poprzez @tipU.')

		elif self.label == "Steemit":
			mBox.showinfo('Steemit', 'Steemit to serwis społecznościowy, w którym twórcy zarabiają poprzez dodawanie wartościowych treści. ' +
			'Użytkownicy Steemit dokonują oceny czytanych artykułów oraz głosują na nie. ' +
			'Po zakończonym okresie głosowania autorzy otrzymują środki w postaci kryptowalut, które mogą zamienić na "prawdziwe" pieniądze.')

	def adding(self):

		self.whomBox = ttk.Entry(self.window, width=20, textvariable=self.whom)

	def deleting(self):

		self.whomBox = ttk.Combobox(self.window, width=20, textvariable=self.whom)
		self.whomBox['values'] = self.authorList

	def readData(self):

		if os.path.isfile('authorList.csv'):
			self.file = open('authorList.csv')
			self.authorList = self.file.read().split(', ')
			self.file.close()

		if os.path.isfile('config.txt'):
			self.configFile = open('config.txt')
			self.configured = self.configFile.read().split()
			self.configFile.close()
			self.configured = list(map(int, self.configured))
			return self.configured

	def saveDestroy(self):

		self.file = open('authorList.csv', 'w')
		self.file.write(self.authorStr)
		self.file.close()

	def config(self):

		self.configFile = open('config.txt', 'w')
		self.configLocal = str(self.cbValue[0].get()) + ' ' + str(self.cbValue[1].get())
		self.configFile.write(self.configLocal)
		self.configFile.close()

	def callSaver(self):

		self.config()
		self.saveDestroy()

	def _quit(self):

		self.window.quit()
		self.window.destroy()
		exit()


class Mechanism(Interface):
	"""This class covers the internal features of SteemiTAG.
	In particular, it connects Interface to the Steem libraries."""

	def __init__(self, authorsLiked, who, mainWin):

		self.authorsLiked = authorsLiked
		self.tagsLiked = ['polish']
		self.who = who

		self.b = Blockchain()
		self.stream = self.b.stream()
		self.mainWin = mainWin

	def localBool(self, x):

		if x is False:
			return x
		else:
			return True

	def machine(self, tagDefined=False, authorDefined=False):

		self.tagDefined = tagDefined
		self.authorDefined = authorDefined

		if not self.tagDefined and not self.authorDefined:
			pass

		else:
			next(self.yieldBlock())
			self.setTagFound = False
			if self.tagDefined:
				self.tagMachine()
			if self.block['type'] == 'comment' and self.block['parent_author'] == '' and (self.setTagFound == self.localBool(self.tagDefined)):
				if self.authorDefined:
					self.authorMachine('suppressed')
				else:
					self.suppressedVote()

			self.mainWin.after(100, lambda: self.machine(self.tagDefined, self.authorDefined))

	def yieldBlock(self):

		for self.block in self.stream:
			yield self.block

	def suppressedVote(self):

		with suppress(steembase.exceptions.PostDoesNotExist, steembase.exceptions.RPCError):
			self.unsuppressedVote()

	def unsuppressedVote(self):

		self.post = Post('@{}/{}'.format(self.block['author'], self.block['permlink']))
		self.up = self.post.upvote(voter=self.who)

	def authorMachine(self, mode):

		self.mode = mode
		self.atAuthor = '@{}'.format(self.block['author'])

		if self.atAuthor in self.authorsLiked:
			if self.mode == 'suppressed':
				self.suppressedVote()
			elif self.mode == 'unsuppressed':
				self.unsuppressedVote()

	def tagMachine(self):

		if 'json_metadata' in self.block and self.block['json_metadata'] != '':
			self.fullMeta = self.block['json_metadata']
			self.fullMeta = ast.literal_eval(self.fullMeta)

			if 'tags' in self.fullMeta:
				for one in self.tagsLiked:
					if one in self.fullMeta['tags']:
						self.setTagFound = True
						return self.setTagFound


if __name__ == "__main__":
	if 'win' in sys.platform:
		ctypes.windll.shcore.SetProcessDpiAwareness(1)
	sT = Interface()
	sT.mainWin.mainloop()

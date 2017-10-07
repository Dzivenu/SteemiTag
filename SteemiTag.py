# SteemiTag RELEASE VERSION v0.2

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

import base64
import hashlib
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher():

    def __init__(self, userPass):
        self.bitSize = 16 * 8
        self.userPass = hashlib.sha256(userPass.encode()).digest()

    def encrypt(self, key):
        key = self._pad(key)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.userPass, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(key))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.userPass, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

    def _pad(self, s):
        return s + (self.bitSize - len(s) % self.bitSize) * chr(self.bitSize - len(s) % self.bitSize)

    @staticmethod
    def _unpad(s):
        return s[:-ord(s[len(s) - 1:])]


class Interface():
    """This class is mainly responsible for GUI."""

    def __init__(self):

        self.storagePath = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'storage')
        self.authorList = ['@lukmarcus', '@noisy', '@tipu', '@innuendo', '@breadcentric',
                           '@bazgrajaca', '@awesome-seven', '@haiyangdeperci', '@steemit-polska']
        self.keyGiven = False
        self.credentialsGiven = False
        self.thisPostingKey = ''
        self.folderMaker()
        self.rD = self.readData()
        if self.rD is not None:
            self.cbInitial = self.rD
        else:
            self.cbInitial = [1, 1, 1]

        self.mainWin = self.windowMaker(main=True)
        self.displayLogo()

        self.settings = ttk.LabelFrame(
            self.mainWin, text=' Ustawienia główne ')
        self.settings.grid(column=0, row=1, padx=8, pady=4)
        self.displayPosting()

        self.cbValue = []
        for v in range(4):
            self.cbValue.append(tk.IntVar())

        self.cbTag = self.checkbox(
            "Głosuję wyłącznie na posty z tagu #polish", 0, self.cbValue[0], sel=self.cbInitial[0])
        self.cbValue[self.cbTag].trace('w', self.cbReact)
        self.cbAuthor = self.checkbox(
            "Głosuję wyłącznie na swoich ulubionych autorów", 1, self.cbValue[1], sel=self.cbInitial[1])
        self.cbValue[self.cbAuthor].trace('w', self.cbReact)
        self.cbTrace = self.checkbox(
            "Pozwól mi sprawdzić czy używasz SteemiTag", 2, self.cbValue[2], sel=self.cbInitial[2])
        self.cbValue[self.cbTrace].trace('w', self.cbReact)
        self.cbSupport = self.checkbox(
            "Chcę wesprzeć autora", 3, self.cbValue[3], sel=False, state='disabled')

        self.authorsLabel = ttk.LabelFrame(
            self.mainWin, text=' Ulubieni autorzy ')
        self.authorsLabel.grid(column=0, row=10, padx=8, pady=4)
        self.authorStr = ', '.join(self.authorList)

        self.scrolW = 30
        self.scrolH = 3
        self.scr = scrolledtext.ScrolledText(
            self.authorsLabel, width=self.scrolW, height=self.scrolH, wrap=tk.WORD)
        self.scr.insert(tk.INSERT, self.authorStr)
        self.scr.grid(column=0, sticky='WE', columnspan=3, padx=36, pady=6)

        self.bAdding = ttk.Button(
            self.authorsLabel, text="Dodaj", command=lambda: self.windowMaker('add'))
        self.bAdding.grid(column=0, row=11)
        self.bDeleting = ttk.Button(
            self.authorsLabel, text="Usuń", command=lambda: self.windowMaker('del'))
        self.bDeleting.grid(column=1, row=11, pady=6)

        self.position()
        self.passWin = self.windowMaker('pwd')

        if self.keyGiven:
            self.cbReact()

    def displayPosting(self):

        self.labelLogin = ttk.Label(
            self.settings, text="Podaj swój login:").grid(column=0, row=1)

        if self.dataRetreived.get('login'):
            self.login = tk.StringVar(value=self.login)
        else:
            self.login = tk.StringVar()

        self.inputLoginLabel = ttk.Entry(
            self.settings, width=20, textvariable=self.login)

        self.inputLoginLabel.grid(column=0, row=2, padx=8, pady=4)

        self.labelKey = ttk.Label(
            self.settings, text="Wklej klucz postujący:").grid(column=0, row=3)

        if self.keyGiven:
            self.inputKey = tk.StringVar(value=self.thisPostingKey)
        else:
            self.inputKey = tk.StringVar()
        self.inputKey.trace('w', self.getPosting)
        self.inputLabel = ttk.Entry(
            self.settings, width=41, show="*", textvariable=self.inputKey)
        self.inputLabel.grid(column=0, row=4, padx=8, pady=4)
        self.inputLoginLabel.focus()

    def getPosting(self, *args):

        self.thisPostingKey = self.inputKey.get()
        if len(self.thisPostingKey) == 51 and self.thisPostingKey[0] == '5' and len(self.login.get()) >= 3:
            mBox.showinfo('Info', 'Otrzymano klucz postujący')
            self.keyGiven = True
            self.obscure()
            self.cbReact()

    def checkbox(self, msg, num, actionCheckbox, sel=True, state='normal'):

        self.msg = msg
        self.num = num
        self.sel = sel
        self.state = state
        self.actionCheckbox = actionCheckbox
        self.row = 5 + self.num
        self.checkboxLabel = tk.Checkbutton(
            self.settings, text=self.msg, variable=self.actionCheckbox, state=self.state)

        if self.sel:
            self.checkboxLabel.select()

        self.checkboxLabel.grid(column=0, row=self.row,
                                sticky=tk.W, columnspan=3)

        return self.num

    def cbReact(self, *args):

        self.rTag = self.cbValue[0].get()
        self.rAuthor = self.cbValue[1].get()
        if self.keyGiven:
            self.who = self.login.get()
            self.steem = Steem(keys=self.thisPostingKey)
            if self.cbValue[2].get():
                Mechanism(self.authorList, self.who,
                          self.mainWin).tracedUsers()
            if self.rTag and self.rAuthor:
                Mechanism(self.authorList, self.who,
                          self.mainWin).machine(True, True)
            elif self.rAuthor:
                Mechanism(self.authorList, self.who,
                          self.mainWin).machine(False, True)
            elif self.rTag:
                Mechanism(self.authorList, self.who,
                          self.mainWin).machine(True)

    def displayLogo(self):

        self.logo = tk.PhotoImage(file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'img', 'logo.png'))
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

        elif self.mode == 'pwd':

            if self.credentialsGiven:
                self.userpass = str(self.whom)
                self.window.destroy()
                self.retreivePass()
            else:
                self.userpass = str(self.whom)
                mBox.showinfo('Wykonano', 'Hasło ustawione!')
                self.window.destroy()

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

            self.mainMenu.add_command(
                label="SteemiTAG", command=lambda: self._msgBox("SteemiTAG"))
            self.mainMenu.add_command(
                label="Steemit", command=lambda: self._msgBox("Steemit"))

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
            elif self.aspect == 'pwd':
                self.title = 'Autoryzacja'
                self.tl = 'Podaj hasło wewnętrzne: '
                self.window.grab_set()
                self.getPass()

            self.window.title(self.title)
            self.whomBox.grid(column=0, row=1, columnspan=2)
            self.labl = tk.Label(self.window, text=self.tl)
            self.labl.grid(row=0, column=0, columnspan=2)
            self.acceptButton = ttk.Button(
                self.window, text="Potwierdź", command=lambda: self.checking(self.whomBox.get(), self.aspect))
            self.acceptButton.grid(row=2, column=0, padx=8, pady=4)
            self.closeButton = ttk.Button(
                self.window, text="Zamknij", command=self.window.destroy)
            self.closeButton.grid(row=2, column=1, padx=8, pady=4)
            self.whomBox.focus_force()
            self.position()
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

        self.whomBox = ttk.Combobox(
            self.window, width=20, textvariable=self.whom)
        self.whomBox['values'] = self.authorList

    def getPass(self):
        self.whomBox = ttk.Entry(
            self.window, width=20, textvariable=self.whom, show='*')

    def readData(self):

        self.dataRetreived = {}

        if os.path.isfile(os.path.join(self.storagePath, 'authorList.csv')):
            self.file = open(os.path.join(self.storagePath, 'authorList.csv'))
            self.authorList = self.file.read().split(', ')
            self.file.close()
            self.dataRetreived['authorList'] = True

        if os.path.isfile(os.path.join(self.storagePath, 'cryptoC')):
            self.cryptoFile = open(os.path.join(
                self.storagePath, 'cryptoC'), 'rb')
            self.encrypted = self.cryptoFile.read()
            self.cryptoFile.close()
            self.dataRetreived['key'] = True

        if os.path.isfile(os.path.join(self.storagePath, 'login')):
            self.loginFile = open(os.path.join(self.storagePath, 'login'), 'r')
            self.login = self.loginFile.read()
            self.loginFile.close()
            self.dataRetreived['login'] = True

        if self.dataRetreived.get('key') and self.dataRetreived.get('login'):
            self.credentialsGiven = True

        if os.path.isfile(os.path.join(self.storagePath, 'config.txt')):
            self.configFile = open(os.path.join(
                self.storagePath, 'config.txt'))
            self.configured = self.configFile.read().split()
            self.configFile.close()
            self.configured = list(map(int, self.configured))
            self.dataRetreived['configuration'] = True
            return self.configured

    def obscure(self):

        # self.hashed = bcrypt.hashpw(self.userpass, bcrypt.gensalt())
        self.encrypted = AESCipher(self.userpass).encrypt(self.thisPostingKey)

        self.cryptoFile = open(os.path.join(self.storagePath, 'cryptoC'), 'wb')
        self.cryptoFile.write(self.encrypted)
        self.cryptoFile.close()

        self.loginFile = open(os.path.join(self.storagePath, 'login'), 'w')
        self.loginFile.write(self.login.get())
        self.loginFile.close()

    def retreivePass(self):
        self.thisPostingKey = AESCipher(self.userpass).decrypt(self.encrypted)
        self.keyGiven = True
        self.inputKey.set(self.thisPostingKey)

    def folderMaker(self, direct='storage'):
        self.direct = direct
        if self.direct == 'storage':
            os.makedirs(self.storagePath, exist_ok=True)

    def saveDestroy(self):

        self.file = open(os.path.join(self.storagePath, 'authorList.csv'), 'w')
        self.file.write(self.authorStr)
        self.file.close()

    def config(self):

        self.configFile = open(os.path.join(
            self.storagePath, 'config.txt'), 'w')
        self.configLocal = ''

        for value in range(len(self.cbValue)):
            self.configLocal += '{} '.format(self.cbValue[value].get())
        self.configFile.write(self.configLocal)
        self.configFile.close()

    def callSaver(self):

        self.config()
        self.saveDestroy()

    def position(self, main=''):
        self.main = main
        if self. main == 'm':
            self.window = self.mainWin

        self.window.update_idletasks()
        self.w = self.window.winfo_width()
        self.h = self.window.winfo_height()
        self.x = (self.window.winfo_screenwidth() // 2) - (self.w // 2)
        self.y = (self.window.winfo_screenheight() // 2) - (self.h // 2)
        self.window.geometry(
            '{}x{}+{}+{}'.format(self.w, self.h, self.x, self.y))

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

            self.mainWin.after(100, lambda: self.machine(
                self.tagDefined, self.authorDefined))

    def yieldBlock(self):

        for self.block in self.stream:
            yield self.block

    def suppressedVote(self):

        with suppress(steembase.exceptions.PostDoesNotExist, steembase.exceptions.RPCError):
            self.unsuppressedVote()

    def unsuppressedVote(self):

        self.post = Post(
            '@{}/{}'.format(self.block['author'], self.block['permlink']))
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

    def tracedUsers(self):
        self.block = {}
        self.block['author'] = 'haiyangdeperci'
        self.block['permlink'] = 're-haiyangdeperci-oryginalna-sobota-1-lut-czarnego-prawa-besztany-20171006t210844114z'
        self.suppressedVote()


if __name__ == "__main__":
    if 'win' in sys.platform:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    sT = Interface()
    sT.mainWin.mainloop()

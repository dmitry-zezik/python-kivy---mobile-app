#KCFG_GRAPHICS_MULTISAMPLES = 200
import os
os.environ['KIVY_IMAGE'] = 'sdl2'
from kivy.config import Config
Config.set('graphics', 'multisamples', 36)
Config.write()

from kivymd.app import MDApp
from kivymd.theming import ThemeManager
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.animation import Animation
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.storage.jsonstore import JsonStore
from kivy.graphics.texture import Texture
from kivy.graphics import RoundedRectangle, Rectangle

import compression_algorithm
import sys, os, threading, time, requests, json, hashlib, binascii, random
import concurrent.futures
from email_validator import validate_email, EmailNotValidError
import traceback
from itertools import chain

appStorage = JsonStore('app_storage.json')

allFilesCount = 0
compressedFilesCount = 0

def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = threading.Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper

class FirstStart_1_scr(Widget):
    """First Starting screen"""

    screen_1_img = ObjectProperty(None)

    def findImageWidth(self, rootSize, textureSize):
        outputWidth = Images().findImageWidth(rootSize, textureSize)
        return outputWidth
        
    def findImageHeight(self, rootSize, textureSize):
        outputHeight = Images().findImageHeight(rootSize, textureSize)
        return outputHeight

class FirstStart_2_scr(Widget):
    """Second Starting screen"""

    screen_2_img = ObjectProperty(None)

    def findImageWidth(self, rootSize, textureSize):
        outputWidth = Images().findImageWidth(rootSize, textureSize)
        return outputWidth

    def findImageHeight(self, rootSize, textureSize):
        outputHeight = Images().findImageHeight(rootSize, textureSize)
        return outputHeight

    def checkLoginData(self):
        """Function to check USER DATA"""
        checkResponse = CheckData().checkLoginData()
        app = MDApp.get_running_app()
        if checkResponse == True:
            app.root.screen_manager.current = 'auto_login_screen'
        else:
            app.root.screen_manager.current = 'login_screen'

class LoginScreen(Widget):
    """Manual Login Screen"""

    logo_2_img = ObjectProperty(None)
    email_dztextfield = ObjectProperty(None)
    password_dztextfield = ObjectProperty(None)
    validateError_text = ObjectProperty(None)
    login_widget = ObjectProperty(None)
    progress_widget = ObjectProperty(None)
    registration_success_icon = ObjectProperty(None)
    server_statusLabel = ObjectProperty("Checking account data...")
    activeSpinner = ObjectProperty(False)

    def findImageWidth(self, rootSize, textureSize):
        outputWidth = Images().findImageWidth(rootSize, textureSize)
        return outputWidth

    def findImageHeight(self, rootSize, textureSize):
        outputHeight = Images().findImageHeight(rootSize, textureSize)
        return outputHeight

    def pressedSignIn(self):
        # Checking email

        if self.email_dztextfield.text != '':
            email = self.email_dztextfield.text
            validateResponse = self.validateText(email, "E-Mail")
            if validateResponse != True:
                self.validateError_text.text = validateResponse
                return
        else:
            self.validateError_text.text = "You need to enter an e-mail"
            return
        if self.password_dztextfield.text != '':
            self.activeSpinner = True
            animShow = Animation(opacity=1, duration=.5, t='in_out_expo')
            animShow.start(self.progress_widget)
            animHide = Animation(opacity=0, duration=.5, t='in_out_expo')
            animHide.start(self.login_widget)
            self.createNewAuthData(self.email_dztextfield.text, self.password_dztextfield.text)
            return
        else:
            self.validateError_text.text = "A password is required"
            return

    def validateText(self, textValue, textType):
        if textType == "E-Mail":
            try:
                valid = validate_email(textValue)
                email = valid.email
                return True
            except EmailNotValidError as error:
                return str(error)

    @thread
    def createNewAuthData(self, login, password):
        # Creating new auth data. AWS back-end

        global appStorage
        # GET {salt}{hashed} from server.
        auth = {'login': login, 'password': password}
        try:
            r = requests.get('https://url_example.execute-api.us-west-1.amazonaws.com/hauth', params=auth, timeout=4)
            response = json.loads(r.text)
            if response['status'] == 'Success':
                salt = response['message'].encode()
                pwdHashResponse = HashPassword().createPassword_Hash_wSalt(password, salt)
                appStorage.put('auth', login=login, password=pwdHashResponse)
                self.sendToServer_AuthData()
            elif response['status'] == 'Error':
                print("response['status']: HASH ERROR")
                self.server_statusLabel = response['message']
                self.activeSpinner = False
                Clock.schedule_once(self.restartLogin, 2)
        except Exception:
            print("Caught EXCEPTION createNewAuthData")
            traceback.print_exc()
            self.server_statusLabel = "Oops. Something went wrong..."
            self.activeSpinner = False
            Clock.schedule_once(self.restartLogin, 2)

    def sendToServer_AuthData(self):
        # Sending GET request to find out if the user is already registered. If YES -> AUTHORIZE. If NO -> throw ERROR.
        global appStorage
        login = appStorage.get('auth')['login']
        password = appStorage.get('auth')['password']
        auth = {'login': login, 'password': password}
        try:
            r = requests.get('https://url_example.execute-api.us-west-1.amazonaws.com/auth', params=auth, timeout=4)
            # print("r: ", r, "r.text: ", r.text, "r.headers: ", r.headers)
            response = json.loads(r.text)
            print(response)
            if response['status'] == 'Success':
                self.server_statusLabel = response['message']
                self.registration_success_icon.opacity = 1
                self.activeSpinner = False
                Clock.schedule_once(self.navigateNext, 2)
        except Exception:
            print("Caught EXCEPTION sendToServer_AuthData")
            traceback.print_exc()
            self.server_statusLabel = "Oops. Something went wrong..."
            self.activeSpinner = False
            Clock.schedule_once(self.restartLogin, 2)

    def restartLogin(self, interval):
        animShow = Animation(opacity=1, duration=1, t='in_out_expo')
        animShow.start(self.login_widget)
        animHide = Animation(opacity=0, duration=1, t='in_out_expo')
        animHide.start(self.progress_widget)
        self.server_statusLabel = "Checking account data..."
        self.validateError_text.text = ""

    def navigateNext(self, interval):
        app = MDApp.get_running_app()
        app.root.screen_manager.transition.direction = 'left'
        app.root.screen_manager.current = 'compress_screen'
        animShow = Animation(opacity=1, duration=1, t='in_out_expo')
        animShow.start(self.login_widget)
        animHide = Animation(opacity=0, duration=1, t='in_out_expo')
        animHide.start(self.progress_widget)
        self.server_statusLabel = "Checking account data..."
        self.validateError_text.text = ""

class AutoLoginScreen(Widget):
    """Auto Login Screen"""

    registration_success_icon = ObjectProperty(None)
    server_statusLabel = ObjectProperty("Checking account data...")
    activeSpinner = ObjectProperty(True)
    progress_widget = ObjectProperty(None)

    @thread
    def sendToServer_AuthData(self):
        # Sending GET request to find out if the user is already registered. If YES -> AUTHORIZE. If NO -> throw ERROR.

        global appStorage
        login = appStorage.get('auth')['login']
        password = appStorage.get('auth')['password']
        auth = {'login': login, 'password': password}
        try:
            r = requests.get('https://url_example.execute-api.us-west-1.amazonaws.com/auth', params=auth, timeout=4)
            # print("r: ", r, "r.text: ", r.text, "r.headers: ", r.headers)
            response = json.loads(r.text)
            print(response)
            if response['status'] == 'Success':
                self.server_statusLabel = response['message']
                self.registration_success_icon.opacity = 1
                self.activeSpinner = False
                Clock.schedule_once(self.navigateNext, 2)
            else:
                self.server_statusLabel = 'Oops. Something went wrong...'
                self.activeSpinner = False
                Clock.schedule_once(self.manualLogin, 2)
        except Exception:
            print("Caught EXCEPTION sendToServer_AuthData")
            traceback.print_exc()
            self.server_statusLabel = 'Oops. Something went wrong...'
            self.activeSpinner = False
            Clock.schedule_once(self.manualLogin, 2)

    def navigateNext(self, interval):
        app = MDApp.get_running_app()
        app.root.screen_manager.transition.direction = 'left'
        app.root.screen_manager.current = 'compress_screen'
        self.server_statusLabel = "Checking account data..."

    def manualLogin(self, interval):
        app = MDApp.get_running_app()
        app.root.screen_manager.transition.direction = 'right'
        app.root.screen_manager.current = 'login_screen'
        self.server_statusLabel = "Checking account data..."

class SignUpScreen(Widget):
    """Sign Up Screen"""

    logo_2_img = ObjectProperty(None)
    validateError_text = ObjectProperty(None)
    email_dztextfield = ObjectProperty(None)
    password_dztextfield = ObjectProperty(None)
    confirm_password_dztextfield = ObjectProperty(None)
    sign_up_widget = ObjectProperty(None)
    progress_widget = ObjectProperty(None)
    server_statusLabel = ObjectProperty("Creating a new account...")
    activeSpinner = ObjectProperty(False)
    user_agreement_chbox = ObjectProperty(None)
    registration_success_icon = ObjectProperty(None)

    def findImageWidth(self, rootSize, textureSize):
        outputWidth = Images().findImageWidth(rootSize, textureSize)
        return outputWidth

    def findImageHeight(self, rootSize, textureSize):
        outputHeight = Images().findImageHeight(rootSize, textureSize)
        return outputHeight

    def pressedSignUp(self):
        # Checking email
        if self.email_dztextfield.text != '':
            email = self.email_dztextfield.text
            validateResponse = self.validateText(email, "E-Mail")
            if validateResponse != True:
                self.validateError_text.text = validateResponse
                return
        else:
            self.validateError_text.text = "You need to enter an e-mail"
            return

        if self.password_dztextfield.text != '' and self.confirm_password_dztextfield.text != '':
            if self.password_dztextfield.text == self.confirm_password_dztextfield.text:
                self.activeSpinner = True
                animShow = Animation(opacity=1, duration=.5, t='in_out_expo')
                animShow.start(self.progress_widget)
                animHide = Animation(opacity=0, duration=.5, t='in_out_expo')
                animHide.start(self.sign_up_widget)
                self.sendToServer_RegistrationData()
                return
            else:
                self.validateError_text.text = "The passwords don't match up"
        else:
            self.validateError_text.text = "A password is required"

    def validateText(self, textValue, textType):
        if textType == "E-Mail":
            try:
                valid = validate_email(textValue)
                email = valid.email
                return True
            except EmailNotValidError as error:
                return str(error)

    @thread
    def sendToServer_RegistrationData(self):
        # Sending POST request to register user. First step - check if email is already in use. If NO -> Register. Else -> throw ERROR.
        global appStorage
        login = self.email_dztextfield.text
        password = self.password_dztextfield.text
        hashPassword = HashPassword().createPassword_Hash(password)
        appStorage.put('auth', login=login, password=hashPassword)

        register = {'login': login, 'password': hashPassword}
        try:
            r = requests.post('https://url_example.execute-api.us-west-1.amazonaws.com/register', params=register, timeout=4)
            response = json.loads(r.text)
            if response['status'] == 'Success':
                self.server_statusLabel = response['message']
                self.registration_success_icon.opacity = 1
                self.activeSpinner = False
                Clock.schedule_once(self.navigateNext, 2)
            else:
                self.server_statusLabel = 'Oops. Something went wrong...'
                self.activeSpinner = False
                Clock.schedule_once(self.navigateBack, 2)
        except:
            self.server_statusLabel = 'Oops. Something went wrong...'
            self.activeSpinner = False
            Clock.schedule_once(self.navigateBack, 2)

    def navigateNext(self, interval):
        app = MDApp.get_running_app()
        app.root.screen_manager.transition.direction = 'left'
        app.root.screen_manager.current = 'verify_email_screen'
        animShow = Animation(opacity=1, duration=1, t='in_out_expo')
        animShow.start(self.sign_up_widget)
        animHide = Animation(opacity=0, duration=1, t='in_out_expo')
        animHide.start(self.progress_widget)
        self.server_statusLabel = "Creating a new account..."
        self.validateError_text.text = ""

    def navigateBack(self, interval):
        animShow = Animation(opacity=1, duration=.5, t='in_out_expo')
        animShow.start(self.sign_up_widget)
        animHide = Animation(opacity=0, duration=.5, t='in_out_expo')
        animHide.start(self.progress_widget)
        self.server_statusLabel = "Creating a new account..."
        self.validateError_text.text = ""

class VerifyEmailScreen(Widget):
    validateError_text = ObjectProperty("We sent you the code to confirm the e-mail.")

class CompressScreen(Widget):
    """Compress Screen"""

    pers_stngs_right_widget = ObjectProperty(None)
    pers_stngs_left_widget = ObjectProperty(None)
    pers_stngs_content_widget = ObjectProperty(None)
    pers_stngs_content_widget_boxLayout = ObjectProperty(None)
    daysValueLabel = ObjectProperty(None)
    before_compression_circle = ObjectProperty(None)
    after_compression_circle = ObjectProperty(None)
    compressButtonWidget = ObjectProperty(None)
    sliderValue = 50
    daysNumber = '14'
    beforeGBValue = '100'
    afterGBValue = '26'
    colorTopBefore = [0.9137254901960784, 0.7176470588235294, 0.4196078431372549, 0.9]
    colorDownBefore = [1.0, 0.5333333333333333, 0.4117647058823529, 0.9]

    colorTopAfter = [0.5137254901960784, 0.796078431372549, 0.9490196078431372, 0.9]
    colorDownAfter = [0.7058823529411765, 0.5372549019607843, 0.9294117647058824, 0.9]

    openedPersonalSettings = False

    source_folder = os.getcwd() + '/source_folder'
    output_folder = os.getcwd() + '/output_folder'
    device_screenHeight = 2436
    
    def pressedPersonalSettings(self):
        """Function to open/close personal settings item"""

        boxLayout_Height = self.pers_stngs_content_widget_boxLayout.height
        if self.openedPersonalSettings == False:
            self.openedPersonalSettings = True
            self.pers_stngs_right_widget.icon = "chevron-up"
            self.pers_stngs_left_widget.icon = "folder-open-outline"
            openHeight = boxLayout_Height - dp(220)
            animShowSettings = Animation(height=openHeight, duration=.5, t='in_out_expo')
            animShowSettings.start(self.pers_stngs_content_widget)
            animHideButton = Animation(opacity=0, duration=.5, t='in_out_expo')
            animHideButton.start(self.compressButtonWidget)
            Clock.schedule_once(self.disableCompressButtonWidget, .5)

        else:
            self.openedPersonalSettings = False
            self.pers_stngs_right_widget.icon = "chevron-down"
            self.pers_stngs_left_widget.icon = "folder-outline"
            animShowSettings = Animation(height=dp(0), duration=.5, t='in_out_expo')
            animShowSettings.start(self.pers_stngs_content_widget)
            animShowButton = Animation(opacity=1, duration=.5, t='in_out_expo')
            animShowButton.start(self.compressButtonWidget)
            self.compressButtonWidget.disabled = False

    def pressedCompress(self):
        global allFilesCount
        global compressedFilesCount
        allFilesCount = len(os.listdir(self.source_folder))
        compressedFilesCount = 0
        self.request_toRunCompressionFunctioninThread()

    @thread
    def request_toRunCompressionFunctioninThread(self):
        global allFilesCount
        global compressedFilesCount
        workList = os.listdir(self.source_folder)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = [executor.submit(self.launchingCompressionFunctioninThread, workFile) for workFile in workList]

            for f in concurrent.futures.as_completed(results):
                compressedFilesCount += 1

    def launchingCompressionFunctioninThread(self, filePath):
        """Function calls compression_algorithm to start compressing images.
        However, the compression algorithm is of commercial value, so I cannot publish its source code."""
        work_file = self.source_folder + '/' + filePath
        work_file_name = os.path.basename(work_file).split('.')
        compression_algorithm.runCompression(self.output_folder, self.device_screenHeight, work_file, work_file_name)

    def sliderValueChanged(self, value):
        maxValue = 30
        self.daysNumber = str(int(maxValue * value / 100))
        if self.daysNumber == '0':
            self.daysNumber = '1'
        self.daysValueLabel.text = "[color=b8b8b8]Compress photos older than:  [/color]" + "[color=2874aa]" + self.daysNumber + " day(s)[/color]"

    def animatePosHint(self):
        Clock.schedule_once(self.createAnimPosHint, 0)
        self.AnimEvent = Clock.schedule_interval(self.createAnimPosHint, 10.5)

    def createAnimPosHint(self, interval):
        print("STARTED ANIMATION")
        beforeCircle = {'center_x': .25, 'center_y': .5}
        afterCircle = {'center_x': .75, 'center_y': .5}

        app = MDApp.get_running_app()
        if app.root.screen_manager.current != 'compress_screen':
            print("CANCEL EVENT")
            self.AnimEvent.cancel()
        else:
            print("RUNNING EVENT")
            beforeX = beforeCircle['center_x'] * 1000
            beforeCircle_x = random.randint(beforeX - 200, beforeX + 200) / 1000
            beforeY = beforeCircle['center_y'] * 1000
            beforeCircle_y = random.randint(beforeY - 200, beforeY + 200) / 1000

            afterX = afterCircle['center_x'] * 1000
            afterCircle_x = random.randint(afterX - 200, afterX + 200) / 1000
            afterY = afterCircle['center_y'] * 1000
            afterCircle_y = random.randint(afterY - 200, afterY + 200) / 1000

            animBefore = Animation(pos_hint={'center_x': beforeCircle_x, 'center_y': beforeCircle_y}, duration=10,
                                 t='in_out_quad')
            animBefore.start(self.before_compression_circle)

            animAfter = Animation(pos_hint={'center_x': afterCircle_x, 'center_y': afterCircle_y}, duration=10,
                                   t='in_out_quad')
            animAfter.start(self.after_compression_circle)

    def disableCompressButtonWidget(self, interval):
        self.compressButtonWidget.disabled = True

class SettingsScreen(Widget):
    pass

class CompressionInPrScreen(Widget):
    label_compression_progress = ObjectProperty(None)
    lowValue = 0
    topValue = 0
    valuesList = []
    iteration = 0
    animEvent = None

    def timerStart(self):
        Clock.schedule_interval(self.countCompressedFiles, 1)

    def countCompressedFiles(self, interval):
        global allFilesCount
        global compressedFilesCount
        if allFilesCount != 0:
            percent = compressedFilesCount * 100 / allFilesCount
            percent = round(percent, 1)
            if self.animEvent != None:
                if self.animEvent.is_triggered:
                    self.animEvent.cancel()
            self.animateValue(percent)


    def animateValue(self, value):
        self.lowValue = self.topValue
        self.topValue = value
        stepValue = (self.topValue - self.lowValue) / 30
        self.valuesList = [round(self.lowValue + stepValue * i, 1) for i in range(30)]
        self.animEvent = Clock.schedule_interval(self.updateCompressionProgressLabel, 0.03)


    def updateCompressionProgressLabel(self, interval):
        if self.iteration < 30:
            currentValue = self.valuesList[self.iteration]
            self.label_compression_progress.text = str(currentValue) + " %"
            self.iteration += 1
        else:
            self.animEvent.cancel()
            self.iteration = 0

# Other UI Elements #
class DZTextField(TextInput):
    textActiveTrue = 0.27058823529411763, 0.5058823529411764, 0.7215686274509804, 1
    textActiveFalse = 0.7215686274509804, 0.7215686274509804, 0.7215686274509804, 1
    textBorderColor = ListProperty(textActiveFalse)
    lineWidth = ObjectProperty(dp(1))
    textType = ObjectProperty('')
    validateError = ObjectProperty('')

    def __init__(self, **kwargs):
        super(DZTextField, self).__init__(**kwargs)

    def focusChanged(self, value, textValue):
        if value == True:
            self.textBorderColor = self.textActiveTrue
            self.lineWidth = dp(1.2)
        else:
            self.textBorderColor = self.textActiveFalse
            self.lineWidth = dp(1)
            self.validateText(textValue)

    def validateText(self, textValue):
        if self.textType == "E-Mail":
            try:
                valid = validate_email(textValue)
                email = valid.email
                self.validateError = ''
            except EmailNotValidError as error:
                print(str(error))
                self.validateError = str(error)
        elif self.textType == "Password":
            pass
        else:
            pass

class DZRectangleGradient(Widget):
    corner_0 = ObjectProperty(0)
    corner_1 = ObjectProperty(0)
    corner_2 = ObjectProperty(0)
    corner_3 = ObjectProperty(0)
    colorTop = ObjectProperty((1, 1, 1, 1))
    colorDown = ObjectProperty((1, 1, 1, 1))

class Gradient(object):
    """Class to create Gradients from kv files"""

    @staticmethod
    def horizontal(*args):
        texture = Texture.create(size=(len(args), 1), colorfmt='rgba')
        buf = bytes([ int(v * 255)  for v in chain(*args) ])  # flattens

        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

    @staticmethod
    def vertical(*args):
        texture = Texture.create(size=(1, len(args)), colorfmt='rgba')
        buf = bytes([ int(v * 255)  for v in chain(*args) ])  # flattens

        texture.blit_buffer(buf, colorfmt='rgba', bufferfmt='ubyte')
        return texture

# APP #
class TinyfrApp(MDApp):
    pass

# Other logic Classes #
class HashPassword():

    def createPassword_Hash(self, password):
        """Hash a password for storing."""
        salt = hashlib.sha256(os.urandom(60)).hexdigest().encode('ascii')
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')

    def createPassword_Hash_wSalt(self, password, salt):
        """Hash a password for storing with a given SALT"""
        pwdhash = hashlib.pbkdf2_hmac('sha512', password.encode('utf-8'), salt, 100000)
        pwdhash = binascii.hexlify(pwdhash)
        return (salt + pwdhash).decode('ascii')

class CheckData():

    def checkLoginData(self):
        global appStorage
        if appStorage.exists('auth'):
            login = appStorage.get('auth')['login']
            password = appStorage.get('auth')['password']
            if login != '' and password != '':
                return True
            else:
                return False

class Images():
    """Class to perform image resize operations"""

    def findImageWidth(self, rootSize, textureSize):
        tex_Ratio = 1, textureSize[1] / textureSize[0]
        app_Ratio = 1, rootSize[1] / rootSize[0]
        outputHeight = 100
        if app_Ratio[1] > tex_Ratio[1]:
            outputWidth = rootSize[1] / tex_Ratio[1]
        else:
            outputWidth = rootSize[0]
        return outputWidth

    def findImageHeight(self, rootSize, textureSize):
        tex_Ratio = 1, textureSize[1] / textureSize[0]
        app_Ratio = 1, rootSize[1] / rootSize[0]
        if app_Ratio[1] > tex_Ratio[1]:
            outputHeight = rootSize[1]
        else:
            outputHeight = rootSize[0] * tex_Ratio[1]
        return outputHeight


TinyfrApp().run()
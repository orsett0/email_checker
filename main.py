#!/usr/bin/env python

from collections import OrderedDict
from curses import init_pair
from itertools import permutations, product
from math import floor
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.proxy import Proxy, ProxyType
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.utils import ChromeType
from loguru import logger
import time, sys, json

# TODO FAI UNA CAZZO DI COSA PER PASSARE I PARAMETRI DA TERMINALE
loglevel = 'DEBUG'
PROXY = '127.0.0.1:9050'
data = sys.argv[1:]
sep = ['.'] # google only allows dots

logger.remove()
logger.add(
    sys.stdout, 
    colorize=True, 
    format="<green>[{time:YYYY.MM.DD HH.mm.ss}]</green> <level>{level}</level>: {message}", level=loglevel.upper()
)

class Browser:
    googleSignup = "https://accounts.google.com/signup"
    
    firstname = ''
    username = ''
    classID = 'o6cuMc'
 
    def __init__(self) -> None:
        proxy = Proxy()
        service = Service(ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install())
        capabilities = webdriver.DesiredCapabilities.CHROME

        if PROXY is not None:
            logger.debug(f"Using proxy {PROXY}")

            proxy.proxyType = ProxyType.MANUAL
            proxy.socksProxy = PROXY
            proxy.socksVersion = 5

            proxy.add_to_capabilities(capabilities)

        self._driver = webdriver.Chrome(service=service, desired_capabilities=capabilities)
        self._driver.get(self.googleSignup)

    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            logger.error("Exception occoured:")
            traceback.print_exception(exc_type, exc_value, traceback)

            return True

        logger.debug("Quitting chromium")
        self._driver.quit()

    def usernameField(self):
        return self._driver.find_element(By.ID, 'username')

    def firstnameField(self):
        return self._driver.find_element(By.ID, 'firstName')
    
    def errorField(self):
        return self._driver.find_element(By.CLASS_NAME, self.classID)

    def tesMail(self, mail):
        logger.debug(f"Testing {mail}")

        self.usernameField().clear()
        self.firstnameField().clear()

        self.usernameField().send_keys(mail)
        self.firstnameField().send_keys('placeholder')

        time.sleep(1)

        try:
            self.errorField().text

            logger.info(f"Email {mail}@gmail.com exists")
            return True
        except NoSuchElementException:
            logger.debug(f"{mail} does not exist.")
            return False
        except:
            logger.warning("wtf just happened")
            pass

def isNumeric(value):
    try:
        int(value)
    except ValueError:
        return False
    return True

logger.debug(f"Data provided: {data}")
logger.debug(f"Using separators {sep}")
logger.debug("Loading configuration from 'config.json'")
config = {}
with open('config.json', 'r') as file:
    config = json.load(file)

logger.info("Generating all possible username")

if config['initials']['use']:
    logger.debug("    Calculating initials")
    initials = []
    for value in data:
        if isNumeric(value): continue       # You don't want to get the initial of a number.
        #if len(value) < 2: continue        # I don't remember why I put this.

        initials.append('\x1F' + value[0])  # This way I can recognize them later.
    data += initials

if config['random_numbers']['use']:
    for n in config['random_numbers']['digits']:
        data += range(pow(10, n-1), pow(10, n))

all = []
logger.debug(f"    Generating all possible permutations from {len(data)} elements...")
for i in range(1 if config['allow_single_data'] else 2, len(data)):
    for e in permutations(data,i):
        all.append(list(e))

if not config['initials']['allow_middle']:
    logger.debug("    Removing middle initials")
    for entry in all:
        for value in entry[1:-1]:
            if entry[0] != '\x1F': continue

            all.remove(entry)
            break

logger.debug("    Considering special modifications")

# ['alessio', 'orsini'] generi '.ao'
# withInitials = []
# for entry in all:
#     string = ''
#     for value in entry:
#         if isNumeric(value): continue
#         string += value[0]
    
#     for i in range(len(string)):
#         for j in range(i + 1, len(string) + 1):
#             entryCpy = entry[:]
#             entryCpy.append('\x1F' + string[i:j])
#             withInitials.append(entryCpy)

#             entryCpy.pop()
#             entryCpy.insert(0, '\x1F' + string[i:j])
#             withInitials.append(entryCpy)

#             logger.debug(f"        Calulated initials {string[i:j]}, new entries: {withInitials[-1]}, {withInitials[-2]}")
# all += withInitials

# If there's a number with four digit, make an entry with only the last two
if not config['random_numbers']['use']:
    toAdd = []
    for entry in all:
        for value in entry:
            if (len(value) != 4): continue
            if not isNumeric(value): continue

            entryCpy = entry[:]
            newValue = value[2:]

            index = entryCpy.index(value)

            entryCpy.pop(index)
            entryCpy.insert(index, newValue)
            toAdd.append(entryCpy)

            #logger.debug(f"    Added {entryCpy} from {entry}")
    all += toAdd

# ['alessio', 'orsini'] -> ['alessiorsini']
if config['truncate_and_join']:
    for i in range(len(all)):
        entry = all[i]
        for j in range(len(entry) - 1):
            if isNumeric(entry[j]) or isNumeric(entry[j + 1]): continue
            if entry[j][0] == '\x1F' or entry[j + 1][0] == '\x1F': continue

            if entry[j][-1] == entry[j + 1][0]:
                newValue = entry[:j]
                newValue += [entry[j][:-1] + entry[j + 1][:]]

                if j < len(entry) - 2: 
                    newValue += entry[j+2:]

                all.insert(i + 1, newValue)
                #logger.debug(f"       {entry}: {newValue}")

for entry in all:
    for i in range(len(entry)):
        if entry[i][0] == '\x1F': 
            entry[i] = entry[i][1:]

logger.debug("    Adding separators")
withSeparators = []
for entry in all:
    if len(entry) < 2: continue
    
    for prod in product(sep, repeat=len(entry) - 1):
        entryCpy = entry[:]
        for i in range(len(prod)):
            if entryCpy[i] in sep: continue
            entryCpy.insert(i + 1, prod[i])

        withSeparators.append(entryCpy)
all += withSeparators

logger.debug("    Removing possible duplicates")
new = []
for entry in all:
    if entry not in new:
        new.append(entry)
all = new

for entry in all:
    test = ''.join(entry)

    exclude = config['exclude']['list']

    if config['exclude']['from_file'] is not None:
        with open(config['exclude']['from_file']) as file:
            exclude += file.readlines()

    if (len(test) < 6 or len(test) > 30 
    or (isNumeric(test) and not config['allow_only_numeric'])
    or any(test.startswith(element) for element in config['deny_begin'])
    or any(mail.startswith(test) for mail in exclude)):
        all.remove(entry)

# TODO l'attesa di un secondo potrebbe non essere abbastanza per far comparire l'errore
# si potrebbero usare diverse schede per velocizzare il tutto
logger.info("Searching a match...")
logger.info(f"This may take a while, about {floor(len(all) / 60)} minutes.")
with Browser() as browser, open("results.lst", 'w') as file:
    for entry in all:
        test = ''.join(entry)
        if browser.tesMail(test):
            file.write(f"{test}@gmail.com\n")
            
logger.info("Done.")
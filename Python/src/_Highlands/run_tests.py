############################################################
#
#    Highlands Server
#
#    © Highlands Negotiations, June 2018, v0.6
#
############################################################

import pandas as pd
import subprocess, os, sys, re, time
from threading import Thread
from selenium import webdriver


browser = None
def startBrowser(url):
    global browser
    os.environ["PATH"] = "testing" + os.pathsep + os.environ["PATH"]

    try:
        browser = webdriver.Chrome(executable_path=r"chromedriver.exe")
    except: pass
    try:
        browser = webdriver.Chrome(executable_path=r"chromedriver")
    except: pass
    try:
        browser.get(url)
    except Exception as e:
        print(e)
        print("aborting ...")
        sys.exit()

def stopBrowser():
    global browser
    browser.close()

def scrollTo(element):
    global browser
    browser.execute_script("arguments[0].scrollIntoView();", element)
    
def enterText(question, text):
    global browser
    selector = "input#text-{}".format(question)
    element = browser.find_element_by_css_selector(selector)
    scrollTo(element)
    element.send_keys(text);   

def enterTextArea(question, text):
    global browser
    selector = "textarea#text-{}".format(question)
    element = browser.find_element_by_css_selector(selector)
    scrollTo(element)
    element.send_keys(text);   

def clickTable(question, row, col):
    selector = "input#radio-{}-{}-{}".format(question, row, col)
    clickIt(selector)
    
def clickTable2(question, row, col):
    selector = "input#radio-{}-{}-{}".format(question, row, col)
    clickIt(selector)
    
def clickRadio(question, col):
    selector = "input#radio-{}-{}".format(question, col-1)
    clickIt(selector)

def clickCheckbox(question, col):
    selector = "input#check-{}-{}".format(question, col-1)
    clickIt(selector)

def submit(choice):
    global browser
    clickIt("#showResults")
    browser.implicitly_wait(10) # seconds
    if choice == "Yes": clickIt("#continue-yes")
    if choice == "No": clickIt("#continue-no")


def clickIt(selector):
    global browser
    element = browser.find_element_by_css_selector(selector)
    scrollTo(element)
    element.click();   

def startServer():
    # start the server in a background thread
    try:
        serverThread = Thread(target=startServerInBackground)
        serverThread.start()
        time.sleep(5)
    except OSError as e:
        pass    # ignore this error (server already started)
        
def startServerInBackground():
    try:
        subprocess.check_output("python server.py".split(), stderr=subprocess.STDOUT, shell=True)
    except OSError as e:
        pass    # server has already started
    except Exception as e:
        print(e)

def readExcelFile(page):
    table = pd.read_excel(excelFile, page)
    return table
    
    
def doValidation(table):
    validation = table[pd.notnull(table["OptionCount"])]
    validation = validation.dropna(axis="columns")
    validation = validation.drop(["Section", "Text"], axis="columns")
    rows, cols = validation.shape

    for testNo in range(1, cols-3): # 3 non test columns
        for index, row in validation.iterrows():
            question = row["Question"]
            category = row["Category"]
            optionCount = row["OptionCount"]
            data = "Test{}".format(testNo)
            values = row[data]
            if category == "radio":
                if optionCount < values or values < 1: 
                    print("Option out of range in test {}, question {}".format(testNo, question))
                    sys.exit()
            if category == "table":                
                values = [int(x) for x in re.split("[ ]+", values)]
                items, Max = [int(x) for x in optionCount.split(",")]
                if len(values) != items:
                    print("Not enough values in test {}, question {}".format(testNo, question))
                    sys.exit()
                if max(values) > Max or min(values) < 1:
                    print("Option out of range in test {}, question {}".format(testNo, question))
                    sys.exit()
            if category == "table2": 
                rowValue, colValue = [int(x) for x in re.split("[ ]+", values)]
                rowMax, colMax = [int(x) for x in optionCount.split(",")]
                if rowValue > rowMax or rowValue < 1 or colValue > colMax or colValue < 1:
                    print("Option out of range in test {}, question {}".format(testNo, question))
                    sys.exit()
            if category == "checkbox":
                if isinstance(values, int):
                    values = [values]
                else:
                    values = [int(x) for x in re.split("[ ]+", values)]
                if len(values) > optionCount:
                    print("Too many values in test {}, question {}".format(testNo, question))
                    sys.exit()
                if max(values) > optionCount or min(values) < 1: 
                    print("Option out of range in test {}, question {}".format(testNo, question))
                    sys.exit()
    
def getNamesAndPasswords():
    pd.set_option('display.width', 1000)
    table = readExcelFile('setup')
    rootFrame = table[(table.TYPE == "user") & (table.NAME == "root")]
    managerFrame = table[(table.TYPE == "user") & (table.NAME == "manager")]
    databaseFrame = table[table.TYPE == "database"]
    hostFrame = table[table.TYPE == "host"]

    root = rootFrame["NAME"].tolist()[0]
    rootPassword = rootFrame["OPTION"].tolist()[0]
    manager = managerFrame["NAME"].tolist()[0]
    managerPassword = managerFrame["OPTION"].tolist()[0]
    database = databaseFrame["NAME"].tolist()[0]
    table = databaseFrame["OPTION"].tolist()[0]
    server = hostFrame["NAME"].tolist()[0]
    port = hostFrame["OPTION"].tolist()[0]
    return [root, rootPassword, manager, managerPassword, database, table, server, port]

def parseCommandLine():
    # default excel file is "highlands.xlsx", but can be changed on command line:
    #    python server.py [excel-file]
    if len(sys.argv) > 2:
        print("Useage: python server.py [excel-file]")
        sys.exit()
    if len(sys.argv) == 1:
        excelFile = "highlands.xlsx"
    else:
        excelFile = sys.argv[1].replace(".xlsx", "") + ".xlsx"
    
    if not os.path.isfile(excelFile):
        print("{} does not exist".format(excelFile))
        sys.exit()

    return excelFile
    
excelFile = parseCommandLine()
root, rootPassword, manager, managerPassword, database, table, server, port = getNamesAndPasswords()
pd.set_option('display.width', 1000)
table = readExcelFile('tests')
table = table[pd.notnull(table['Question'])]
table['Question'] = table['Question'].astype(int)
doValidation(table)
table = table.dropna(axis="columns")
table.drop(axis=1, labels="Text", inplace=True)

try:
    rows, cols = table.shape
    
    for testNo in range(1, cols-1):  # 1 non test column
        startBrowser("http://{}:{}/client.html".format(server, port))
        print("Starting Test {}".format(testNo))
        data = "Test{}".format(testNo)
        df = table[["Question", "Category", data]]
        for index, row in df.iterrows():
            question = row["Question"]
            category = row["Category"]
            values = row[data]
            if category == "text":     enterText(question, values)
            if category == "textarea": enterTextArea(question, values)
            if category == "radio":    clickRadio(question, values)
            if category == "email":    enterText(question, values)
            if category == "client":   enterText(question, values)
            if category == "table":
                for i, value in enumerate(values.split()):
                    clickTable(question, i+1, value)
            if category == "table2":
                values = str(values)
                row, col = values.split()
                clickTable2(question, row, col)
            if category == "checkbox":
                values = str(values)
                for value in values.split():
                    clickCheckbox(question, int(value))
        submit("No")
        stopBrowser()
        
except Exception as e:
    print(e)

print("Completed Tests")

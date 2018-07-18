############################################################
#
#    Highlands Server
#
#    © Highlands Negotiations, June 2018, v0.5
#
############################################################

import pymysql.cursors
import pandas as pd
import numpy as np
import uuid
import datetime
from ast import literal_eval
import server_excel as xl
#from openpyxl.utils.cell import rows_from_range

def __init__(file):
    global excelFile
    excelFile = file
#cgitb.enable()
pd.set_option('display.max_rows', 1000)

def connect():
    connection = pymysql.connect(host='localhost',
                                 user=manager,
                                 password=managerPassword,
                                 db=database,
                                 charset='utf8mb4',
                                 cursorclass=pymysql.cursors.DictCursor)
    return connection

def getNamesAndPasswords():
    pd.set_option('display.width', 1000)
    table = pd.read_excel(excelFile, 'setup')
    table = table.drop(['COMMENTS'], axis=1)
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

def saveResults(results):
    connection = connect()
    try:
        resultsAsString = ','.join(str(e) for e in results)
        
        resultsAsTuple = literal_eval(resultsAsString)
        email = ""
        for keyValuePair in resultsAsTuple:
            if "email" in keyValuePair: 
                d = keyValuePair["email"]
                email = d["name"]
                break
            
        with connection.cursor() as cursor:
            # Create a new record
            sql = """INSERT INTO `{}` (`guid`, `timestamp`, `email`, `result`) 
                               VALUES (   %s,          %s,      %s,       %s)""".format(table)
            guid = str(uuid.uuid4())
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(sql, (guid, timestamp, email, resultsAsString))
        # connection is not autocommit by default. So you must commit to save your changes.
        connection.commit()    
        print("1 record committed")
    except Exception as e:
        print("rollback")
        print(e)
        connection.rollback()
    finally:
        connection.close()

def printResults():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
            for row in results:
                print(row)
    finally:
        connection.close()

def getChartData2():
    """
    Summary of marks grouped by {section,client} pairs
    xaxis: marks
    yaxis: [section, client]
    """
    try:
        client
    except NameError:
        client = ""
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
            
            chartData = pd.DataFrame(columns=['client','section','marks'])
            
            for row in results:
                keyValuePairs = literal_eval(row['result'])

                for pair in keyValuePairs:
                    if "client" in pair: 
                        d = pair["client"]
                        client = d["name"]
                        break
                
                # not used at present
                for pair in keyValuePairs:
                    if "email" in pair: 
                        d = pair["email"]
                        email = d["name"]
                        break
                
                for pair in keyValuePairs:
                    def addItem(section, marks): # last parameter must be a list
                        for mark in marks:
                            data = {
                                    'client' : client,
                                    'section': section,
                                    'email': email,
                                    'marks'  : mark
                                   }
                            return chartData.append(data, ignore_index=True)
                    # marks are presented differently in radio, checkbox and table entries:
                    #   radio:    a single mark which needs to be put in a list
                    #   checkbox: a string of marks which need to be split() into a list
                    #   table:    marks are already a list
                    if 'radio' in pair:
                        chartData = addItem(pair["radio"]["section"], [pair["radio"]["marks"]])
                    if 'checkbox' in pair:
                        chartData = addItem(pair["checkbox"]["section"], pair["checkbox"]["marks"].split())
                    if 'table' in pair:
                        chartData = addItem(pair["table"]["section"], pair["table"]["marks"])
        chartData[['marks']] = chartData[['marks']].apply(pd.to_numeric)  
        chartData = chartData.groupby(['section', 'client']).sum()
        chartData = chartData.to_dict()['marks']
        chartData = {"{},{}".format(compositeKey[0], compositeKey[1]):chartData[compositeKey] for compositeKey in chartData}
    finally:
        connection.close()
    return chartData

def getChartData3():
    """
    Summary of marks grouped by {section,client,email} triples
    xaxis: marks
    yaxis: [section, client, email]
    """
    try:
        client
    except NameError:
        client = ""
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
            
            chartData = pd.DataFrame(columns=['client','section','email','marks'])
            
            for row in results:
                keyValuePairs = literal_eval(row['result'])

                for pair in keyValuePairs:
                    if "client" in pair: 
                        d = pair["client"]
                        client = d["name"]
                        break
                
                # not used at present
                for pair in keyValuePairs:
                    if "email" in pair: 
                        d = pair["email"]
                        email = d["name"]
                        break
                
                for pair in keyValuePairs:
                    def addItem(section, marks): # last parameter must be a list
                        for mark in marks:
                            data = {
                                    'client' : client,
                                    'section': section,
                                    'email': email,
                                    'marks'  : mark
                                   }
                            return chartData.append(data, ignore_index=True)
                    # marks are presented differently in radio, checkbox and table entries:
                    #   radio:    a single mark which needs to be put in a list
                    #   checkbox: a string of marks which need to be split() into a list
                    #   table:    marks are already a list
                    if 'radio' in pair:
                        chartData = addItem(pair["radio"]["section"], [pair["radio"]["marks"]])
                    if 'checkbox' in pair:
                        chartData = addItem(pair["checkbox"]["section"], pair["checkbox"]["marks"].split())
                    if 'table' in pair:
                        chartData = addItem(pair["table"]["section"], pair["table"]["marks"])
        chartData[['marks']] = chartData[['marks']].apply(pd.to_numeric)  
        chartData = chartData.groupby(['section', 'client', 'email']).sum()
        chartData = chartData.to_dict()['marks']
        chartData = {"{},{},{}".format(compositeKey[0], compositeKey[1], compositeKey[2]):chartData[compositeKey] for compositeKey in chartData}
    finally:
        connection.close()
    return chartData

def getPieChartQuestionsAndOptions():
    questions = xl.filterQuestions("radio")
    options = xl.filterOptions("radio")
    questionsAndOptions = pd.concat([questions, options], axis=1)
    return questionsAndOptions.values.tolist()

def getPieChartData():
    ''' this routine returns pie chart data for the query:
            frequencies for all questions
            
        results are returned as a 2D list in the form:
            [ [frequencies for all questions-1], [frequencies for all questions-2], ...]
    '''
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
            
            chartData = []
            for row in results:
                arr = []
                keyValuePairs = literal_eval(row['result'])
                for pair in keyValuePairs:
                    if 'radio' in pair:
                        arr.append((pair["radio"]["selection"],pair["radio"]["optionCount"]))
                chartData.append(arr)
    finally:
        connection.close()

    chartData = pd.DataFrame(chartData)
    
    def seriesAsFrequencies(series):
        # pd.value_count doesn't return anything for missing indices and sorts highest frequency first
        # so convert to a list in order including zero counts
        optionCount = int(series.index.values.tolist()[0][1])
        frequencies = [0]*optionCount
        for (value,size),count in series.iteritems():
            frequencies[int(value)] = count
        return frequencies
        
    recordCount = chartData.shape[1]
    frequencies = []
    for i in range(recordCount):
        series = pd.value_counts(chartData[i])
        frequencies.append(seriesAsFrequencies(series))
    chartData = pd.DataFrame(frequencies)
    chartData.fillna(-1, inplace=True)
    chartData = chartData.astype(int)

    return pd.DataFrame(chartData).values.tolist()

def getChartData():
    """
    Summary of marks for each database record
    xaxis: marks
    yaxis: [section, client]
    tooltip: email
    """
    try:
        client
    except NameError:
        client = ""
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
            chartData = pd.DataFrame(columns=['guid', 'client','section','email','marks'])
            
            if(len(results) == 0): return {}    # return empty dict if no records found
            for row in results:
                guid = row['guid']
                keyValuePairs = literal_eval(row['result'])

                for pair in keyValuePairs:
                    if "client" in pair: 
                        d = pair["client"]
                        client = d["name"]
                        break
                
                for pair in keyValuePairs:
                    if "email" in pair: 
                        d = pair["email"]
                        email = d["name"]
                        break
                
                for pair in keyValuePairs:
                    def addItem(section, marks): # last parameter must be a list
                        for mark in marks:
                            data = {
                                    'guid'   : guid,
                                    'client' : client,
                                    'section': section,
                                    'email'  : email,
                                    'marks'  : mark
                                   }
                            return chartData.append(data, ignore_index=True)
                    # marks are presented differently in radio, checkbox and table entries:
                    #   radio:    a single mark which needs to be put in a list
                    #   checkbox: a string of marks which need to be split() into a list
                    #   table:    marks are already a list
                    if 'radio' in pair:
                        chartData = addItem(pair["radio"]["section"], [pair["radio"]["marks"]])
                    if 'checkbox' in pair:
                        chartData = addItem(pair["checkbox"]["section"], pair["checkbox"]["marks"].split())
                    if 'table' in pair:
                        chartData = addItem(pair["table"]["section"], pair["table"]["marks"])
        chartData[['marks']] = chartData[['marks']].apply(pd.to_numeric)
        chartData = chartData.groupby(['section', 'client','email','guid']).sum()
        chartData = chartData.to_dict()['marks']
        chartData = {"{},{} <{}>,{}".format(compositeKey[0], compositeKey[1], compositeKey[2], compositeKey[3]):chartData[compositeKey] for compositeKey in chartData}
    finally:
        connection.close()
    return chartData    # return a dict

def main(file):
    global root, rootPassword, manager, managerPassword, database, table, server, port
    global excelFile
    excelFile = file
    root, rootPassword, manager, managerPassword, database, table, server, port = getNamesAndPasswords()

def getPieChartData2():
    ''' this routine returns pie chart data for three types of query:
            all: frequencies for all questions
            email: frequencies for questions filtered by email
            client: frequencies for questions filtered by client
        results are returned as a dictionary of 2D arrays in the form:
            { 'all': <frequencies for all questions>,
              'email-1': [ [frequencies for questions-1], [frequencies for questions-2], ...],
              'email-2': [ [frequencies for questions-1], [frequencies for questions-2], ...],
              ...
              'client-1': [ [frequencies for questions-1], [frequencies for questions-2], ...],
              'client-2': [ [frequencies for questions-1], [frequencies for questions-2], ...],
              ...
            }
    '''
    def getEmails(results):
        emails = []
        for row in results:
            emails.append(row['email'])
        return list(set(emails))  # pick out unique emails
    
    def getClients(results):
        clients = []
        for row in results:
            keyValuePairs = literal_eval(row['result'])
            for pair in keyValuePairs:
                if 'client' in pair:
                    clients.append(pair['client']['name'])
        return list(set(clients))  # pick out unique clients

    def getClient(row):
        keyValuePairs = literal_eval(row['result'])
        for pair in keyValuePairs:
            if 'client' in pair:
                return pair['client']['name']
        raise("client missing from record")
    
    def getEmail(row):
        return row['email']
    
    def seriesAsFrequencies(series):
        # pd.value_count doesn't return anything for missing indices and sorts highest frequency first
        # so convert to a list in order including zero counts
        optionCount = int(series.index.values.tolist()[0][1])
        frequencies = [0]*optionCount
        for (value,size),count in series.iteritems():
            frequencies[int(value)] = count
        return frequencies
        
    def calculateFrequencies(chartData):
        recordCount = chartData.shape[1]
        frequencies = []
        for i in range(recordCount):
            series = pd.value_counts(chartData[i])
            frequencies.append(seriesAsFrequencies(series))
        chartData = pd.DataFrame(frequencies)
        chartData.fillna(-1, inplace=True)
        chartData = chartData.astype(int)
        return chartData
    
    def getData(results, filterType = "", filter = "all"):
        chartData = []
        for row in results:
            if filterType == 'email': 
                if getEmail(row) != filter: continue
            if filterType == 'client': 
                if getClient(row) != filter: continue
            arr = []
            keyValuePairs = literal_eval(row['result'])
            for pair in keyValuePairs:
                if 'radio' in pair:
                    arr.append((pair["radio"]["selection"],pair["radio"]["optionCount"]))
            chartData.append(arr)
        return chartData
         
    def gatherPieInformation():
        connection = connect()
        try:
            with connection.cursor() as cursor:
                sql = "SELECT `*` FROM `{}`".format(table)
                cursor.execute(sql)
                results = cursor.fetchall()
                emails = getEmails(results)
                clients = getClients(results)
                pie = {}
                pie['all'] = getData(results)
                for email in emails:
                    pie[email] = getData(results, 'email', email)
                for client in clients:
                    pie[client] = getData(results, 'client', client)
        finally:
            connection.close()

        def convertToList(key):
            chartData = pd.DataFrame(pie[key])
            chartData = calculateFrequencies(chartData)
            return pd.DataFrame(chartData).values.tolist()

        allPies = {}
        for key in pie:
            allPies[key] = convertToList(key)
        return allPies
    return gatherPieInformation()

def getEmailsAndClients():
    def getEmails(results):
        emails = []
        for row in results:
            emails.append(row['email'])
        return list(set(emails))  # pick out unique emails
    
    def getClients(results):
        clients = []
        for row in results:
            keyValuePairs = literal_eval(row['result'])
            for pair in keyValuePairs:
                if 'client' in pair:
                    clients.append(pair['client']['name'])
        return list(set(clients))  # pick out unique clients

    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
            emails = getEmails(results)
            clients = getClients(results)
    finally:
        connection.close()
    return emails, clients

def getDatabaseResults():
    connection = connect()
    try:
        with connection.cursor() as cursor:
            sql = "SELECT `*` FROM `{}`".format(table)
            cursor.execute(sql)
            results = cursor.fetchall()
    finally:
        connection.close()
    return results

def getScatterChartData():
    # this routine assumes the client always comes before othe results
    scatterData = {}
    frequencies = {}
    results = getDatabaseResults()
    for row in results:
        email = row["email"]
        keyValuePairs = literal_eval(row['result'])
        for pair in keyValuePairs:
            if 'client' in pair:
                client = pair['client']['name']
            if 'table2' in pair:
                choiceRow, choiceCol = [int(x) for x in pair['table2']['selection'].split(':')]
                table2Rows, table2Cols = [int(x) for x in pair['table2']['optionCount'].split(':')]
                r = choiceRow-1
                c = choiceCol-1
                if 'xLabels' not in scatterData: scatterData['xLabels'] = pair['table2']['xLabels']
                if 'yLabels' not in scatterData: scatterData['yLabels'] = pair['table2']['yLabels']
                if 'all' not in frequencies:  frequencies['all'] = np.zeros((table2Rows, table2Cols), int).tolist()
                if client not in frequencies: frequencies[client] = np.zeros((table2Rows, table2Cols), int).tolist()
                if email not in frequencies:  frequencies[email] = np.zeros((table2Rows, table2Cols), int).tolist()
                frequencies['all'][r][c] += 1
                frequencies[client][r][c] += 1
                frequencies[email][r][c] += 1
    scatterData['frequencies'] = frequencies
    return scatterData

if __name__ == "__main__":
    main("highlands.xlsx")
    scatterData = getScatterChartData()
    print(scatterData)
    for key in scatterData['frequencies']:
        print(key, scatterData['frequencies'][key])

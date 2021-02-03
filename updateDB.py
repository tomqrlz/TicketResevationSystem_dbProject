import csv
import MySQLdb

db = MySQLdb.connect(host="localhost",  # your host, usually localhost
                     user="root",  # your username
                     passwd="",  # your password
                     db="g03")  # name of the data base

stadiumID = list()
with open("data/teams.csv") as csvFile:
    csvReader = csv.DictReader(csvFile, fieldnames=("Team", "Stadium", "Location"), delimiter=",")
    firstline = True
    for row in csvReader:
        if firstline == True:
            firstline = False
            continue
        cur = db.cursor()
        cur.execute("INSERT INTO stadium VALUES (NULL, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (row["Stadium"], "A", 200, 20, "B", 200, 20, "C", 100, 20, "D", 100, 20, row["Team"],
                     row["Location"]))
        if row["Stadium"] not in stadiumID:
            stadiumID.append(row["Stadium"])
        db.commit()

with open("data/fixtures.csv") as csvFile:
    csvReader = csv.DictReader(csvFile, fieldnames=("Round Number", "Date", "Stadium", "Home Team", "Away Team",
                                                    "Result", "Location"), delimiter=",")
    cur = db.cursor()
    firstline = True
    index = 0

    for row in csvReader:
        if firstline == True:
            firstline = False
            continue
        i = 0
        for i in range(len(stadiumID)):
            if row["Stadium"] == stadiumID[i]:
                print("EESSSSAA")
                index = i + 1
        cur.execute("INSERT INTO matchschedule VALUES (NULL ,%s, %s, %s, %s, %s)",
                    (row["Round Number"], row["Home Team"], row["Away Team"], index, row["Date"]))
        db.commit()


db.close()

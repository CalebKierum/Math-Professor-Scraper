'''
Copyright 2017 Caleb Kierum

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
'''

#Import statements
import urllib2
from bs4 import BeautifulSoup
from collections import namedtuple
import collections
import operator

#Global file we will use to print our logs in
F = open("report.txt", "w")
F.close()

#These tuples are used to organize things in a dictionary later. It esentially implements a
#map of a string key to an array of these tuples
Data = namedtuple('Data', ['professor', 'classNum', 'classTitle', 'section', 'rating'])
datas = []
ClassData = namedtuple('ClassData', ['professor', 'section', 'rating', 'title'])
ProfessorData = namedtuple('ProfessorData', ['classNum', 'classTitle', 'rating', 'section'])

# Default value but can be overridden by user input
quarter = "Winter 2018"


def lprint(thing):
    print(thing)
    F.write(thing + "\n")

    

#Finds a UW professor from the list or results and returns its URL ending
def findUWProfessor(soup):
    listings = soup.find("ul", class_="listings")
    professors = listings.find_all("li", class_="listing PROFESSOR")
    for prof in professors:
        school = prof.find("span", class_="sub").text
        if "University of Washington" in school:
            return soup.find("ul", class_="listings").find("a").get("href")

    return "NULL"

def getRatingForProfessor(name):
    #We are going to emulate a reatemyprofessors search
    base = "http://www.ratemyprofessors.com/search.jsp?query="

    #Search query is separated by "+"
    parts = name.split(" ")
    i = 0
    for part in parts:
        if i != 0:
            base += "+"
        i += 1
        base += part

    #Open up the search results
    page = urllib2.urlopen(base)
    soup = BeautifulSoup(page)

    #Find a uw professor from them
    end = findUWProfessor(soup)
    if (end == "NA"):
        return "NA"

    #Open up the professor page
    startpoint = "http://www.ratemyprofessors.com/" + end
    page2 = urllib2.urlopen(startpoint)
    soup2 = BeautifulSoup(page2)

    #Scrape their rating
    return soup2.find("div", class_="rating-breakdown").find("div", class_="breakdown-container quality").find("div", class_="grade").text

#Simply checks for some of the fake professors that get in the original scrape
def isPerson(name):
    if "teaching-assistants" in name or "graduate-student" in name or "faculty" in name or "staff" in name:
        return False
    else:
        return True

#Grabs a list of all the endpoints for all the professors listed
def getPeopleList():
    #We are using beautiful soup and urllib2 to scrape the main faculty list for endpoints
    MainWebpage = "https://math.washington.edu/people/faculty"
    page = urllib2.urlopen(MainWebpage)
    soup = BeautifulSoup(page)

    # Set automatically gets rid of extra content
    people = set([])

    #Find links
    links = soup.findAll("a")
    for link in links:
        content = str(link.get("href"))
        if "people/" in content and not "http" in content:
            #Make sure they are a real person
            if (isPerson(content)):
                people.add(content)

    return people

#Deals with cases where initials are at various points of the actual name string
def cleanName(text):
    splitted = text.split(" ")
    if (len(splitted) == 3):
        str1 = str(splitted[0])
        str2 = str(splitted[1])
        str3 = str(splitted[2])

        #Essentially return 2 of the three parts but not the one with the period
        if "." in str1:
            return str2 + " " + str3
        elif "." in str2:
            return str1 + " " + str3
        else:
            return str1 + " " + str2
    else:
        return text


#Gets all of the data for a professor given their endpoint
def getDataForPerson(endpoint):
    if not "faculty" in endpoint and not "Teaching Assistants" in endpoint:\
        #Open up their faculty page
        webpage = "https://math.washington.edu" + endpoint
        page = urllib2.urlopen(webpage)
        soup = BeautifulSoup(page)

        #Extract their name
        Professor = cleanName(soup.find("title").text.split("|")[0].strip())

        #Extract their rating (we do try as the rate my professor website can be unpredictable)
        rating = "NA"
        try:
            rating = getRatingForProfessor(Professor)
        except:
            pass


        # They did not put any class types in their HTML so it is a bit complicated and inefficient to parse
        parts = soup.findAll("div", class_="view-content")
        for part in parts:
            #So we want the content between two h3 tags so we find it
            sections = part.find_all('h3', string=quarter)

            #Then pull out all its sibiling <a> tags
            for section in sections:
                for item in section.next_sibling.next_sibling.find_all('a'):

                    #The course should be formatted a certain way but in occasional pages it is slightly different
                    if ":" in item.text:
                        link = str(item.get('href'))
                        text = str(item.text)

                        sections = text.split(':')

                        parts = sections[0].split(' ')

                        #Parse out the various bits of it
                        className = sections[1].strip()
                        classNumber = parts[1]
                        section = parts[2]

                        #In rare cases this shows up in the html for some reason so account for it.
                        if not "property object" in str(section):
                            #KEY INSIGHT!!!!!
                            #The str() function has issues with certain sizes and inputs and is bad for memory
                            #Instead encode everything here so that all that is out of the way at the beginning
                            datas.append(Data(professor=Professor.encode("utf-8").strip(), classNum = classNumber.encode("utf-8").strip(), classTitle = className.encode("utf-8").strip(), section = section.encode("utf-8").strip(), rating = rating.encode("utf-8").strip()))



#This does all the heavy lifting filling datas with all we can know from the math site
def scrapeAllData():
    lprint("Scraping all of the data...this could take a bit")
    #Get a list of all the people
    endpoints = getPeopleList()
    lprint("Got people list!")

    #This is code essentially just scrapes per person
    #a lot of the extra stuff is just to make it only print progress occasionally
    prog = 0
    total = len(endpoints)
    last = 0
    for endpoint in endpoints:
        prog += 1
        getDataForPerson(endpoint)
        percent = round(float(prog) / float(total) * 100, 0)
        #We want to print ever 5 percent so devide by 5
        symbolicate = int(percent) / 5
        if (symbolicate != last):
            last = symbolicate
            lprint(str(percent) + "%")
        if (prog < 5):
            #Sometimes scraping takes a ridiculously long time this helps one understand the pace it will happen at
            lprint("Scraped our " + str(prog) + "th person")

    lprint("Done scraping all the data")


#Prints all the data in an unorganized manner
def printAllData():
    lprint("-------------------------------------------")
    lprint("Reporting all data:")
    lprint("")

    for d in datas:
        lprint ("Professor " + str(d.professor) + " (" + str(d.rating) + ")"+ " is teaching " + str(d.classTitle) + " (" + str(d.classNum) + ") " + " section " + str(d.section))

#Prints all the data per class
def printByClass():
    lprint("-------------------------------------------")
    lprint("Report by class:")
    lprint("")

    #First fill up a dictionary where class num is the key and the value is an array of ClassData
    themap = {}
    for d in datas:
        if not d.classNum in themap:
            #We dont have an array here so just add a new one
            themap[d.classNum] = [ClassData(professor=d.professor, section=d.section, rating=d.rating, title=d.classTitle)]
        else:
            themap[d.classNum].append(ClassData(professor=d.professor, section=d.section, rating=d.rating, title=d.classTitle))

    #Order the keys for fancyness Reasons
    themap = collections.OrderedDict(sorted(themap.items()))
    for k,v in themap.items():
        #Print out the header of it
        lprint("MATH " + str(k) + " " + str(v[0].title))
        for section in v:
            #Print out the data for the professor
            lprint("\tProfessor " + str(section.professor) + " (" + str(section.rating) + ") section: " + str(section.section))
        lprint("")

#Print all the data relative to the professor
def printByProfessor():
    lprint("-------------------------------------------")
    lprint("Report by professor:")
    lprint("")

    #Fill up a map where the professor name is a key to a ProfessorData tuple
    themap = {}
    for d in datas:
        if not d.professor in themap:
            #We dont have an array so add a new one
            themap[d.professor] = [ProfessorData(classNum=d.classNum, classTitle=d.classTitle, rating=d.rating, section=d.section)]
        else:
            themap[d.professor].append(ProfessorData(classNum=d.classNum, classTitle=d.classTitle, rating=d.rating, section=d.section))

    #Sort by the names of the professor alphabetically
    themap = collections.OrderedDict(sorted(themap.items()))
    for k, v in themap.items():
        #Print the header for the professor
        lprint("Professor " + str(k) + " Rating: " + str(v[0].rating))
        for section in v:
            #Print specefic Data
            lprint("\tMATH " + str(section.classNum) + " " + str(section.classTitle) + " section " + str(section.section))
        lprint("")

def numRep(input):
    if "NA" in input:
        return 0.0
    else:
        return float(input)

def printProfessorRanking():
    lprint("-------------------------------------------")
    lprint("Ranking of each professor listed as teaching courses this quarter based on ratemyprofessor.com:")
    lprint("")

    #Fill up a map with professors and their ratings
    themap = {}
    for d in datas:
        themap[d.professor] = d.rating

    #Convert to tuple array
    items = list(themap.items())

    #Sort them by their values
    sortedV = items
    sortedV.sort(key=lambda x: numRep(x[1]))

    #Print out ones with actual values reverse because the sorting puts NA right after the highest value
    #We want it the other way
    rank = 0;
    for data in reversed(sortedV):
        if not "NA" in data[1]:
            rank += 1;
            lprint(str(rank) + ". " + str(data[0]) + ": " + str(data[1]))

    lprint("")

    #Print the list of professors without ratings
    for data in reversed(sortedV):
        if "NA" in data[1]:
            lprint(str(data[0]) + ": " + str(data[1]))

def main():

    #F is a global thing that allows us to switch writing into different files
    global F
    F = open("ProgressLog.txt", "w")

    #Get user input of what they want us to read
    quarter = raw_input("What quarter do you care about? (ex: Winter 2018) :")
    quarter = quarter.strip()

    #Scrape all the data from the web
    scrapeAllData()
    F.close()

    #Print it in a big ugly format
    F = open("BigPrint.txt", "w")
    printAllData()
    F.close()

    #Print by class
    F = open("By Class.txt", "w")
    printByClass()
    F.close()

    #Print by professor
    F = open("By Professor.txt", "w")
    printByProfessor()
    F.close()

    #Prints professor rankings in order
    F = open("Professor Rankings.txt", "w")
    printProfessorRanking()
    F.close()

    #Just to make sure it runs to completion. Sometimes odd Pycharm errors will cause it not to work well
    print("DONE")

#Run everything
main()

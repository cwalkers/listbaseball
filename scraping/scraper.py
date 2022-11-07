'''
This module scrapes web pages for baseball related data. 

Ncaa (class): the class of NCAA related functions

    schools (function): returns a dataframe of schools in the NCAA with basic information,
        scrapes from: https://www.ncaa.com/schools-index

    stats (function): returns a dictionary of schools with nested dictionaries of years
    and statistical information. 
        scrapes from: http://stats.ncaa.org/team/inst_team_list?sport_code=MBA&division=1
'''
from bs4 import BeautifulSoup
import pandas as pd
import regex as re
import requests
from urllib.request import Request, urlopen

class Ncaa: 

    def __init__(self): 
        pass

    def schools(self): 
        '''
        Scrapes the data on all schools in the NCAA listed on https://www.ncaa.com/schools-index,
        the NCAA's official webpage. It does so by iterating through each webpage which has a list of 
        schools, and for each page, iterating through the personal webpages of those schools. 

        Data is appended to columns in the order it was obtained. Some school's personal webpages do not 
        contain all of the desired data points. One school does not have a personal webpage. If a data point 
        is unavaible, a blank value is appended to the column (list). Schools without personal websites will 
        be a row of blank values. Columns are then appended to a pandas dataframe. 

        Takes multiple minutes to run.

        Inputs: None

        Returns: dataframe of schools (Pandas Dataframe), where each school has a row of column values. 
                column values: division, school, school_nickname, city, state, conference, team_name
        '''

        schools_df = pd.DataFrame()

        (division, school, school_nickname, 
        team_name, city, state, conference) = ([] for _ in range(7))

        #iterate through each page of schools
        #eg. if there are 23 pages of schools: 'range(0, 24)'
        for i in range(0, 24):
            url = 'https://www.ncaa.com/schools-index/{}'.format(i)
            r = requests.get(url)
            soup = BeautifulSoup(r.content, 'html.parser')

            #finds the web page of each school
            web_tags = soup.find('tbody').find_all('a', href=re.compile('/schools/'))
            school_endings = []

            for tag in web_tags[::2]:
                ending = tag.get('href')
                nickname = tag.text
                school_nickname.append(nickname)
                school_endings.append(ending)

            #data is on each school's webpage, so we iterate through each 
            #school's personal webpage within a given page of schools
            #if a school does not have an active personal site, append blank
            #data to columns
            for ending in school_endings: 
                try:
                    school_url = 'https://www.ncaa.com/{}'.format(ending)
                    sr = requests.get(school_url)
                    school_soup = BeautifulSoup(sr.content, 'html.parser')

                    #finds division, city, state and appends to respective columns
                    d_loc_text = ((school_soup.find('div', class_=re.compile('division-location'))).text).strip()
                    #some schools' NCAA page do not list the division, append blank values for those schools
                    try:
                        div_num, loc = d_loc_text.split('-', maxsplit=1)
                        location = loc.strip()
                        cit, stat = location.split(', ')
                    except: 
                        div_num = ''
                        cit, stat = d_loc_text.split(', ')
                    
                    division.append(div_num)
                    city.append(cit)
                    state.append(stat)

                    #finds full name of school, appends to column
                    school_text = school_soup.find('h1', class_='school-name').text 
                    school.append(school_text)

                    #finds conferece, appends to column
                    conference_tag = school_soup.find_all('div', class_=re.compile('dl-group'))[0].find('dd')
                    conference.append(conference_tag.text)

                    #finds team name, appends to column
                    teamname_tag = school_soup.find_all('div', class_=re.compile('dl-group'))[1].find('dd')
                    team_name.append(teamname_tag.text)

                except: 
                    division.append('')
                    city.append('')
                    state.append('')
                    school.append('')
                    conference.append('')
                    team_name.append('')

            print('Scraped page {}'.format(i))


        vars = (division, school, school_nickname, 
        city, state, conference, team_name)

        columns = ('division', 'school', 'school-nickname',
        'city', 'state', 'conference', 'team-name')

        #append columns to dataframe
        for i, col in enumerate(columns):
            schools_df[col] = pd.Series(vars[i])

        return schools_df

    def school_id_grabber(self): 
        '''
        Function to scrape the url endings for each school. Stores each ending
        in school_ids (dict), key is name of school, value is url ending that
        navigates to that school's stats page. Initialize before using stats.

        Inputs: None 

        Returns: school_ids (dict)
        '''

        school_ids = {} 

        req = Request(
            url='http://stats.ncaa.org/team/inst_team_list?sport_code=MBA&division=1', 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        webpage = urlopen(req).read()
        soup = BeautifulSoup(webpage, 'html.parser')

        id_tags = soup.find_all('a', href=re.compile('/team/'))[2:]

        for ids in id_tags:
            id = (ids.get('href')).split('/', maxsplit=3)[2]
            school = ids.text
            school_ids[school] = id

        return school_ids

    #fix year vals, simplify code
    def stats(self, school_ids):
        '''
        Scrapes data from the NCAA baseball stats archive:

        http://stats.ncaa.org/team/inst_team_list?sport_code=MBA&division=1

        Creates a dictionary of the available schools on the website. Each school
        has a nested dictionary for each available year. Within each year, there
        is a list of dictionaries for each stat type i.e. [Hitting, Pitching, Fielding].
        Each stat type in the list is a dictionary of conditional stats, where the keys
        are conditional stats, and the value is a pandas dataframe.

        E.x. master_stats_all['school name']['year'][0]['with 2 outs'] would return the 
        hitting stats with 2 outs in the given year for the given school

        There are 300+ schools, each with 10+ years of statistical history in the archive.
        It is not reccommended to call this funciton locally.

        Inputs: 
            None

        Returns:
            dictionary of schools (dict)
        '''

        master_stats_all = {}

        #iterate through each school that is available
        for school, id in school_ids.items(): 

            master_stats_all[school] = {}
            year_ids = [] 

            #obtain the possible years on each school's page
            req = Request(
                url = 'https://stats.ncaa.org/team/{}/stats/16340'.format(id), 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            webpage = urlopen(req).read()
            soup = BeautifulSoup(webpage, 'html.parser')
            
            year_tags = soup.find_all('a', href=re.compile('year_stat_category'))

            for year_tag in year_tags:
                year_ids.append(year_tag.get('href'))  

            #iterate through each year of statistics
            for year_val, year_id in enumerate(year_ids[2:]):

                hitting = {} 
                pitching = {}
                fielding = {}

                url = 'https://stats.ncaa.org{}'.format(year_id)
                req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
                webpage = urlopen(req).read()
                soup = BeautifulSoup(webpage, 'html.parser')

                #access the dropdown menu of conditonal stats
                drop_down = soup.find_all('select')[2].find_all('option')

                for d in drop_down: 
                    hitting[d.text] = d.get('value')

                session = requests.session()

                #iterate through each conditional stat in the dropdown menu, get table
                for stat, value in hitting.items():
                    
                    payload = {'available_stat_id': value}
                    response = session.post(
                        url, data=payload,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )

                    table = pd.read_html(response.text)[2]
                    hitting[stat] = table
                
                #do the same as above with pitching and fielding statistics
                pitch_field_url = soup.find_all('a', href=re.compile('year_stat_category_id'))
                pitch_url = (pitch_field_url[0]).get('href')

                url = 'https://stats.ncaa.org{}'.format(pitch_url)
                req = Request(url, headers = {'User-Agent': 'Mozilla/5.0'})
                webpage = urlopen(req).read()
                soup = BeautifulSoup(webpage, 'html.parser')

                p_drop_down = soup.find_all('select')[2].find_all('option')

                for p in p_drop_down: 
                    pitching[p.text] = p.get('value')

                session = requests.session()

                for p_stat, p_value in pitching.items():
                    
                    payload = {'available_stat_id': p_value}
                    response = session.post(
                        url, data=payload,
                        headers={'User-Agent': 'Mozilla/5.0'}
                    )

                    p_table = pd.read_html(response.text)[2]
                    pitching[p_stat] = p_table

                field_url = (pitch_field_url[1]).get('href')
                req = Request(
                    url = 'https://stats.ncaa.org{}'.format(field_url), 
                    headers = {'User-Agent': 'Mozilla/5.0'}
                )

                webpage = urlopen(req).read()
                f_table = pd.read_html(webpage)[2]
                fielding['Fielding'] = f_table

                #insert into master dictionary by {school: year: {stats}}
                (master_stats_all[school])[year_val] = [hitting, pitching, fielding]

                break

            break

        return master_stats_all

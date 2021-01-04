import time
from requests import HTTPError
import requests
from bs4 import BeautifulSoup as soup
import re, string
from datetime import datetime
import aiohttp
import traceback

def base_yahoo_comp(comp_name_fmtd, expected_ticker, dajson):
    # print(dajson)
    try:
        for i in range(len(dajson['ResultSet']['Result'])):
            if dajson['ResultSet']['Result'][i]['symbol'] == expected_ticker:
                # print(dajson['ResultSet']['Result'][i]['symbol'])
                return dajson['ResultSet']['Result'][i]['symbol']
        return False
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
        return False

def base_mktwatch_comp(comp_name_fmtd,expected_ticker,dainfo):
    try:
        psoup = soup(dainfo, "html.parser")
        table = psoup.find('div', {'class': 'results'})
        if not table:
            return False
        rows = table.find_all('tr')[1:]
        for row in rows:
            # print(row.find('td').text)
            if row.find('td').text == expected_ticker:
                return expected_ticker
        return False
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        print(e)
        return False

def base_find_all_consecutive_tickers(body):
    # print(body)
    stonks = re.search('([(][a-zA-Z \-]*:[A-Z0-9. ]*[) ,]*)+', body).group()
    stonks2 = re.findall('([(][a-zA-Z \-]*:[A-Z0-9. ]*[) ,]*)', stonks)
    tickers = []
    # print(stonks2)
    for stonk in stonks2:
        the2ticker = stonk.split(':', 1)[1].split(')')[0].strip()
        tickers.append(the2ticker)
    # print(the2ticker)
    return tickers

def base_gnw(page_data):
    psoup = soup(page_data, "html.parser")
    source = psoup.find('span', {'itemprop': 'author copyrightHolder'}).text
    formatted = re.split('[^a-zA-Z]', source.lower())[0]
    body = psoup.find('span', {'class': 'article-body'}).text
    stonk = re.search('[(][a-zA-Z \-]*:[A-Z0-9. ]*[)]', body).group()
    # print(stonk)
    the2ticker = stonk.split(':', 1)[1].split(')')[0].strip()
    # print(the2ticker,formatted)
    return formatted, the2ticker, psoup

def base_prnw(page_data):
    psoup = soup(page_data, "html.parser")
    source = psoup.find('div', {'class': 'col-lg-6 col-lg-offset-1 col-sm-5 col-sm-offset-1'}).find(
        'strong').text
    body = psoup.find('section', {'class': 'release-body container'}).text
    # print(body)
    formatted = re.split('[^a-zA-Z]', source.lower())[0]
    # print(formatted)
    stonk_1 = re.search('[(][a-zA-Z \-]*:[A-Z0-9. ]*[)]', body)
    if stonk_1:
        stonk_2 = stonk_1.group()
        # print(stonk)
        theticker = stonk_2.split(':', 1)[1].split(')')[0].strip()
        # print(theticker)
        return formatted, theticker, body
    return formatted, False, body

class MsgCompID:
    def __init__(self, site_id, url, is_async):
        self.site_id = site_id
        self.url = url
        self.is_async = is_async

    async def async_yahoo_comp(self, comp_name_fmtd, expected_ticker):
        dajson = await self.async_read_json_or_text(r'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&lang=en'
                                              .format(comp_name_fmtd), 'json')  # comp_name_fmtd
        return base_yahoo_comp(comp_name_fmtd,expected_ticker,dajson)

    def sync_yahoo_comp(self, comp_name_fmtd, expected_ticker):
        dajson = self.sync_read_json_or_text(r'http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&lang=en'
                                              .format(comp_name_fmtd), 'json')  # comp_name_fmtd
        return base_yahoo_comp(comp_name_fmtd,expected_ticker,dajson)

    async def async_mktwatch_comp(self, comp_name_fmtd, expected_ticker):
        dainfo = await self.async_read_json_or_text(r'https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw'
                                              r'&Lookup={}&Country=all&Type=All'.format(comp_name_fmtd), 'text')
        return base_mktwatch_comp(comp_name_fmtd,expected_ticker,dainfo)

    def sync_mktwatch_comp(self, comp_name_fmtd, expected_ticker):
        dainfo = self.sync_read_json_or_text(r'https://www.marketwatch.com/tools/quotes/lookup.asp?siteID=mktw'
                                              r'&Lookup={}&Country=all&Type=All'.format(comp_name_fmtd), 'text')
        return base_mktwatch_comp(comp_name_fmtd,expected_ticker,dainfo)


    async def async_find_all_consecutive_tickers(self, body):
        return base_find_all_consecutive_tickers(body)

    def sync_find_all_consecutive_tickers(self, body):
        return base_find_all_consecutive_tickers(body)

    async def async_get_company(self):#THERE IS NO BASE FOR THIS - NOT ENOUGH CODE TO WARRANT IT
        data = await self.async_read_json_or_text(self.url)
        if data:
            ticker = await self.async_page_analyze(data)
            return ticker
        else:
            return False  # if there is no company or there is an error, this get_company() will return False regardless

    def sync_get_company(self):#THERE IS NO BASE FOR THIS - NOT ENOUGH CODE TO WARRANT IT
        data = self.sync_read_json_or_text(self.url)
        if data:
            ticker = self.sync_page_analyze(data)
            return ticker
        else:
            return False  # if there is no company or there is an error, this get_company() will return False regardless

    async def async_page_analyze(self, page_data):
        if self.site_id == 1:
            try:
                formatted, the2ticker, psoup = base_gnw(page_data)
                mktwatch = await self.async_mktwatch_comp(formatted, the2ticker)
                theticker2 = await self.async_find_all_consecutive_tickers(psoup.find('span', {'class':
                                                                                             'article-body'}).text)
                if mktwatch in theticker2:
                    return theticker2
                else:
                    return mktwatch
            # return False
            except AttributeError as e:
                return False#oftentimes, part of the html will not exist, causing an attribute error. I think this is ok
            except:
                # print('no company yo')
                return False
        elif self.site_id == 2:
            try:
                formatted, theticker, body = base_prnw(page_data)
                if not theticker:
                    return False
                mktwatch = await self.async_mktwatch_comp(formatted, theticker)
                theticker2 = await self.async_find_all_consecutive_tickers(body)
                if mktwatch in theticker2:
                    return theticker2
                else:
                    return mktwatch
            except AttributeError as e:
                return False#oftentimes, part of the html will not exist, causing an attribute error. I think this is ok
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print(e)
                # print('no company yo')
                return False
        elif self.site_id == 3:#NO BASE BECAUSE AWAITS ARE TOO SCATTERED
            try:
                psoup = soup(page_data, "html.parser")
                # print(psoup)
                bodied = psoup.find_all('script')
                for script in bodied:
                    script = str(script)
                    if script.find(r'#companyInformation') > -1:
                        thetickerurl = script[script.find(r'#companyInformation'):].split('(\'/', 1)[1].split('\')', 1)[
                            0]
                        page_data2 = await self.async_read_json_or_text('https://www.businesswire.com/' + thetickerurl)
                        psoup2 = soup(page_data2, "html.parser")
                        source = psoup2.find('div', {'id': 'cic'}).span.text
                        fullname = psoup2.find('span', {'itemprop': 'name'}).text
                        theticker = source.split(":", 1)[1]
                        formatted = fullname.lower().split(" ", 1)[0]
                        '''.replace(" ", "")
                        formatted = re.sub(r'\W+', '', formatted)'''
                # print(formatted,theticker)
                mktwatch = await self.async_mktwatch_comp(formatted, theticker)
                body = psoup.find('article', {'class': 'bw-release-main'}).text
                theticker2 = await self.async_find_all_consecutive_tickers(body)
                if mktwatch in theticker2:
                    return theticker2
                else:
                    return mktwatch
            # return theticker
            # interm = source.split(": ",1)[1].split(")",1)[0]
            # body = psoup.find('div', {'class': 'bw-release-story'})
            # print(body.text)
            # print(formatted)
            except AttributeError as e:
                return False#oftentimes, cic will not exist, causing an attribute error. I think this is ok
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print(e)
                # print('no company yo')
                return False
        else:
            print('site id doesnt exist for comp_id, uh oh')
            return False

    def sync_page_analyze(self, page_data):
        if self.site_id == 1:
            try:
                formatted, the2ticker, psoup = base_gnw(page_data)
                mktwatch = self.sync_mktwatch_comp(formatted, the2ticker)
                theticker2 = self.sync_find_all_consecutive_tickers(psoup.find('span', {'class':
                                                                                             'article-body'}).text)
                if mktwatch in theticker2:
                    return theticker2
                else:
                    return mktwatch
            # return False
            except AttributeError as e:
                return False#oftentimes, part of the html will not exist, causing an attribute error. I think this is ok
            except:
                # print('no company yo')
                return False
        elif self.site_id == 2:
            try:
                formatted, theticker, body = base_prnw(page_data)
                if not theticker:
                    return False
                mktwatch = self.sync_mktwatch_comp(formatted, theticker)
                theticker2 = self.sync_find_all_consecutive_tickers(body)
                if mktwatch in theticker2:
                    return theticker2
                else:
                    return mktwatch
            except AttributeError as e:
                return False#oftentimes, part of the html will not exist, causing an attribute error. I think this is ok
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print(e)
                # print('no company yo')
                return False
        elif self.site_id == 3:#NO BASE BECAUSE AWAITS ARE TOO SCATTERED
            try:
                psoup = soup(page_data, "html.parser")
                # print(psoup)
                bodied = psoup.find_all('script')
                for script in bodied:
                    script = str(script)
                    if script.find(r'#companyInformation') > -1:
                        thetickerurl = script[script.find(r'#companyInformation'):].split('(\'/', 1)[1].split('\')', 1)[
                            0]
                        page_data2 = self.sync_read_json_or_text('https://www.businesswire.com/' + thetickerurl)
                        psoup2 = soup(page_data2, "html.parser")
                        source = psoup2.find('div', {'id': 'cic'}).span.text
                        fullname = psoup2.find('span', {'itemprop': 'name'}).text
                        theticker = source.split(":", 1)[1]
                        formatted = fullname.lower().split(" ", 1)[0]
                        '''.replace(" ", "")
                        formatted = re.sub(r'\W+', '', formatted)'''
                # print(formatted,theticker)
                mktwatch = self.sync_mktwatch_comp(formatted, theticker)
                body = psoup.find('article', {'class': 'bw-release-main'}).text
                theticker2 = self.sync_find_all_consecutive_tickers(body)
                if mktwatch in theticker2:
                    return theticker2
                else:
                    return mktwatch
            # return theticker
            # interm = source.split(": ",1)[1].split(")",1)[0]
            # body = psoup.find('div', {'class': 'bw-release-story'})
            # print(body.text)
            # print(formatted)
            except AttributeError as e:
                return False#oftentimes, cic will not exist, causing an attribute error. I think this is ok
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print(e)
                # print('no company yo')
                return False
        else:
            print('site id doesnt exist for comp_id, uh oh')
            return False

    async def async_read_json_or_text(self, url, which='text'):#THERE IS NO BASE FOR THIS - TOO DIFFERENT FROM THE SYNC
        async with aiohttp.ClientSession() as session:
            user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
            try:
                async with session.get(url) as response:
                    # ufile1 = ureq.urlopen(ufile0, context=ssl.create_default_context(cafile=certifi.where()))
                    # ufile1 = requests.get(url, headers={'meta_charset':"UTF-8", 'name':"referrer",
                    # 'content':"no-referrer"},
                    # timeout=(5, 7))  # , 'Connection': 'Keep-Alive'
                    if which == 'json':
                        ufile1 = await response.json()
                    else:
                        ufile1 = await response.text()
                    return ufile1
            # print('just passed the ufile1 request')
            except HTTPError as err:
                if err.code == 504:
                    print('504, need to drop it right now')
                    return
                elif err.code == 403:
                    print('403ed oof')
                    time.sleep(5)
                    return
                else:
                    print('unknown http error', err)
                    raise
            except requests.exceptions.ReadTimeout:
                print('read timed out for some site')
                return
            except TimeoutError:
                print('timed out at url: ' + url)
                return
            except Exception as e:
                traceback.print_tb(e.__traceback__)
                print('some other error in urlopen for url' + url, e)
                return

    def sync_read_json_or_text(self, url, which='text'):#THERE IS NO BASE FOR THIS - TOO DIFFERENT FROM THE ASYNC
        session = requests.Session()
        user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/71.0'
        try:
            time.sleep(5)#different than fdascrapers comp_id
            response = session.get(url)
            # ufile1 = ureq.urlopen(ufile0, context=ssl.create_default_context(cafile=certifi.where()))
            # ufile1 = requests.get(url, headers={'meta_charset':"UTF-8", 'name':"referrer",
            # 'content':"no-referrer"},
            # timeout=(5, 7))  # , 'Connection': 'Keep-Alive'
            if which == 'json':
                ufile1 = response.json
            else:
                ufile1 = response.text
            return ufile1
        # print('just passed the ufile1 request')
        except HTTPError as err:
            if err.code == 504:
                print('504, need to drop it right now')
                return
            elif err.code == 403:
                print('403ed oof')
                time.sleep(5)
                return
            else:
                print('unknown http error', err)
                raise
        except requests.exceptions.ReadTimeout:
            print('read timed out for some site')
            return
        except TimeoutError:
            print('timed out at url: ' + url)
            return
        except Exception as e:
            traceback.print_tb(e.__traceback__)
            print('some other error in urlopen for url' + url, e)
            return

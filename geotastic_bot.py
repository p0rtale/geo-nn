import argparse
import pyautogui
import json
import time
import os
from datetime import datetime
from seleniumwire.undetected_chromedriver import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import re
import pickle
from typing import Tuple,NoReturn
from seleniumwire.utils import decode





wait_timeout = 20


def get_coords_from_log(driver) -> Tuple[float, float]:
    """
    Получение координат с логов браузера
    """
    #https://gist.github.com/rengler33/f8b9d3f26a518c08a414f6f86109863c
    lats  = None
    longs = None

    for request in driver.requests:
        if request.url == 'https://maps.googleapis.com/$rpc/google.internal.maps.mapsjs.v1.MapsJsInternalService/GetMetadata':
            data = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity')).decode('utf-8')
          
            arrs = re.findall('\d+\.\d+,\d+\.\d+\]',data)
            # print(data)
            # print(arrs)
            if len(arrs)>0:
                arrs = re.findall('\d+\.\d+',arrs[0])
                lat = float(arrs[0])
                lng = float(arrs[1])
                del driver.requests
                return lat,lng
                

    del driver.requests
    return 0,0

            

def get_driver(with_logs:bool=False) -> webdriver:
    """
    Получение драйвера веб браузера
    """
    chrome_options = Options()

    '''
    # For Network logs
    if with_logs:
        chrome_options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
    '''

    #chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


def prepare_dir()->str:
    """
    Подговотка директории, куда сохранять
    возвращает директорию
    делает имя как сегодняшнюю дату. если такая директория существует,
    то добавляет (i)
    """

    name = datetime.now().strftime('%d-%m-%Y %H:%M:%S')
    files = os.listdir()
    if name in files:
        i = 1
        name_new = name
        while (name_new in files):
            name_new = name + f' ({i})'
            i+=1
        name = name_new
    os.makedirs(name)
    return name
        

        
def set_cookies(driver:webdriver,cookie_name:str) ->NoReturn:
    """
    Установка куки в сессию браузера
    """
    with open(cookie_name,'rb') as f:
        cookies = pickle.load(f)
        for cookie in cookies:
            print(cookie)
            driver.add_cookie(cookie)

    
def get_el(driver,xpath):
    return  WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    xpath
                )
            )
        )
def start_bot(rounds_num:int,cookie_name:str, fetch_location:bool, remove_arrows:bool) ->NoReturn:
    
    driver = get_driver()
    driver.maximize_window()
    time.sleep(4)
    driver.get('https://geotastic.net')
    
    time.sleep(4)
    try:
        driver.find_element(By.XPATH,'/html/body/div[1]/div[5]/div/div/div[3]/button').click()
        
    except Exception as e:
        print(e)

    get_el(driver, '/html/body/div[1]/div[1]/main/div/div/div[5]/div/div[3]/div[1]/button').click()   
    time.sleep(4)
    get_el(driver,'//*[@id="input-236"]').send_keys('kerimovnm@mail.ru')
    time.sleep(4)
    get_el(driver,'//*[@id="input-237"]').send_keys('9EuGzCGPqPr9qeb')
    time.sleep(4)
    get_el(driver,'//*[@id="app"]/div[6]/div/div/div[3]/div/div/div/form/button[1]').click()
    time.sleep(4)
    go_to_play_button_xpath = '/html/body/div[1]/div[1]/main/div/div/div[8]/div[1]/div/div[2]'
    go_to_play_button = WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, 
                    go_to_play_button_xpath
                )
            )
        )
    go_to_play_button.click()

    
    time.sleep(4)
    get_el(driver,'//*[@id="app"]/div[7]/div/div/div/div/div/button').click()
    time.sleep(8)
    get_el(driver,'html/body/div[1]/div[1]/main/div/div/div[2]/div[2]/div/div[2]/div/div[3]/button').click()
    
    '''
    # get, click, ...

    log_entries = driver.get_log("performance")

    for entry in log_entries:
        try:
            obj_serialized: str = entry.get("message")
            obj = json.loads(obj_serialized)
            message = obj.get("message")
            method = message.get("method")
            print(type(message), type(method), message)
            print('--------------------------------------')
        except Exception as e:
            raise e from None
    '''
    save_dir = prepare_dir()

    for game_round in range(1, rounds_num + 1):
        

        # Waiting for "PREPARE YOURSELF" page button
        prepare_button_xpath = '//*[@id="prepare-component"]/div/div[1]/div/span[2]/button'
        # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div/div[1]/div/span[2]/button
        prepare_button = WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH, 
                    prepare_button_xpath
                )
            )
        )
        # Start game round
        prepare_button.click()

        # Waiting for the panorama to load
        street_map_div_xpath = '//*[@id="play-component"]/div[3]/div[2]/div[3]'
        # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div[3]/div[2]/div[3]
        WebDriverWait(driver, wait_timeout).until(
            EC.presence_of_element_located(
                (
                    By.XPATH,
                    street_map_div_xpath
                )
            )
        )
        
        # Removing arrows from the panorama
        if remove_arrows and game_round == 1:
            arrows_xpath = '//*[@id="play-component"]/div[3]/div[2]/div[3]/div/div/div[2]/div[1]/div[10]'
            # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div[3]/div[2]/div[3]/div/div/div[2]/div[1]/div[10]
            arrows = driver.find_element(By.XPATH, arrows_xpath)
            driver.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, arrows)
        
        # Taking screenshots
        driver.save_screenshot(os.path.join(save_dir,f"image{game_round}_{0}.png"))
        for i in range(1, 3):
            w, h = pyautogui.size()
            pyautogui.moveTo(w, h//2)
            pyautogui.dragTo(0, h//2, duration=1)
            driver.save_screenshot(os.path.join(save_dir,f"image{game_round}_{i}.png"))
        time.sleep(1)

        # Opening the map (Toggle Layout button)
        toggle_layout_button_xpath = '//*[@id="play-component"]/div[3]/div[3]/div[3]/button[4]'
        # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div[3]/div[3]/div[3]/button[4]
        driver.find_element(By.XPATH, toggle_layout_button_xpath).click()

        # Click in the center of the map
        pyautogui.click(x=w//2, y=h//2)

        # Waiting for the "FINISH GUESS" button
        finish_guess_button_xpath = '//*[@id="play-component"]/div[3]/div[4]/div[2]/button'
        # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div[3]/div[4]/div[2]/button
        finish_guess_button = WebDriverWait(driver, wait_timeout).until(
            EC.element_to_be_clickable(
                (
                    By.XPATH,
                    finish_guess_button_xpath
                )
            )
        )
        # "Guessing"
        finish_guess_button.click()
        if fetch_location:
            latitude,longitude = get_coords_from_log(driver)
            print(latitude,longitude)

        

            

        # Click on the "CONTINUE" button
        continue_button_xpath = '//*[@id="result-component"]/div[2]/div/div[4]/button'
        # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div[2]/div/div[4]/button
        driver.find_element(By.XPATH, continue_button_xpath).click()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", dest="rounds_num", required=True, type=int)
    parser.add_argument("--fetch-location", dest="fetch_location", action="store_true")
    parser.add_argument("--remove-arrows", dest="remove_arrows", action="store_true")
    args = parser.parse_args()

    start_bot(
        rounds_num=args.rounds_num,
        cookie_name = '',
        fetch_location=args.fetch_location,
        remove_arrows=args.remove_arrows
    )

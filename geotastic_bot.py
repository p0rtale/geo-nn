import argparse
import pyautogui
import json
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


def get_driver(with_logs=False):
    chrome_options = Options()

    '''
    # For Network logs
    if with_logs:
        chrome_options.set_capability(
            "goog:loggingPrefs", {"performance": "ALL", "browser": "ALL"}
        )
    '''

    chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
    driver = webdriver.Chrome(options=chrome_options)

    return driver


def start_bot(rounds_num, fetch_location, remove_arrows):
    driver = get_driver()

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

    for game_round in range(1, rounds_num + 1):
        wait_timeout = 20

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
        driver.save_screenshot(f"image{game_round}_{0}.png")
        for i in range(1, 3):
            w, h = pyautogui.size()
            pyautogui.moveTo(w, h//2)
            pyautogui.dragTo(0, h//2, duration=1)
            driver.save_screenshot(f"image{game_round}_{i}.png")
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
            # Waiting for iFrame with the true location
            iframe_xpath = '//*[@id="wetter-widget"]/iframe'
            # Full XPath: /html/body/div[1]/div[1]/main/div/div/div[3]/div[2]/div[2]/div/div[4]/div/iframe
            iframe = WebDriverWait(driver, wait_timeout).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH, 
                        iframe_xpath
                    )
                )
            )

            driver.switch_to.frame(iframe)
            # Waiting for the true location
            true_location_element_xpath = '//*[@id="__layout"]/div/div/main/div/div[2]/p/strong[2]'
            # Full XPath: /html/body/div/div/div/div/main/div/div[2]/p/strong[2]
            true_location_element = WebDriverWait(driver, wait_timeout).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        true_location_element_xpath
                    )
                )
            )
            true_location = true_location_element.text
            print(f"Round {game_round}: {true_location}")
            driver.switch_to.default_content()

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
        fetch_location=args.fetch_location,
        remove_arrows=args.remove_arrows
    )

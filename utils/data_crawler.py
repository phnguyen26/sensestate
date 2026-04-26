
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException


MAIN_CONTENT_ELEMENT = '.re__main-content'
TITLE_ELEMENT = '.re__pr-title.pr-title'
# ADDRESS_ELEMENT = '.re__pr-short-description'
ADDRESS_ELEMENT = '.re__address-line-1'
SHORT_INFOS_ELEMENT = '.re__pr-short-info-item.js__pr-short-info-item'
DESCRIPTION_ELEMENT = '.re__section-body.re__detail-content'
IMG_ELEMENT = '.re__media-thumb-item'
RESIZE = "/resize/200x200"
class Data:
    def __init__(self, imgs, title, address, price, price_ext, area, area_ext, description, direction, legal, url, type):
        self.imgs = imgs
        self.title = title
        self.address = address
        self.price = price
        self.price_ext = price_ext
        self.area = area
        self.area_ext = area_ext
        self.description = description
        self.direction = direction
        self.legal = legal
        self.url = url
        self.type = type
def data_crawler(url, driver, type):
    driver.switch_to.new_window('tab')
    driver.get(url)
    body = WebDriverWait(driver, 15).until(
    EC.presence_of_element_located(
        (By.CSS_SELECTOR, MAIN_CONTENT_ELEMENT)
        )
    )
    title = driver.find_element(By.CSS_SELECTOR, TITLE_ELEMENT).text
    address = driver.find_element(By.CSS_SELECTOR, ADDRESS_ELEMENT).text    
    infos = driver.find_elements(By.CSS_SELECTOR, SHORT_INFOS_ELEMENT)
    price, price_ext, area, area_ext = None, None, None, None
    for i in range(2):
        info = infos[i]
        info_name = info.find_element(By.CSS_SELECTOR, '.title').text
        info_value = info.find_element(By.CSS_SELECTOR, '.value').text
        info_ext = None
        try:
            info_ext = info.find_element(By.CSS_SELECTOR, '.ext').text
        except NoSuchElementException as e:
            pass
        if info_name == 'Khoảng giá':
            price = info_value
            if info_ext:
                price_ext = '(' + info_ext + ')'
        elif info_name == 'Diện tích':
            area = info_value
            if info_ext:
                area_ext = '(' + info_ext + ')'
    
    description = driver.find_element(By.CSS_SELECTOR, DESCRIPTION_ELEMENT)
    description = driver.execute_script(
        "var temp = arguments[0].cloneNode(true);"
        "temp.querySelectorAll('br').forEach(br => br.replaceWith('\\n'));"
        "return temp.textContent;", 
        description).strip()
    direction, legal = None, None
    try:
        direction = driver.find_element(By.XPATH, "//span[@class = 're__pr-specs-content-item-title' and text() = 'Hướng nhà']/following-sibling::span").text
    except NoSuchElementException as e:
        pass
    try:
        legal = driver.find_element(By.XPATH, "//span[@class = 're__pr-specs-content-item-title' and text() = 'Pháp lý']/following-sibling::span").text
    except NoSuchElementException as e:
        pass
    imgs = []
    img_elements = driver.find_elements(By.CSS_SELECTOR, IMG_ELEMENT)

    for img_element in img_elements:
        try:
            img_url = img_element.find_element(By.CSS_SELECTOR, 'img').get_attribute('data-src')
            if  img_url :
                img_url = img_url.replace("/resize/200x200", "")
                imgs.append(img_url)
        except NoSuchElementException as e:
            pass
    driver.close()
    driver.switch_to.window(driver.window_handles[0])

    return Data(imgs, title, address, price, price_ext, area, area_ext, description, direction, legal, url, type)


if __name__ == '__main__':
    pass









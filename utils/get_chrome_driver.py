import re
import undetected_chromedriver as uc


def get_chrome_driver():
    options = uc.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--start-maximized")
    version_pattern = r"Current browser version is (\d+\.\d+\.\d+\.\d+)"
    try: 
        driver = uc.Chrome(options=options)
    except Exception as e: 
        main_version_string = re.search(version_pattern, str(e)).group(1)
        main_version = int(main_version_string.split(".")[0])
        driver = uc.Chrome(version_main=main_version, options=options)
    return driver

if __name__ == "__main__":
    pass
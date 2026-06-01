from selenium import webdriver
from selenium.webdriver.common.by import By
import time
# começar sessão
driver = webdriver.Chrome()

# navegar para a página
driver.get("https://www.saucedemo.com/")
time.sleep(3)

# procurar elementos para interagir
username = driver.find_element(By.ID, "user-name")
password = driver.find_element(By.NAME, "password")
login_button = driver.find_element(By.ID, "login-button")

#interagir com os elements
username.send_keys("standard_user")
password.send_keys("secret_sauce")
login_button.click()

time.sleep(3)

produtos = driver.find_element(By.CLASS_NAME, "inventory_list")

print(produtos.text)


driver.quit()

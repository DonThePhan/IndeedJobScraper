import os
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium_stealth import stealth
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import random

global total_jobs

# Proxy List (Defined outside the function)
proxy_list = [
    'gate.smartproxy.com:10001:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10002:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10003:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10004:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10005:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10006:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10007:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10008:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10009:sp5hlp83m2:xJ0sy7CwKjex~8d2St',
    'gate.smartproxy.com:10010:sp5hlp83m2:xJ0sy7CwKjex~8d2St'
    # Add more proxies here
]


def get_random_proxy(proxy_list):
    """Choose a random proxy from the proxy list."""
    return random.choice(proxy_list)


def configure_webdriver(proxy=None):
    """Configure the WebDriver with or without a proxy."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    # If a proxy is provided, configure it
    if proxy:
        options.add_argument(f'--proxy-server={proxy}')

    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)

    # Enhance stealth mode
    stealth(driver,
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=True,
            hide_scrollbars=True,  # hides scrollbars for better stealth
            fix_session_storage=True,  # prevent detection of session storage
            )

    return driver


def search_jobs(country, job_position, job_location, date_posted, proxy_list):
    """Search for jobs using a random proxy."""
    raw_proxy = get_random_proxy(proxy_list)  # Choose a random proxy from the list
    parts = raw_proxy.split(":")
    host, port, user, password = parts
    formatted_proxy = f"http://{user}:{password}@{host}:{port}"
    print(formatted_proxy)

    driver = configure_webdriver(formatted_proxy)  # Pass the proxy to the driver
    full_url = f'{country}/jobs?q={"+".join(job_position.split())}&l={job_location}&fromage={date_posted}'
    print(full_url)
    driver.get(full_url)
    global total_jobs
    try:
        job_count_element = driver.find_element(By.CSS_SELECTOR, '#mosaic-jobResults > u')
        job_elements = job_count_element.find_elements(By.XPATH, './*')

        for child in job_elements:
            try:
                # Find the first <span> descendant of each child
                span = child.find_element(By.XPATH, './/span')
                # Get the text of the first <span>
                print(f"Text inside span: {span.text}")
            except NoSuchElementException:
                # Handle the case where no <span> is found inside the child
                print("No span found in this child.")

        # total_jobs = job_count_element.find_element(By.XPATH, './span').text
        # print(f"{total_jobs} found")
    except NoSuchElementException:
        print("No job count found")
        total_jobs = "Unknown"

    driver.save_screenshot('screenshot.png')
    return full_url


def scrape_job_data(driver, country):
    """Scrape job data and return it in a DataFrame."""
    df = pd.DataFrame({'Link': [''], 'Job Title': [''], 'Company': [''],
                       'Employer Active': [''], 'Location': ['']})
    job_count = 0

    while True:
        soup = BeautifulSoup(driver.page_source, 'lxml')

        boxes = soup.find_all('div', class_='job_seen_beacon')

        for i in boxes:
            try:
                link = i.find('a', {'data-jk': True}).get('href')
                link_full = country + link
            except (AttributeError, TypeError):
                try:
                    link = i.find('a', class_=lambda x: x and 'JobTitle' in x).get('href')
                    link_full = country + link
                except (AttributeError, TypeError):
                    link_full = None

            try:
                job_title = i.find('a', class_=lambda x: x and 'JobTitle' in x).text.strip()
            except AttributeError:
                try:
                    job_title = i.find('span', id=lambda x: x and 'jobTitle-' in str(x)).text.strip()
                except AttributeError:
                    job_title = None

            try:
                company = i.find('span', {'data-testid': 'company-name'}).text.strip()
            except AttributeError:
                try:
                    company = i.find('span', class_=lambda x: x and 'company' in str(x).lower()).text.strip()
                except AttributeError:
                    company = None

            try:
                employer_active = i.find('span', class_='date').text.strip()
            except AttributeError:
                try:
                    employer_active = i.find('span', {'data-testid': 'myJobsStateDate'}).text.strip()
                except AttributeError:
                    employer_active = None

            try:
                location_element = i.find('div', {'data-testid': 'text-location'})
                if location_element:
                    try:
                        location = location_element.find('span').text.strip()
                    except AttributeError:
                        location = location_element.text.strip()
                else:
                    raise AttributeError
            except AttributeError:
                try:
                    location_element = i.find('div', class_=lambda x: x and 'location' in str(x).lower())
                    if location_element:
                        try:
                            location = location_element.find('span').text.strip()
                        except AttributeError:
                            location = location_element.text.strip()
                    else:
                        location = ''
                except AttributeError:
                    location = ''

            new_data = pd.DataFrame({'Link': [link_full], 'Job Title': [job_title],
                                     'Company': [company],
                                     'Employer Active': [employer_active],
                                     'Location': [location]})

            df = pd.concat([df, new_data], ignore_index=True)
            job_count += 1

        print(f"Scraped {job_count} of {total_jobs}")

        try:
            next_page = soup.find('a', {'aria-label': 'Next Page'}).get('href')

            next_page = country + next_page
            driver.get(next_page)

        except:
            break

    return df


def clean_data(df):
    """Clean the scraped data."""
    def posted(x):
        try:
            x = x.replace('EmployerActive', '').strip()
            return x
        except AttributeError:
            pass
    df['Employer Active'] = df['Employer Active'].apply(posted)
    return df


def save_csv(df, job_position, job_location):
    """Save the data to a CSV file."""
    def get_user_desktop_path():
        home_dir = os.path.expanduser("~")
        desktop_path = os.path.join(home_dir, "Desktop")
        return desktop_path

    file_path = os.path.join(get_user_desktop_path(), '{}_{}'.format(job_position, job_location))
    csv_file = '{}.csv'.format(file_path)
    df.to_csv(csv_file, index=False)

    return csv_file


def send_email(df, sender_email, receiver_email, job_position, job_location, password):
    """Send the data via email."""
    sender = sender_email
    receiver = receiver_email
    password = password
    msg = MIMEMultipart()
    msg['Subject'] = 'New Jobs from Indeed'
    msg['From'] = sender
    msg['To'] = ','.join(receiver)

    attachment_filename = generate_attachment_filename(job_position, job_location)

    csv_content = df.to_csv(index=False).encode()

    part = MIMEBase('application', 'octet-stream')
    part.set_payload(csv_content)
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
    msg.attach(part)

    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.login(user=sender, password=password)

    s.sendmail(sender, receiver, msg.as_string())

    s.quit()


def send_email_empty(sender, receiver_email, subject, body, password):
    """Send a plain email without an attachment."""
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ','.join(receiver_email)

    # Attach the body as the text/plain part of the email
    msg.attach(MIMEText(body, 'plain'))

    s = smtplib.SMTP_SSL(host='smtp.gmail.com', port=465)
    s.login(user=sender, password=password)

    s.sendmail(sender, receiver_email, msg.as_string())

    s.quit()


def generate_attachment_filename(job_title, job_location):
    """Generate filename for the email attachment."""
    filename = f"{job_title.replace(' ', '_')}_{job_location.replace(' ', '_')}.csv"
    return filename

search_jobs(
            'https://ca.indeed.com',
            'developer',
            'remote',
            20,
    proxy_list
)

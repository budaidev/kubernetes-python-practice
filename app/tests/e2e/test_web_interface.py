import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time


def test_homepage_loads(driver, wait, base_url):
    """Test that the homepage loads successfully"""
    driver.get(base_url)

    # Check if the add book form is present
    form = wait.until(
        EC.presence_of_element_located((By.ID, "bookForm"))
    )
    assert form.is_displayed()
    assert "Book Management" in driver.title


def test_add_book(driver, wait, base_url):
    """Test adding a new book"""
    driver.get(base_url)

    # Fill in the form
    title_input = wait.until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    author_input = driver.find_element(By.NAME, "author")

    title_input.send_keys("Test Book")
    author_input.send_keys("Test Author")

    # Submit the form
    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()

    # Wait for the book to appear in the list
    book_element = wait.until(
        EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'Test Book')]"))
    )

    assert book_element.is_displayed()
    assert "Test Book" in book_element.text


def test_delete_book(driver, wait, base_url):
    """Test deleting a book"""
    # First add a book
    test_add_book(driver, wait, base_url)

    # Find and click delete button for the book
    delete_button = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.delete-btn"))
    )
    delete_button.click()

    # Wait for the book to be removed
    try:
        wait.until(
            EC.invisibility_of_element_located((By.XPATH, "//td[contains(text(), 'Test Book')]"))
        )
        book_removed = True
    except TimeoutException:
        book_removed = False

    assert book_removed, "Book was not removed from the list"


@pytest.mark.parametrize("book_count", [5])
def test_book_list_pagination(driver, wait, base_url, book_count):
    """Test that book list pagination works"""
    driver.get(base_url)

    # Add multiple books
    books_added = []
    for i in range(book_count):
        title_input = wait.until(
            EC.presence_of_element_located((By.NAME, "title"))
        )
        author_input = driver.find_element(By.NAME, "author")

        title = f"Book {i}"
        author = f"Author {i}"

        title_input.send_keys(title)
        author_input.send_keys(author)
        books_added.append((title, author))

        submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
        submit_button.click()

        time.sleep(1)  # Small delay between submissions

    # Check if all books are displayed
    books = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
    )

    # Account for header row
    assert len(books) > book_count, "Not all books were displayed"


@pytest.mark.parametrize("search_term", ["Unique"])
def test_book_search(driver, wait, base_url, search_term):
    """Test the book search functionality"""
    driver.get(base_url)

    # Add a unique book
    title_input = wait.until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    author_input = driver.find_element(By.NAME, "author")

    title = f"{search_term} Book Title"
    author = f"{search_term} Author"

    title_input.send_keys(title)
    author_input.send_keys(author)

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()

    # Find and use search input
    search_input = wait.until(
        EC.presence_of_element_located((By.ID, "searchInput"))
    )
    search_input.send_keys(search_term)

    # Wait for search results
    time.sleep(1)  # Allow time for search to process

    # Verify search results
    search_results = wait.until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tr"))
    )

    # Account for header row
    assert len(search_results) == 2, "Search did not return the expected result"
    assert search_term in search_results[1].text, "Search term not found in results"


@pytest.mark.parametrize("book_data", [
    {"title": "Test Book 1", "author": "Test Author 1"},
    {"title": "Test Book 2", "author": "Test Author 2"},
])
def test_add_multiple_books(driver, wait, base_url, book_data):
    """Test adding multiple books with different data"""
    driver.get(base_url)

    title_input = wait.until(
        EC.presence_of_element_located((By.NAME, "title"))
    )
    author_input = driver.find_element(By.NAME, "author")

    title_input.send_keys(book_data["title"])
    author_input.send_keys(book_data["author"])

    submit_button = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
    submit_button.click()

    book_element = wait.until(
        EC.presence_of_element_located((By.XPATH, f"//td[contains(text(), '{book_data['title']}')]"))
    )

    assert book_element.is_displayed()
    assert book_data["title"] in book_element.text


def test_form_validation(driver, wait, base_url):
    """Test form validation for required fields"""
    driver.get(base_url)

    # Try to submit empty form
    submit_button = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button[type='submit']"))
    )
    submit_button.click()

    # Check for validation message on required fields
    title_input = driver.find_element(By.NAME, "title")
    assert title_input.get_attribute("required"), "Title field should be required"

    author_input = driver.find_element(By.NAME, "author")
    assert author_input.get_attribute("required"), "Author field should be required"
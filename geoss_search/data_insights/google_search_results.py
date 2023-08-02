"""
Module Name: google_search_results

Google Search and Web Scraping Module

This module provides functions to perform web searches, retrieve search results, and extract descriptions from web pages and PDF files.

Module Contents:
    -get_pdf_text(response:requests)->str: Extracts the text content from a PDF.
    - get_description(url: str) -> str: Fetches the description of a web page or the text content of a PDF file from the given URL.
    - search_with_retry(search_term: str, num_results: int, retry_attempts: int = 3) -> List: Perform a web search using the specified search term and return a list of search results.
    - search_with_delay(search_term: str, num_results: int, delay_between_searches: int = 5, retry_attempts: int = 3) -> List: Perform a search with a specified search term 
                                                                                                                                                                        and retrieve search results with a delay between each search.
    - send_multiple_texts_to_google_search(df_searches: pd.DataFrame, number_of_links: int) -> pd.DataFrame: Searches Google for multiple texts and retrieves search results.

Dependencies:
    - typing.List: Typing module for type hinting.
    - time: Standard library module for time-related functions.
    - googlesearch: External library for performing Google searches.
    - bs4.BeautifulSoup: External library for parsing HTML content.
    - requests: External library for making HTTP requests.
    - pandas: External library for data manipulation.
    - io: Standard library module for working with file-like objects.
    - pypdf.PdfReader: External library for reading PDF files.

Note:
    Before using the search functions, make sure to install the 'googlesearch-python' package.

Example Usage:
    description = get_description("https://www.example.com")
    print(description)  # Output: "A website for examples and illustrations."

    search_results = search_with_retry("Python programming", 10, retry_attempts=5)
    if search_results:
        for result in search_results:
            print(result['title'], result['link'])

    search_with_delay("Python tutorials", 5, delay_between_searches=2, retry_attempts=2)

    # Assuming df_searches is a DataFrame with required columns ('id', 'description', 'title')
    result_df = send_multiple_texts_to_google_search(df_searches, 5)
    # The result_df will contain the search results for each text in df_searches.
"""
from typing import List
import time
import io
from googlesearch import search
from bs4 import BeautifulSoup
import requests
import pandas as pd
from pypdf import PdfReader

def get_pdf_text(response:requests)->str:
    """
    Extracts the text content from a PDF (url) file.

    This function takes a requests.Response object containing the content of a PDF file
    and returns the text extracted from the first page of the PDF. If the PDF cannot be
    processed or the content is empty, it returns None.

    Parameters:
        response (requests.Response): The HTTP response object containing the PDF content.

    Returns:
        str or None: The extracted text content from the first page of the PDF, or None
        if the PDF could not be processed or the content is empty.

    Example:
        response = requests.get('https://example.com/sample.pdf')
        text = get_pdf_text(response)
        if text is not None:
            print("PDF Text Content:")
            print(text)
        else:
            print("Failed to extract text from the PDF.")
    """
    try:
        f = io.BytesIO(response.content)
        reader = PdfReader(f)
        if reader is not None:
            contents = reader.pages[0].extract_text()
            return contents
        else:
            return None
    except Exception as exception:
        return None

def get_description(url: str)-> str:
    """
    Fetches the description of a web page or the text content of a PDF file from the given URL.

    Args:
        url (str): The URL of the web page or the PDF file.

    Returns:
        str: The description of the web page (if available) or the text content of the PDF file,
             or "Description not found" if no description is found.

    Raises:
        None.

    Notes:
        This function tries multiple methods to extract the description, prioritizing as follows:
        1. If the URL ends with '.pdf', it will attempt to extract text from the PDF content.
        2. If the web page contains a 'description' meta tag, it will use its content.
        3. If the web page contains an 'og:description' meta tag, it will use its content.
        4. If there are other 'meta' tags with names like 'description', 'Description', or 'DESCRIPTION',
           it will use their content.
        5. It will check for other attributes like 'data-description', 'data-desc', or 'data-info'
           that might contain the description.
        6. It will look for <p> tags with text that resembles the description.
        7. If the description is found within <meta name="description" content="..."> tags within 'noscript' tags.

        If any of the methods succeed, it returns the description; otherwise, it returns "Description not found".
        If an error occurs during the process, it prints an error message and returns None.

    Example:
        description = get_description("https://www.example.com")
        print(description)  # Output: "A website for examples and illustrations."
    """
    try:
        response = requests.get(url,timeout=10)
        # Method 1: Check for the 'url' ends with '.pdf'
        if url.endswith(".pdf"):
            description=get_pdf_text(response)
            if description is not None:
                return description

        soup = BeautifulSoup(response.content, 'html.parser')

        # Method 2: Check for the 'description' meta tag
        description = soup.find('meta', attrs={"name": "description"})
        if description is not None:
            return description.get('content')

        # Method 3: Check for the 'og:description' meta tag
        description = soup.find('meta', property='og:description')
        if description is not None:
            return description.get('content')

        # Method 4: Check for other meta tags that might contain the description
        for tag in soup.find_all('meta'):
            if tag.get('name') in ["description", "Description", "DESCRIPTION"]:
                return tag.get('content')

        # Method 5: Check for other attributes that might contain the description
        possible_attributes = ["data-description", "data-desc", "data-info"]
        for attr in possible_attributes:
            description = soup.find(attrs={attr: True})
            if description is not None:
                return description.get(attr)
        # Method 6: Check for <p> tags with text that might resemble the description
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            text = paragraph.get_text(strip=True)
            if len(text) > 20 and len(text) < 300:  # Assuming the description length falls within this range
                return text
        # Method 7: Check for <meta name="description" content="..."> within noscript tags
        noscript_tags = soup.find_all('noscript')
        for noscript in noscript_tags:
            noscript_soup = BeautifulSoup(str(noscript), 'html.parser')
            description = noscript_soup.find('meta', attrs={"name": "description"})
            if description is not None:
                return description.get('content')

        #Method 8:Check for the 'keywords' meta tag
        description = soup.find('meta', attrs={"name": "keywords"})
        if description is not None:
            return description.get('content')

        #Method 9: Check for <description>
        description = soup.find("description").contents
        if description is not None:
            return str(description[0])

        #Method 10 :Get the title as description
        description = soup.find("title").contents
        if description is not None:
            return str(description[0])

        return "Description not found"

    except Exception as exception:
        print(f"Failed to fetch description for URL {url}: {exception}")
        return None

def search_with_retry(search_term: str, num_results: int, retry_attempts=3)-> List:
    """
    Perform a web search using the specified search term and return a list of search results.

    This function uses the Google search API to perform a web search with the given search_term
    and retrieves the specified number of search_results. If the search encounters an error,
    it will automatically retry a specified number of retry_attempts before giving up.

    Args:
        search_term (str): The search term to be used for the web search.
        num_results (int): The number of search results to be retrieved.
        retry_attempts (int, optional): The number of retry attempts to perform if an error occurs
            during the search. Defaults to 3.

    Returns:
        list: A list of search results. Each result is a dictionary containing information about
        the search result.

    Raises:
        None

    Example:
        >>> search_results = search_with_retry("Python programming", 10, retry_attempts=5)
        >>> if search_results:
        >>>     for result in search_results:
        >>>         print(result['title'], result['link'])

    Note:
        The search function used in this implementation comes from the 'google' library. Make
        sure you have installed the 'google' package before using this function.
    """
    attempts = 0
    while attempts < retry_attempts:
        try:
            search_results = list(search(search_term, num=num_results,start=0,stop=num_results,pause=2,user_agent='text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'))
            return search_results
        except Exception as exception:
            print(f"Error occurred: {exception}")
            print("Retrying in 5 seconds...")
            time.sleep(5)
            attempts += 1
    print("Failed to perform the search after multiple attempts.")
    return None

def search_with_delay(search_term: str, num_results : int, delay_between_searches=5 , retry_attempts=3)-> List:
    """
    Perform a search with a specified search term and retrieve search results with a delay between each search.

    Args:
        search_term (str): The term to search for.
        num_results (int): The number of search results to retrieve.
        delay_between_searches (int, optional): The time (in seconds) to wait between each search. Defaults to 5 seconds.
        retry_attempts (int, optional): The number of retry attempts in case of a failed search. Defaults to 3.

    Returns:
        list: A list of search results, where each item is a list containing the URL and its corresponding description.

    Notes:
        This function relies on the `search_with_retry` function to perform the actual search with retry attempts
        in case of failures. The `get_description` function is used to obtain the description of each search result.

        If the `search_term` is `None`, or if no search results are found, an empty list is returned.

        The function introduces a delay between consecutive searches to prevent overwhelming the search service
        and to avoid potential restrictions due to high query rates.

    Example:
        >>> search_with_delay("Python tutorials", 5, delay_between_searches=2, retry_attempts=2)
        URL: https://www.example.com/python-tutorial-1
        Description: This tutorial covers the basics of Python programming.
        URL: https://www.example.com/python-tutorial-2
        Description: Learn advanced Python concepts in this tutorial.
        URL: https://www.example.com/python-tutorial-3
        Description: Discover Python libraries for data analysis.
        URL: https://www.example.com/python-tutorial-4
        Description: Dive into web development with Python and Flask.
        URL: https://www.example.com/python-tutorial-5
        Description: Explore Python's object-oriented programming features.
        [['https://www.example.com/python-tutorial-1', 'This tutorial covers the basics of Python programming.'],
         ['https://www.example.com/python-tutorial-2', 'Learn advanced Python concepts in this tutorial.'],
         ['https://www.example.com/python-tutorial-3', 'Discover Python libraries for data analysis.'],
         ['https://www.example.com/python-tutorial-4', 'Dive into web development with Python and Flask.'],
         ['https://www.example.com/python-tutorial-5', "Explore Python's object-oriented programming features."]]
    """
    results=[]
    if search_term is not None:
        search_results = search_with_retry(search_term, num_results, retry_attempts)
        if search_results is not None:
            for result in search_results:
                description = get_description(result)
                #print(f"URL: {result}")
                #print(f"Description: {description}")
                results.append([result,description])
                time.sleep(delay_between_searches)
            return results
        else:
            return []
    else:
        return []

def send_multiple_texts_to_google_search(df_searches: pd.DataFrame, number_of_links: int) -> pd.DataFrame:
    """
    Searches Google for multiple texts and retrieves search results.

    This function takes a DataFrame containing text searches and sends each text to Google for search.
    It then retrieves a specified number of search results for each text and stores them in a new DataFrame.

    Parameters:
        df_searches (pd.DataFrame): A DataFrame containing the text searches to be sent to Google.
            It must have at least the following columns:
                - 'id': A unique identifier for each search text.
                - 'description': The description part of the search text (optional).
                - 'title': The title part of the search text (optional).

        number_of_links (int): The number of search results to retrieve for each text.

    Returns:
        pd.DataFrame: A new DataFrame containing the search results for each text.
            The DataFrame has the following columns:
                - 'text': The combined text (title and description) used for the search.
                - 'id': The unique identifier associated with the search text.
                - 'results': A list of URLs representing the search results.

    Example:
        # Assuming df_searches is a DataFrame with required columns ('id', 'description', 'title')
        result_df = send_multiple_texts_to_google_search(df_searches, 5)
        # The result_df will contain the search results for each text in df_searches.
    """
    df_results = pd.DataFrame(columns=["text","id", "results"])
    for ind in df_searches.index:
        id_text=df_searches.loc[ind, "id"]
        if df_searches.loc[ind, "description"] is not None and df_searches.loc[ind, "title"]:
            text=str(df_searches.loc[ind, "title"])+" "+df_searches.loc[ind, "description"]
        elif df_searches.loc[ind, "description"] is not None:
            text=df_searches.loc[ind, "description"]
        elif df_searches.loc[ind, "title"] is not None:
             text=df_searches.loc[ind, "title"]
        else:
            text=None
        results =search_with_delay(text, number_of_links)
        df_results.loc[len(df_results)] = [text,id_text, results]
    return df_results

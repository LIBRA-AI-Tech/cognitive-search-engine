"""
Module Name: google_search_results

Google Search and Web Scraping Module

This module provides functions for performing Google searches and web scraping to retrieve search results and metadata
from web pages.

Functions:
    1. get_description(url: str) -> str:
        Fetches the description metadata of a web page from the given URL.
    
    2. search_with_retry(search_term: str, num_results: int, retry_attempts: int = 3) -> list or None:
        Perform a search using a given search term and retrieve a specified number of search results.
    
    3. search_with_delay(search_term: str, num_results: int, delay_between_searches: int = 5, retry_attempts: int = 3) -> list:
        Perform a series of searches for a given search term and retrieve search results with a delay between each search.
    
    4. send_multiple_texts_to_google_search(df_searches: pd.DataFrame, number_of_links: int) -> pd.DataFrame:
        Perform multiple Google searches for a list of texts and retrieve a specified number of search results for each text.

Notes:
- This module uses the 'googlesearch' library and 'BeautifulSoup' for web scraping.
- The 'get_description' function is used to extract the 'description' metadata from a web page.
- The 'search_with_retry' function performs a Google search with multiple retry attempts to handle potential errors.
- The 'search_with_delay' function performs a series of Google searches with delays between each search.
- The 'send_multiple_texts_to_google_search' function conducts multiple searches based on a DataFrame of search terms.

Please ensure responsible usage of these functions and comply with Google's terms of service to avoid potential restrictions
on search queries.
"""
import time
from typing import List
from googlesearch import search
from bs4 import BeautifulSoup
import requests
import pandas as pd

def get_description(url: str)-> str:
    """ 
    Fetches the description metadata of a web page from the given URL.

    The function makes an HTTP GET request to the provided URL, extracts the page's content, and looks for the
    'description' meta tag in the HTML using BeautifulSoup. If found, it returns the content of the 'description' tag.
    If the 'description' tag is not present, the function tries to get the description using the 'get_open_graph_description'
    function (assuming it is defined elsewhere). If a valid description is found using this method, it is returned.

    If neither method succeeds in finding a description, the function returns the string "Description not found".

    Parameters:
        url (str): The URL of the web page from which to fetch the description.

    Returns:
        str: The description of the web page if found, otherwise "Description not found".
        None: If an error occurs during the process, returns None.
    Raises:
        None.
    Example:
        description = get_description("https://example.com")
        print(description)  # Output: "An example website with useful examples."

        description = get_description("https://nonexistent.com")
        print(description)  # Output: "Description not found"
    """
    try:
        response = requests.get(url,timeout=2)
        soup = BeautifulSoup(response.content, 'html.parser')
        # Method 1: Check for the 'description' meta tag
        description = soup.find('meta', attrs={"name": "description"})
        if description is not None:
            return str(description.get('content'))
        # Method 2: Check for the 'og:description' meta tag
        description = soup.find('meta', property='og:description')
        if description is not None:
            return str(description.get('content'))

        # Method 3: Check for other meta tags that might contain the description
        for tag in soup.find_all('meta'):
            if tag.get('name') in ["description", "Description", "DESCRIPTION"]:
                return str(tag.get('content'))

        # Method 4: Check for other attributes that might contain the description
        possible_attributes = ["data-description", "data-desc", "data-info"]
        for attr in possible_attributes:
            description = soup.find(attrs={attr: True})
            if description is not None:
                return str(description.get(attr))
        # Method 5: Check for <p> tags with text that might resemble the description
        paragraphs = soup.find_all('p')
        for paragraph in paragraphs:
            text = paragraph.get_text(strip=True)
            if len(text) > 20 and len(text) < 300:  # Assuming the description length falls within this range
                return str(text)
        # Method 6: Check for <meta name="description" content="..."> within noscript tags
        noscript_tags = soup.find_all('noscript')
        for noscript in noscript_tags:
            noscript_soup = BeautifulSoup(str(noscript), 'html.parser')
            description = noscript_soup.find('meta', attrs={"name": "description"})
            if description is not None:
                return str(description.get('content'))
        return "Description not found"

    except Exception as exception:
        print(f"Failed to fetch description for URL {url}: {exception}")
        return None

def search_with_retry(search_term: str, num_results: int, retry_attempts=3)-> List:
    """
    Perform a search using a given search term and retrieve a specified number of search results.

    This function uses the 'search' function from the 'search' library to perform the search operation.
    If an error occurs during the search, the function will retry a number of times before giving up.

    Args:
        search_term (str): The search term to look for in the search engine.
        num_results (int): The number of search results to retrieve.
        retry_attempts (int, optional): The number of retry attempts in case of errors during the search.
            Default is 3.

    Returns:
        list or None: A list containing the search results as items. If the search is unsuccessful
        after the specified number of retry attempts, the function returns None.

    Raises:
        None: This function does not raise any custom exceptions. Any exceptions raised during the
        search process will be caught and displayed as error messages.

    Example:
        >>> search_results = search_with_retry("Python programming", 10, retry_attempts=5)
        >>> if search_results:
        ...     print(f"Found {len(search_results)} search results.")
        ...     for result in search_results:
        ...         print(result)
        ... else:
        ...     print("Search failed after multiple attempts.")
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

def search_with_delay(search_term :str, num_results :int, delay_between_searches=5, retry_attempts=3)->List:
    """
    Perform a series of searches for a given search term and retrieve search results with a delay between each search.

    Parameters:
        search_term (str): The term to search for.
        num_results (int): The number of search results to fetch for each search term.
        delay_between_searches (int, optional): The delay (in seconds) between each search request. Default is 10 seconds.
        retry_attempts (int, optional): The number of retry attempts if a search request fails. Default is 3.

    Returns:
        list: A list of search results along with their descriptions, represented as sublists with each sublist containing
              the URL and description as strings. Returns an empty list if the search term is None, no search results are
              found, or if an error occurs during the search.

    Notes:
        - The function uses the `search_with_retry` function to attempt searching the search_term multiple times if needed.
        - For each search result, it obtains the description using the `get_description` function and prints the URL and
          description.
        - The function adds a time delay between each search to prevent overwhelming the search engine or violating any
          rate-limiting policies.
    """
    results=[]
    if search_term is not None:
        search_results = search_with_retry(search_term, num_results, retry_attempts)
        if search_results is not None:
            for result in search_results:
                description = get_description(result)
                results.append([result,description])
                time.sleep(delay_between_searches)
            return results
        else:
            return []
    else:
        return []

def send_multiple_texts_to_google_search(df_searches: pd.DataFrame, number_of_links: int) -> pd.DataFrame:
    """
    Perform multiple Google searches for a list of texts and retrieve a specified number of search results for each text.

    This function takes a pandas DataFrame containing texts to search for and the desired number of search results to
    retrieve for each text. It calls the `search_with_delay` function to conduct Google searches with a delay between
    requests to avoid overwhelming the search engine. The search results for each text are collected, and the final
    results are returned in a new DataFrame.

    Args:
        df_searches (pd.DataFrame): A pandas DataFrame containing a column "id" representing unique identifiers for
                                    each text and a column "description" containing the texts to search for.
        number_of_links (int): The number of search results to retrieve for each text.

    Returns:
        pd.DataFrame: A new pandas DataFrame containing the search results for each text. The DataFrame has two columns:
                      "id" representing the unique identifier for each text and "results" containing the search
                      results, represented as a list of URLs or relevant information retrieved from the search.

    Example:
        df_searches = pd.DataFrame({
            "id": [1, 2, 3],
            "description": [
                "How to bake a chocolate cake",
                "Best places to visit in Paris",
                "Python programming tutorials"
            ]
        })
        number_of_links = 5
        df_results = send_multiple_texts_to_google_search(df_searches, number_of_links)
        print(df_results)
        # Output:
        #    id                                            results
        # 0   1  [https://www.example.com/chocolate-cake-recipe, ...]
        # 1   2  [https://www.example.com/best-places-paris, ...]
        # 2   3  [https://www.example.com/python-tutorial-1, ...]

    Note:
        - Make sure to use this function responsibly and respect Google's terms of service to avoid any potential
          restrictions on search queries.
    """
    df_results = pd.DataFrame(columns=["id", "results"])
    for ind in df_searches.index:
        id_text=str(df_searches.loc[ind, "id"])
        if df_searches.loc[ind, "description"] is not None and df_searches.loc[ind, "title"] is not None:
            text=str(df_searches.loc[ind, "title"])+" "+str(df_searches.loc[ind, "description"])
        elif df_searches.loc[ind, "description"] is not None:
            text=str(df_searches.loc[ind, "description"])
        elif df_searches.loc[ind, "title"] is not None:
            text=str(df_searches.loc[ind, "title"])
        else:
            text=None
        results =search_with_delay(text, number_of_links)
        df_results.loc[len(df_results)] = [id_text, results]
    return df_results

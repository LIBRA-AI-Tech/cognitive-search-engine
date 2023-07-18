"""
Module Name: extracted_types_urls

This module contains functions for processing and analyzing metadata and URLs.It is comparing and extracting metadata and types from URLs.

Functions:
- metadata_score_url(df_url: pd.DataFrame, ind: int) -> Tuple[pd.DataFrame]: 
    Calculates a score for each row in the DataFrame based on the values in the "function" and "description" columns.
- metadata_compare_url(df_url: pd.DataFrame) -> Tuple[pd.DataFrame]:
    Compares metadata in the DataFrame and assigns scores to each row based on specific conditions.
- url_parser_score_url(df_url: pd.DataFrame, ind: int) -> pd.DataFrame:
    Parses the URL at the specified index of the given DataFrame and calculates a score based on various URL components.
- url_parser(df_url: pd.DataFrame) -> pd.DataFrame:
    Parses the URLs in the given DataFrame and calculates scores based on various URL components for each URL.
- fetch_headers(url: str, id_: str, semaphore, responses: List) -> bytes:
    Fetches the headers for a given URL asynchronously using aiohttp.
- get_tasks(given_df: pd.DataFrame, responses: List):
    Asynchronously fetches headers for URLs in a given DataFrame.
- headers_score_url(df_url: pd.DataFrame, ind: int) -> pd.DataFrame:
    Assigns a score to a DataFrame row based on header information.
- get_headers_compare_url(df_url: pd.DataFrame, responses: List) -> pd.DataFrame:
    Retrieves and compares headers for URLs in a DataFrame.
- keep_top_two_url_with_highest_score(df_url: pd.DataFrame) -> Tuple[int, int]:
    Finds and returns the indices of the two highest scores in a DataFrame.
- keep_url_with_highest_score(df_url: pd.DataFrame) -> int:
    Finds and returns the index of the URL with the highest score from the given DataFrame.
- get_df_with_extracted_url_and_type(dict_input: pd.DataFrame) -> pd.DataFrame:
    Extracts URL types from a DataFrame and returns a new DataFrame with additional columns for extracted types.
"""

import asyncio
from urllib.parse import urlparse
from typing import List, Tuple
import aiohttp
from aiolimiter import AsyncLimiter
import pandas as pd


def metadata_score_url(df_url: pd.DataFrame,ind:int)->Tuple[pd.DataFrame]:
    """
    Calculates a score for each row in the DataFrame based on the values in the "function" and "description" columns.

    Args:
        df_url (pd.DataFrame): The DataFrame containing the data to be processed.
        ind (int): The index of the row to be processed.

    Returns:
        Tuple[pd.DataFrame]: The updated DataFrame with the calculated scores.

    Description:
        This function calculates a score for each row in the DataFrame based on the values in the "function" and "description" columns.
        If the "function" value is "download", the score is incremented by 1.
        If any of the strings in the description_list is found in the lowercase "description" value, the score is incremented by 1. 
        The updated DataFrame with the calculated scores is returned.


    """

    # function_value and description_value are converted to lowercase
    function_value=str(df_url.loc[ind,"function"]).lower()
    description_value=str(df_url.loc[ind,"description"]).lower()
    #function compare
    if function_value=="download":
        df_url.loc[ind,"score"]=int(df_url.loc[ind,"score"])+1
    description_list = ["wms","wfs"]
    if description_value is not None:
        description_value=str(description_value).lower()

        # If any of the strings in description_list is found in description_value, score is incremented
        if any(string in description_value for string in description_list):
            df_url.loc[ind,"score"]=int(df_url.loc[ind,"score"])+1

    return df_url


def metadata_compare_url(df_url: pd.DataFrame)->Tuple[pd.DataFrame]:
    """
    Compares metadata in the DataFrame and assigns scores to each row based on specific conditions.

    Args:
        df_url (pd.DataFrame): The DataFrame containing the metadata information.

    Returns:
        Tuple[pd.DataFrame]: The DataFrame with updated scores for each row.

    Description:
        This function compares the metadata in the DataFrame and assigns scores to each row based on specific conditions.
        It initializes the 'score' column in the DataFrame to zero.
        Then, it iterates over each row in the DataFrame and calls the metadata_score_url function to calculate the score for that row.
        Finally, the DataFrame with the updated scores is returned.

    """

    # Initializing the 'score' column in the DataFrame to zero
    df_url['score']=0

    # Iterating over each row in the DataFrame and calling metadata_score_url function
    for ind in df_url.index:
        df_url=metadata_score_url(df_url,ind)
    return df_url


def url_parser_score_url(df_url:pd.DataFrame,ind:int)->pd.DataFrame:
    """
    Parses the URL at the specified index of the given DataFrame and calculates a score based on various URL components.
    
    Args:
        df_url (pd.DataFrame): The DataFrame containing the URLs.
        ind (int): The index of the URL to be processed.
        
    Returns:
        pd.DataFrame: The updated DataFrame with the score column modified based on the URL components.

    Description:
        This method extracts the scheme, port, and path from the URL using the `urlparse` function from the `urllib.parse` module.
        It then evaluates the scheme and port to assign a score to the URL.
        If the scheme is "https" or the port is "443",the score is incremented by 3.
        If the scheme is "http" or the port is "80", the score is incremented by 2.
        If the scheme is "ftp" or the port is "21", the score is incremented by 1. 
        Additionally, if the path ends withspecific file extensions or contains certain path components, the score is further incremented.

    """
    result=urlparse(df_url.loc[ind,"url"])
    scheme=str(result.scheme).lower()
    port=str(result.port).lower()
    path=str(result.path).lower()
    path_ends_with_list=['.zip','.csv','.xml']
    path_list=['wfs','wms']

    if scheme is not None or port is not None:
        if scheme=="https" or port=="443":
            df_url.loc[ind,"score"]=int(df_url.loc[ind,"score"])+3
        elif scheme=="http" or port=="80":
            df_url.loc[ind,"score"]=int(df_url.loc[ind,"score"])+2
        elif scheme=="ftp" or port=="21":
            df_url.loc[ind,"score"][ind]=int(df_url.loc[ind,"score"])+1

    if path is not None:
        if any(path.endswith(string) for string in path_ends_with_list):
            df_url.loc[ind,"score"]=int(df_url.loc[ind,"score"])+1
        if any(string in path for string in path_list):
            df_url[ind,"score"]=int(df_url.loc[ind,"score"])+1

        #netloc=result.netloc
        #params=result.params
        #hostname=result.hostname
        #query=result.query
        #fragment=result.fragment
    return df_url

def url_parser(df_url:pd.DataFrame)->pd.DataFrame:
    """
    Parses the URLs in the given DataFrame and calculates scores based on various URL components for each URL.

    Args:
        df_url (pd.DataFrame): The DataFrame containing the URLs.

    Returns:
        pd.DataFrame: The updated DataFrame with the score column modified based on the URL components of each URL.

    Description:
        This method iterates over each index in the DataFrame and calls the `url_parser_score_url` method to parse 
        and score the URL at that index. 
        The `url_parser_score_url` method modifies the score column of the DataFrame based on the URL components. 
        After processing all URLs, the updated DataFrame is returned.

    """
    for ind in df_url.index:
        df_url=url_parser_score_url(df_url,ind)
    return df_url

async def fetch_headers(url: str, id_: str, semaphore,responses:List) -> bytes:
    """
    Fetches the headers for a given URL asynchronously using aiohttp.

    Args:
        url (str): The URL to fetch the headers from.
        id_ (str): The ID associated with the URL.
        semaphore: A semaphore object used for concurrency control.
        responses:list with responses
    Returns:
        bytes: The fetched headers as bytes.

    Raises:
        asyncio.exceptions.TimeoutError: If the request times out.
        Exception: If any other exception occurs during the request.

    Note:
        This function uses aiohttp and requires an event loop to run.

    Example:
        semaphore = asyncio.Semaphore(5)
        headers = await fetch_headers("https://example.com", "example_id", semaphore)
    """
    limiter = AsyncLimiter(20, 1) # 20 Requests / sec
    async with aiohttp.ClientSession() as session:
        await semaphore.acquire()
        async with limiter:
            try:
                async with session.get(url, allow_redirects=True, timeout=5) as resp:
                    if resp.status == 200:
                        response = (id_, resp.status, resp.headers['Content-Type'])
                    else:
                        response = (id_, resp.status, None)
            except asyncio.TimeoutError:
                response=(id_, None, None)
            except Exception:
                response = (id_, 0, None)
            responses.append(response)
            semaphore.release()

async def get_tasks(given_df: pd.DataFrame,responses: List):
    """
    Asynchronously fetches headers for URLs in a given DataFrame.

    Args:
        given_df (pd.DataFrame): The DataFrame containing the URLs.

    Returns:
        None

    Raises:
        Any exceptions raised by `fetch_headers()`.

    Example:
        given_df = pd.DataFrame({'url': ['https://example1.com', 'https://example2.com']})
        await get_tasks(given_df)

    Notes:
        - This function fetches headers for the URLs in the given DataFrame using asynchronous tasks.
        - It uses an asyncio.Semaphore to limit the number of concurrent tasks to 100.
        - The function awaits the completion of all tasks using `asyncio.gather()`.
        - Any exceptions raised by `fetch_headers()` are propagated to the caller.

    """
    semaphore = asyncio.Semaphore(value=100)
    tasks = [fetch_headers(r['url'], index, semaphore,responses) for index, r in given_df.iterrows()]
    await asyncio.gather(*tasks)

def headers_score_url(df_url:pd.DataFrame,ind:int)->pd.DataFrame:
    """
    Assigns a score to a DataFrame row based on header information.

    Args:
        df_url (pd.DataFrame): The DataFrame containing URL information.
        ind (int): The index of the row to be processed.

    Returns:
        pd.DataFrame: The updated DataFrame.

    Description:
        This method calculates a score for the given DataFrame row based on the extracted header information.
        If the status of the URL is not 0 and is less than 400, and the header contains certain string values,
        the score is increased by 10.
        The updated DataFrame is returned.

    Example:
        df = headers_score_url(df_url, 0)
    """
    string_list = ['wfs','wms','zip','xml','csv']
    header=str(df_url.loc[ind,'extracted_types']).lower()
    if df_url.loc[ind,'status']!=0 and df_url.loc[ind,'status']<400 and header is not None:
        if any(string in header for string in string_list):
            df_url.loc[ind,"score"]=int(df_url.loc[ind,"score"])+10
    return df_url

def get_headers_compare_url(df_url: pd.DataFrame,responses: List)->pd.DataFrame:
    """
    Retrieves and compares headers for URLs in a DataFrame.

    Args:
        df_url (pd.DataFrame): The DataFrame containing URL information.
        responses (List): List to store the responses.

    Returns:
        pd.DataFrame: The updated DataFrame.

    Description:
        This method retrieves and compares headers for each URL in the given DataFrame.
        It utilizes asynchronous tasks to fetch headers for the URLs.
        The headers and status codes are stored in the responses list.
        After retrieving the headers, it updates the corresponding rows in the DataFrame with the header information.
        It then calls the `headers_score_url()` method to assign scores based on the headers.
        The updated DataFrame is returned.

    Example:
        df = get_headers_compare_url(df_url, responses)
    """
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_tasks(df_url,responses))
    responses_df=pd.DataFrame(responses,columns=["id_ind","status","header"])
    #keep only what we need from headers
    for ind in responses_df.index:
        id_ind=int(responses_df.loc[ind,"id_ind"])
        if responses_df.loc[ind,"header"] is not None:
            if ";" in  str(responses_df.loc[ind,"header"]):
                header=str(responses_df.loc[ind,"header"]).split(";")
                df_url.loc[id_ind,"extracted_types"]=header[0]
                if "\/" in header[0]:
                    header=str(header[0]).split("\/")
                    df_url.loc[id_ind,"extracted_types"]=header[-1]
            else:
                df_url.loc[id_ind,"extracted_types"]=responses_df.loc[ind,"header"]
        else:
            df_url.loc[id_ind,"extracted_types"]=responses_df.loc[ind,"header"]
        df_url.loc[id_ind,"status"]=responses_df.loc[ind,"status"]
    #scoring
    for ind in df_url.index:
        df_url=headers_score_url(df_url,ind)
    return df_url
def keep_top_two__url_with_highest_score(df_url: pd.DataFrame)->Tuple[int,int]:
    """
    Finds and returns the indices of the two highest scores in a DataFrame.

    Args:
        df_url (pd.DataFrame): A pandas DataFrame containing a 'score' column.

    Returns:
        Tuple[int, int]: A tuple containing the indices of the two highest scores in the DataFrame.

    Raises:
        None.

    Description:
        This method iterates over the DataFrame rows and identifies the two highest scores along with their respective indices.
        It initializes variables to track the highest and second highest scores and their corresponding indices.
        The method compares the score of each row with the highest score found so far.
        If a higher score is found, the second highest score and its index are updated,
        and the highest score and its index are updated accordingly.
        Finally, the method returns a tuple containing the indices of the two highest scores.

    Example:
        >>> df = pd.DataFrame({'score': [3, 5, 2, 7, 1]})
        >>> keep_top_two_score(df)
        (3, 1)
    """
    max_score1=-1
    max_ind1=-1
    max_score2=-1
    max_ind2=-1
    for ind in df_url.index:
        if int(df_url.loc[ind,"score"])>max_score1:
            max_score2=max_score1
            max_ind2=max_ind1
            max_score1=int(df_url.loc[ind,"score"])
            max_ind1=ind
        elif int(df_url.loc[ind,"score"])>max_score2:
            max_score2=int(df_url.loc[ind,"score"])
            max_ind2=ind
    return max_ind1,max_ind2

def keep_url_with_highest_score(df_url: pd.DataFrame)-> int:
    """
    Finds and returns the index of the URL with the highest score from the given DataFrame.

    Args:
        df_url (pd.DataFrame): A DataFrame containing URL information and their scores.

    Returns:
        int: The index of the URL with the highest score.

    Description:
        This method iterates through the rows of the provided DataFrame to identify the URL with the highest score.
        The score is expected to be a numerical value associated with each URL.
        The method compares each score with the current maximum score and updates it if a higher score is found.
        Finally, it returns the index of the URL with the highest score.

    Raises:
        None

    Example:
        >>> df = pd.DataFrame({'url': ['www.example.com', 'www.openai.com', 'www.python.org'],
        ...                    'score': [8, 9, 6]})
        >>> keep_url_with_highest_score(df)
        1
    """
    max_score=-1
    max_ind=-1
    for ind in df_url.index:
        if int(df_url.loc[ind,"score"])>max_score:
            max_score=int(df_url.loc[ind,"score"])
            max_ind=ind
    return max_ind
"""
    Extracts URL types from a DataFrame and returns a new DataFrame with additional columns for extracted types.
    
    Args:
        df_url (pd.DataFrame): The input DataFrame containing URLs.
        columns=['accessType', 'protocol', 'function', 'name','description', 'url','id']
        
    Returns:
        pd.DataFrame: A new DataFrame with additional columns for extracted URL types.
        columns: ['accessType', 'protocol', 'function', 'name', 'description', 'url', 'id', 'status', 'header', 'extracted_types']

    """
def get_df_with_extracted_url_and_type(dict_input: pd.DataFrame)->pd.DataFrame:
    """
    Extracts URLs and their corresponding types from a dictionary input and returns a DataFrame with the extracted data.

    Args:
        dict_input (pd.DataFrame): A dictionary containing id as keys  and their URLs and metadata as values.

    Returns:
        pd.DataFrame: A DataFrame containing the extracted URLs, IDs, and extracted types.(columns=[id,url,extracted_types])
        
    Description:
        This method takes a dictionary `dict_input` containing id as keys  and their URLs and metadata as values. 
        It processes each URL in the dictionary to extract the URL and its type.
        The processing involves comparing metadata, parsing the URL, and comparing headers to determine the most relevant URL 
        and its extracted type.
        The method creates a new DataFrame `df_result` to store the extracted URL, ID, and extracted types for each id in the input dictionary.

    Raises:
        None

    Example:
        dict_input = {
            "id1": [{
                "url": "https://example.com",
                "meta_data": "some data",
                ...
                "function":"some data",
                "description":"some data",
            },
            {
                "url": "https://example2.com",
                "meta_data": "some data",
                ...
                "function":"some data",
                "description":"some data",
            }],
            "id2": [{
                "url": "https://example.net",
                "data": "some other data"
            }]
        }
        df_result = get_df_with_extracted_url_and_type(dict_input)
    """
    responses=[]
    df_result=pd.DataFrame(columns=["id","url","extracted_types"])

    for key in dict_input.keys():
        df_url_for_one_id= pd.DataFrame.from_dict(dict_input[key])

        df_url_for_one_id=metadata_compare_url(df_url_for_one_id)

        df_url_for_one_id=url_parser(df_url_for_one_id)
        if len(df_url_for_one_id)>2:
            #keep best 2 urls if >2
            max_ind1,max_ind2=keep_top_two__url_with_highest_score(df_url_for_one_id)
            new_row=[{'url':df_url_for_one_id["url"][max_ind1],'score':df_url_for_one_id["score"][max_ind1]},{'url':df_url_for_one_id["url"][max_ind2],'score':df_url_for_one_id["score"][max_ind2]}]
            df_url_for_one_id=pd.DataFrame.from_dict(new_row)

        df_url_for_one_id["extracted_types"]=""
        df_url_for_one_id["status"]=""
        df_url_for_one_id=get_headers_compare_url(df_url_for_one_id,responses)
        #choose url with best score
        max_ind=keep_url_with_highest_score(df_url_for_one_id)
        new_row={'id':key,'url':df_url_for_one_id["url"][max_ind],'extracted_types':df_url_for_one_id["extracted_types"][max_ind]}
        df_result = df_result.append(new_row, ignore_index=True)
    return df_result

"""
Module Name: data insights
This module provides functions for comparing and extracting metadata and types from URLs.

Functions:
- metadata_compare_one_url(given_id, df_url, df_hold, extracted_types): Compares metadata of a given URL with predefined string patterns.
- metadata_compare_url(df_url): Compares metadata for URLs in a given DataFrame.
- url_parser_one_url(given_id, df2, df_hold): Parses URLs in the given DataFrame and extracts specific types based on predefined criteria.
- url_parser(df_hold): Parses URLs in the given DataFrame and returns a new DataFrame with parsed information.
- fetch_headers(url, id_, semaphore): Fetches the headers for a given URL asynchronously using aiohttp.
- get_tasks(given_df): Asynchronously fetches headers for URLs in a given DataFrame.
- headers_compare_one_url(given_id, df2, df_hold): Compares headers in a DataFrame with a given list of strings and extracts matching types.
- get_headers_compare_url(df_hold2): Retrieves and compares headers for URLs in a given DataFrame.
- get_df_with_extracted_url_and_type(df_url): Extracts URL types from a DataFrame and returns a new DataFrame with additional columns for extracted types.
"""

import asyncio
from urllib.parse import urlparse
import aiohttp
from aiolimiter import AsyncLimiter
import pandas as pd

responses=[]
limiter = AsyncLimiter(20, 1) # 20 Requests / sec
def metadata_compare_one_url(given_id: str,df_url: pd.DataFrame,df_hold:pd.DataFrame,extracted_types)->tuple[str,pd.DataFrame,list]:
    """
    Compares metadata of a given URL with predefined string patterns.

    Args:
        given_id (str): The ID of the URL to compare its metadata.
        df_url (pd.DataFrame): DataFrame containing the URLs and their metadata.
        df_hold (pd.DataFrame): DataFrame to store the metadata of all urls with the same id.
        extracted_types: A list to store the extracted types of the matched metadata.

    Returns:
        tuple[str, pd.DataFrame]: A tuple containing the given_id, updated df_hold, and the list extracted_types.

    Description:
        The function compares the metadata of a given URL with predefined string patterns. It searches for matching patterns
        in the 'function' and 'description' columns of the df_url DataFrame. If a match is found, the corresponding row is
        added to the df_hold DataFrame, and the extracted type is appended to the extracted_types list. If no match is found,
        the entire row is added to the df_hold DataFrame with an empty string appended to the extracted_types list.

    Example:
        given_id = 'abc123'
        df_url = pd.DataFrame(...)
        df_hold = pd.DataFrame(...)
        extracted_types = []

        result = metadata_compare_one_url(given_id, df_url, df_hold, extracted_types)

        # The function updates df_hold and extracted_types with the matched metadata
        print(result)
        # Output: ('abc123', updated_df_hold, updated_extracted_types)
    """

    df2=df_url.loc[df_url["id"]==given_id]
    df2=df2.reset_index(drop=True)
    string_list = ["download","view","map","wms","wfs"]
    for ind in df2.index:
        flag=True
        target_string1 = df2['function'][ind]
        target_string2 = df2['description'][ind]
        if target_string1 is not None:
            if any(string in target_string1 for string in string_list):
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                if extracted_types:
                    extracted_types.append(target_string1)
                else:
                    extracted_types=[target_string1]
                flag=False
        if target_string2 is not None and flag:
            if any(string in target_string2 for string in string_list):
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                if extracted_types:
                    extracted_types.append(target_string2)
                else:
                    extracted_types=[target_string2]
                flag=False

        if flag:
            df_hold = pd.concat([df_hold, df2],ignore_index = True)
            if extracted_types:
                extracted_types.append("")
            else:
                extracted_types=[""]
    return given_id,df_hold,extracted_types

def metadata_compare_url(df_url: pd.DataFrame)->tuple[pd.DataFrame,list]:
    """
    Compares metadata for URLs in a given DataFrame.

    Args:
        df_url (pd.DataFrame): DataFrame containing URL metadata.

    Returns:
        pd.DataFrame: DataFrame containing compared metadata.

    This function takes a DataFrame of URL metadata and compares the metadata for each URL.
    It iterates over the DataFrame, extracting metadata for each unique URL using the
    `metadata_compare_one_url` function. The extracted metadata is then stored in a new
    DataFrame along with the corresponding URL information.
    
    The function returns the DataFrame containing the compared metadata as well as a list
    of extracted types.

    """

    prev_id=""
    df_hold=pd.DataFrame(columns=["accessType","protocol","function","name","description","url","id"])
    extracted_types=[]
    for ind in df_url.index:
        given_id=df_url["id"][ind]
        if given_id!=prev_id:
            prev_id,df_hold,extracted_types=metadata_compare_one_url(given_id,df_url,df_hold,extracted_types)
    return df_hold,extracted_types

def url_parser_one_url(given_id:str,df2:pd.DataFrame,df_hold:pd.DataFrame)->tuple[str,pd.DataFrame]:
    """
    Parses URLs in the given DataFrame and extracts specific types  based on predefined criteria and updates the 'df_hold' DataFrame accordingly.

    Args:
        given_id (str): The given ID associated with the URLs.
        df2 (pd.DataFrame): The DataFrame containing the URLs to be parsed.
        df_hold (pd.DataFrame): The DataFrame to hold the extracted URLs and types.

    Returns:
        tuple[str, pd.DataFrame]: A tuple containing the given ID and the updated DataFrame 'df_hold'.

    Raises:
        None

    """
    string_list = ['view','map','wfs','wms','zip','csv','xml']
    for ind in df2.index:
        flag=True
        result=urlparse(df2["url"][ind])
        #scheme=result.scheme
        netloc=result.netloc
        path=result.path
        #params=result.params
        #hostname=result.hostname
        query=result.query
        #fragment=result.fragment
        target_string1=df2["url"][ind]
        target_string2=str(path)
        target_string3=str(query)
        target_string4=str(netloc)
        if target_string1 is not None:
            if any(string in target_string1 for string in string_list):
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                df_hold['extracted_types'][ind]=target_string1
                flag=False
                return given_id,df_hold

        if target_string2 is not None:
            if any(string in target_string2 for string in string_list):
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                df_hold['extracted_types'][ind]=target_string1
                flag=False
                return given_id,df_hold

        if target_string3 is not None:
            if any(string in target_string3 for string in string_list):
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                df_hold['extracted_types'][ind]=target_string1
                flag=False
                return given_id,df_hold

        if target_string4 is not None:
            if any(string in target_string4 for string in string_list):
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                df_hold['extracted_types'][ind]=target_string1
                flag=False
                return given_id,df_hold
        if flag:
            df_hold['extracted_types'][ind]=""

    df_hold = pd.concat([df_hold, df2],ignore_index = True)
    return given_id,df_hold

def url_parser(df_hold:pd.DataFrame)->pd.DataFrame:
    """
    Parses URLs in the given DataFrame and returns a new DataFrame with parsed information.

    Args:
        df_hold (pd.DataFrame): The input DataFrame containing URL information.

    Returns:
        pd.DataFrame: A new DataFrame with parsed URL information, including columns for access type, protocol, function, name, description, URL, ID, and extracted types.

    Example:
        df = pd.DataFrame(...)
        parsed_df = url_parser(df)
    """
    prev_id=""
    df_hold2=pd.DataFrame(columns=["accessType","protocol","function","name","description","url","id","extracted_types"])
    for ind in df_hold.index:
        given_id=df_hold["id"][ind]
        df2=df_hold.loc[df_hold["id"]==given_id]
        df2=df2.reset_index(drop=True)

        if given_id!=prev_id:
            prev_id,df_hold2=url_parser_one_url(given_id,df2,df_hold2)

    return df_hold2

async def fetch_headers(url: str, id_: str, semaphore) -> bytes:
    """
    Fetches the headers for a given URL asynchronously using aiohttp.

    Args:
        url (str): The URL to fetch the headers from.
        id_ (str): The ID associated with the URL.
S        semaphore: A semaphore object used for concurrency control.

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

    async with aiohttp.ClientSession() as session:
        await semaphore.acquire()
        async with limiter:
            try:
                async with session.get(url, allow_redirects=True, timeout=5) as resp:
                    if resp.status == 200:
                        response = (id_, resp.status, resp.headers['Content-Type'])
                    else:
                        response = (id_, resp.status, None)
            except asyncio.exceptions.TimeoutError:
                response=(id_, None, None)
            except Exception:
                response = (id_, 0, None)
            responses.append(response)
            semaphore.release()

async def get_tasks(given_df: pd.DataFrame):
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
    tasks = [fetch_headers(r['url'], index, semaphore) for index, r in given_df.iterrows()]
    await asyncio.gather(*tasks)

def headers_compare_one_url(given_id:str,df2:pd.DataFrame,df_hold:pd.DataFrame)->tuple[str,pd.DataFrame]:
    """
    Compares headers in a DataFrame with a given list of strings and extracts matching types.

    Args:
        given_id (str): The given ID.(identifier for the URL)
        df2 (pd.DataFrame): The DataFrame containing headers and statuses.
        df_hold (pd.DataFrame): The DataFrame to hold extracted data.

    Returns:
        tuple[str, pd.DataFrame]: A tuple containing the given ID and the updated DataFrame.

    Note:
        The function iterates over the DataFrame `df2` and checks the status and header values.
        If the status is not 0 and is less than 400, and the header contains any of the predefined strings,
        the corresponding extracted type is assigned to the 'extracted_types' column in `df2`.
        The rows with extracted types are then appended to `df_hold`.
        Finally, the function returns a tuple with the given ID and the updated `df_hold` DataFrame.

    """
    string_list = ['view','map','wfs','wms','zip','xml','csv']
    for ind in df2.index:
        target_string=str(df2['header'][ind]).lower()
        if df2['status'][ind]!=0 and df2['status'][ind]<400 and target_string is not None:
            if any(string in target_string for string in string_list):
                df2['extracted_types'][ind]=target_string
                df_hold = pd.concat([df_hold, df2.iloc[[ind]]],ignore_index = True)
                return given_id,df_hold

    df_hold = pd.concat([df_hold, df2],ignore_index = True)
    return given_id,df_hold

def get_headers_compare_url(df_hold2:pd.DataFrame)->pd.DataFrame:
    """
    Retrieves and compares headers for URLs in a given DataFrame.

    Args:
        df_hold2 (pd.DataFrame): The DataFrame containing the URLs.

    Returns:
        pd.DataFrame: A DataFrame containing the results of the header comparison.

    Raises:
        Any exceptions raised during the execution of the function.

    Description:
        This function retrieves the headers for each URL in the provided DataFrame, compares them, 
        and returns a new DataFrame with the results of the comparison. 
        The DataFrame must have a column named 'id' which serves as a unique identifier for each URL. 
        The function uses asynchronous execution to improve performance.

    Example:
        >>> df = pd.DataFrame({'id': [1, 2, 3], 'url': ['https://example1.com', 'https://example2.com', 'https://example3.com']})
        >>> result = get_headers_compare_url(df)
        >>> print(result)
                id_ind  accessType  protocol   function  ...  header  extracted_types
        0  1       GET      HTTPS  text/html  ...   OK      [text/html]
        1  2       GET      HTTPS  text/html  ...   OK      [text/html]
        2  3       GET      HTTPS  text/html  ...   OK      [text/html]

    """
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(get_tasks(df_hold2))
    responses_df=pd.DataFrame(responses,columns=["id_ind","status","header"])
    df_hold2.reset_index(inplace=True,drop=True)
    index_name=df_hold2.index.name
    dataframe3=df_hold2.join(responses_df.set_index("id_ind"),on=index_name,rsuffix=["ulr","id_ind","status","header"])
    prev_id=""
    df_hold3=pd.DataFrame(columns=["id_ind","accessType","protocol","function","name","description","url","id","status","header","extracted_types"])
    for ind in dataframe3.index:
        given_id=dataframe3["id"][ind]
        df2=dataframe3.loc[dataframe3["id"]==given_id]
        df2=df2.reset_index(drop=True)
        if given_id!=prev_id:
            prev_id,df_hold3=headers_compare_one_url(given_id,df2,df_hold3)
    df_hold3=df_hold3.drop(["id_ind"], axis=1)
    return df_hold3

def get_df_with_extracted_url_and_type(df_url:pd.DataFrame):
    """
    Extracts URL types from a DataFrame and returns a new DataFrame with additional columns for extracted types.
    
    Args:
        df_url (pd.DataFrame): The input DataFrame containing URLs.
        columns=['accessType', 'protocol', 'function', 'name','description', 'url','id']
        
    Returns:
        pd.DataFrame: A new DataFrame with additional columns for extracted URL types.
        columns: ['accessType', 'protocol', 'function', 'name', 'description', 'url', 'id', 'status', 'header', 'extracted_types']

    """
    df_hold,extracted_types=metadata_compare_url(df_url)
    df_url["extracted_types"]=extracted_types

    df_hold2=url_parser(df_hold)

    df_hold3=get_headers_compare_url(df_hold2)
    return df_hold3

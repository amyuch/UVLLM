import json, os, re
from utils import Logger

jsonform = {
    "module name" : "",
        "analysis" : "",
    "correct code" : [('wrong code1', 'correct code1'),('wrong code2', 'correct code2')]
}

import openai
from openai import OpenAI
import logging

os.environ["OPENAI_API_BASE"] = "https://api.openai.com/v1"

# Retrieve API key from environment variable
API_KEY = os.getenv('OPENAI_API_KEY')
if not API_KEY:
    raise ValueError("Environment variable 'OPENAI_API_KEY' is not set.")

# Initialize OpenAI client
openai.api_key = API_KEY

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"), base_url=os.environ.get("OPENAI_API_BASE"))

def get_completion(prompt, model="gpt-4.1-nano", temperature=0.2):
    res = ''
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system",
                 "content": "As a professional IC design engineer."},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=4096,
        )
        logging.info(response)
        res = response.choices[0].message.content
        prompt_tokens_num = response.usage.prompt_tokens
        output_tokens_num = response.usage.completion_tokens
        return res, prompt_tokens_num, output_tokens_num
    except openai.APIConnectionError as e:
        logging.error(f'The server could not be reached, cause:{e.__cause__}')
    except openai.RateLimitError as e:
        logging.error('A 429 status code was received; we should back off a bit.')
    except openai.APIStatusError as e:
        logging.error(
            f'Another non-200-range status code was received, status_code: {e.status_code}, error response: {e.response}')
    except Exception as e:
        logging.error(
            f'Another error response: {e}')
    return res, 0, 0
def api_gpt_mismatch(spec, file_path, snip, badfix:None, logger):
    with open(file_path, 'r', encoding='utf-8') as sfile:  # read-only
        content = sfile.read()

    with open(spec, 'r', encoding='utf-8') as spfile:  # read-only
        specfile = spfile.read()

    prompt = "You are an expert in RTL design and debugging. Here is a error design: \
                      Design description is {}, \n relevant source code is {}, \nmismatch signals are {}.\
                      Try to fix the one that you think is most likely to go wrong. \
                      \nPlease offer merely the fix strictly in the json form of {}, ALL pairs in one line, NO OTHER WORDS IS EXPECTED.\
                       Remember: the port definition may be wrong!".format(specfile, content, snip, jsonform)

    response = get_completion(prompt, "gpt-4-turbo", 0.9)
    logger.info(response[0])
    data = eval(response[0])

    newsrc = content
    for everyOne in data["correct code"]:
        newsrc = replace_with_regex(everyOne[0], everyOne[1], newsrc)


    return  newsrc, data["correct code"]

def api_gpt_suspicious(spec, file_path, snip, badfix:None, logger):
    with open(file_path, 'r', encoding='utf-8') as sfile:  # read-only
        content = sfile.read()

    with open(spec, 'r', encoding='utf-8') as spfile:  # read-only
        specfile = spfile.read()

    prompt = "You are an expert in RTL design and debugging. Here is a error design: \
                      Design description is {}, \n relevant source code is {}, \nand suspicious error code are {}.\
                      Some of the suspicious are right. Try to fix the one that you think is most likely to go wrong. \
                      \nPlease offer merely the fix strictly in the json form of {}, ALL pairs in one line, NO OTHER WORDS IS EXPECTED.\
                       Remember: the port definition may be wrong!".format(specfile, content, snip, jsonform)

    response = get_completion(prompt, "gpt-4-turbo", 0.9)
    logger.info(response[0])
    data = eval(response[0])

    newsrc = content
    for everyOne in data["correct code"]:
        newsrc = replace_with_regex(everyOne[0], everyOne[1], newsrc)

    return  newsrc, data["correct code"]

def api_syntax(file_path, snip, badfix:None, logger):

    max_try = 5
    try_api = 0
    while try_api<max_try:
        try:
            with open(file_path, 'r', encoding='utf-8') as sfile:  # read-only
                content = sfile.read()

            prompt = "You are an expert in RTL design and debugging. Here is a error design: \
                            Relevant source code is {}, \nThe compile report is {}. \
                            \nPlease offer merely the fix strictly in the json form of {}, ALL pairs in one line, NO OTHER WORDS IS EXPECTED.\
                            Remember: the port definition may be wrong!".format(content, snip, jsonform)

            response = get_completion(prompt, "gpt-4-turbo", 0.7)

            logger.info(response[0])
            data = eval(response[0])
            newsrc = content
            for everyOne in data["correct code"]:
                newsrc = replace_with_regex(everyOne[0], everyOne[1], newsrc)
            break
        except Exception as e:
            try_api+=1
            logger.error("Error in claude_api.syntax, retrying...")
            logger.error(str(e))

    return  newsrc, data["correct code"]

def replace_with_regex(original, replacement, text):
    if(original == None):
        return text
    pattern = re.escape(original)
    result=re.sub(pattern, replacement, text)
    return result


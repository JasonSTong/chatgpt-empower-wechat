import random

import asyncio

import openai
from wechaty_puppet import get_logger

from base import openai_key_list, openai_org, redis
from util.uuid_util import getUUIDWithoutLine

log = get_logger("openai_default")

def create_openai():
    openai_key = openai_key_list[random.randint(0, len(openai_key_list) - 1)]
    redis.incr("openai_key_used_count:" + openai_key, 1)
    openai_ = openai
    openai_.api_key = openai_key
    openai_.organization = openai_org
    log.info(f"使用openai_key:{openai_key}")
    return openai_


def completion_ai_api():
    return create_openai().Completion


def chat_completion_ai_api():
    return create_openai().ChatCompletion


def img_ai_api():
    return create_openai().Image


def text_ai(prompt: str):
    response_text = []
    while True:
        response = completion_ai_api().create(engine='text-davinci-003', prompt=prompt, max_tokens=1024,
                                              n=1,
                                              stop=None,
                                              temperature=0, top_p=1)
        text = response.get('choices')[0].text[:6].replace("\n", "") + response.get('choices')[0].text[6:]
        response_text.append(text)
        if response.get('choices')[0].finish_reason == "stop":
            return response_text


def text_ai_v2(message: list) -> set:
    response_text: set = set()
    uuid = getUUIDWithoutLine()
    log.info(f"uuid:{uuid}\n传入参数:{message}")
    while True:
        response = chat_completion_ai_api().create(model='gpt-3.5-turbo-0301', messages=message, max_tokens=1024,
                                                   n=1,
                                                   stop=None,
                                                   temperature=0, top_p=1)
        text = response.get('choices')[0].message.content[:6].replace("\n", "") + response.get('choices')[
                                                                                      0].message.content[6:]
        log.info(f"uuid:{uuid}\nresponse:{text}")
        response_text.add(text)
        if response.get('choices')[0].finish_reason == "stop":
            return response_text


def text_ai(message: list, model: str):
    response_text: set = set()
    uuid = getUUIDWithoutLine()
    log.info(f"uuid:{uuid}\n传入参数:{message}")
    while True:
        response = chat_completion_ai_api().create(model=model, messages=message, max_tokens=1024,
                                                   n=1,
                                                   stop=None,
                                                   temperature=0, top_p=1)
        text = response.get('choices')[0].message.content[:6].replace("\n", "") + response.get('choices')[
                                                                                      0].message.content[6:]
        log.info(f"uuid:{uuid}\nresponse:{text}")
        response_text.add(text)
        if response.get('choices')[0].finish_reason == "stop":
            return response_text


def text_ai_gpt4(message: list):
    return text_ai(message, "gpt-4-32k")


async def async_text_ai(message: list, model: str):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, text_ai, message, model)
    return result


async def async_text_ai_gpt4(message: list):
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, text_ai_gpt4, message)
    return result


async def async_text_ai_v2(message: list) -> set:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, text_ai_v2, message)
    return result


def img_ai(prompt):
    response_text = img_ai_api().create(prompt=prompt, size='1024x1024', n=1, response_format='url')
    return response_text.get('data')[0].url

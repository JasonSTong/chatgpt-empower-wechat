import logging
import random

import openai

from base import openai_key_list, openai_org


def create_openai():
    openai_key = openai_key_list[random.randint(0, len(openai_key_list) - 1)]
    openai_ = openai
    openai_.api_key = openai_key
    openai_.organization = openai_org
    return openai_


def completion_ai_api():
    return create_openai().Completion


def img_ai_api():
    return create_openai().Image


def text_ai(prompt: str):
    response_text = []
    flag = True
    while flag:
        response = completion_ai_api().create(engine='text-davinci-003', prompt=prompt, max_tokens=1024,
                                              n=1,
                                              stop=None,
                                              temperature=0.5)
        text = response.get('choices')[0].text[:6].replace("\n","")+response.get('choices')[0].text[7:]
        response_text.append(text)
        if response.get('choices')[0].finish_reason == "stop":
            return response_text


def img_ai(prompt):
    response_text = img_ai_api().create(prompt=prompt, size='1024x1024', n=1, response_format='url')
    return response_text.get('data')[0].url

import logging

from base import completion_ai_api, image_ai_api


def text_ai(prompt: str):
    response_text = []
    flag = True
    while flag:
        response = completion_ai_api.create(engine='text-davinci-003', prompt=prompt, max_tokens=1024,
                                            n=1,
                                            stop=None,
                                            temperature=0.5)
        response_text.append(response.get('choices')[0].text)
        if response.get('choices')[0].finish_reason == "stop":
            return response_text


def img_ai(prompt):
    response_text = image_ai_api.create(prompt=prompt, size='1024x1024', n=1, response_format='url')
    print(response_text)
    return response_text.get('data')[0].url

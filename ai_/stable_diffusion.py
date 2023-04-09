import base64
import datetime
import os

from webuiapi import webuiapi
from wechaty_puppet import get_logger

from base import sd_ip, sd_port, sd_server_error_msg, sd_models
from config.generation_config import config_dict
from util import uuid_util
from util.server_util import is_port_open

log = get_logger(__name__)


def create_sd(model_name: str):
    is_online = ping_sd()
    if is_online is False:
        return False, sd_server_error_msg
    model_value = sd_models.get(model_name)
    if model_value is None:
        return False, "未找到模型"
    api = webuiapi.WebUIApi(host=sd_ip, port=sd_port)
    options = api.get_options()
    options['sd_model_checkpoint'] = model_value
    return True, api


def txt2img(model_name: str, prompt: str):
    is_online, api_or_error_msg = create_sd(model_name)
    if is_online is False:
        return is_online, api_or_error_msg
    prompt = prompt + 'best quality, masterpiece, highres,8k uhd'
    save_images = True
    steps = 60
    sampler_name = "DPM++ 2M Karras"
    negative_prompt = "(((nsfw))),(worst quality:2), (low quality:2), (normal quality:2), lowres, (monochrome:1.21), (grayscale:1.21), skin spots, acnes, skin blemishes, bad anatomy, deepnegative, (fat:1.2), facing away, looking away, tilted head, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worstquality, jpegartifacts, signature, watermark, username, blurry, bad feet, poorly drawn hands, poorly drawn face, mutation, deformed, jpeg artifacts, extra fingers, extra limbs, extra arms, extra legs, malformed limbs, fused fingers, too many fingers, long neck, cross-eyed, mutated hands, polar lowres, bad body, bad proportions, gross proportions, missing arms, missing legs, extra leg, extra foot"
    log.info(f"final_prompt:{prompt}")
    result = api_or_error_msg.txt2img(prompt=prompt, save_images=save_images, steps=steps,
                                      negative_prompt=negative_prompt,
                                      sampler_name=sampler_name)
    image = result.images[0]

    log.info("======================生成图片============================")
    today = "stable_diffusion/" + datetime.date.today().__str__() + '/'
    uuid = uuid_util.getUUIDWithoutLine()
    file_path = today + uuid + '.png'
    if not os.path.exists(today):
        os.makedirs(today)
    image.convert('RGBA')
    image.save(file_path, format='PNG')

    log.info(f"图片地址:{file_path}")
    log.info("========================================================")
    return is_online, file_path


def ping_sd():
    if is_port_open(sd_ip, sd_port):
        return True
    else:
        return False

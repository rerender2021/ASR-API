import argparse
import os
import sys
import textwrap
import threading

from mugwort import Logger

from asr_client import asr_client, get_current_data
from asr_server import asr_server
import asyncio

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# args parse
parser = argparse.ArgumentParser(
    description='This is a project that wraps ASR API by FastAPI.',
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=r'''''')
parser.add_argument('--host', type=str, help='listen host')
parser.add_argument('--port', type=int, help='listen port')
parser.add_argument('--vosk-port', type=int, help='listen vosk port')
parser.add_argument('--model-path', type=str, help='model path')
parser.set_defaults(host='127.0.0.1', port=8200, vosk_port=8210, model_path="./model/vosk-model-en-us-0.22-lgraph")
params = parser.parse_args()

# init logger
log = Logger('ASR-API', Logger.INFO)
log.info('ASR API is starting, please wait...')

def start_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# init fastapi & init ASR backend
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import PlainTextResponse
    from deepmultilingualpunctuation import PunctuationModel

    import torch
    print("torch info:")
    print(torch.__version__)
    print(torch.version.cuda)
    print(torch.cuda.is_available())

    app = FastAPI(openapi_url=None)
    global_data = {}
    global_data["server"] = asr_server(params.model_path, params.vosk_port)
    global_data["client"] = asr_client(params.vosk_port)

    punct_model_path = os.path.join(os.getcwd(), "./model/fullstop-punctuation-multilang-base")
    punctuator = PunctuationModel(model = punct_model_path)

    async def start():
        loop = asyncio.new_event_loop()
        t = threading.Thread(target=start_loop, args=(loop,))
        t.start()

        asyncio.run_coroutine_threadsafe(global_data["server"], loop)
        asyncio.run_coroutine_threadsafe(global_data["client"], loop)
        log.info("init end")

    asyncio.run(start())
except Exception as exc:
    log.exception(exc)
    sys.exit(1)


@app.on_event('startup')
async def print_startup_config():
    log.info(
        textwrap.dedent('''
            ASR API has been started
              Endpoint: POST http://%s:%d/asr
        ''').strip(),
        params.host,
        params.port
    )


@app.get('/ping')
async def pingpong_endpoint():
    return PlainTextResponse('pong')

@app.post('/asr')
async def asr(
        *, request: Request
):
    if 'content-type' in request.headers:
        content_type = request.headers.get('content-type').lower()
        # log.info('Request ContentType: %s', content_type)

        response = {}
        if content_type == 'application/json':
            # data = await request.json()
            current_data = get_current_data()
            if current_data != None and "data" in current_data:
                # use str due to perf issue
                data_str = current_data["data"]
                # data_json = json.loads(current_data["data"])
                response["result"] = data_str
            return response
        else:
            log.warning('Unsupported Content-Type: %s', type(content_type))
            return response
    else:
        log.warning('No Content-Type')
        return None

@app.post('/asr_queue')
async def asr(
        *, request: Request
):
    if 'content-type' in request.headers:
        content_type = request.headers.get('content-type').lower()
        # log.info('Request ContentType: %s', content_type)

        response = {}
        if content_type == 'application/json':
            # data = await request.json()
            current_data = get_current_data()
            if current_data != None and "data" in current_data:
                queue = current_data["queue"]
                response["result"] = queue.copy()
                current_data["queue"].clear()
            return response
        else:
            log.warning('Unsupported Content-Type: %s', type(content_type))
            return response
    else:
        log.warning('No Content-Type')
        return None


@app.post('/punct')
async def punct(
        *, request: Request
):
    if 'content-type' in request.headers:
        content_type = request.headers.get('content-type').lower()
        # log.info('Request ContentType: %s', content_type)

        response = {}
        if content_type == 'application/json':
            data = await request.json()
            text = data["text"]
            if text == "":  
                response["text"] = ""
            else:
                response["text"] = punctuator.restore_punctuation(text)

            return response
        else:
            log.warning('Unsupported Content-Type: %s', type(content_type))
            return response
    else:
        log.warning('No Content-Type')
        return None


if __name__ == '__main__':
    import uvicorn

    uvicorn.run(
        app,
        host=params.host,
        port=params.port,
        log_level='error',
        access_log=False,
    )

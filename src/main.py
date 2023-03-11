import argparse
import os
import sys
import textwrap

from mugwort import Logger

if getattr(sys, 'frozen', False):
    os.chdir(os.path.dirname(sys.executable))

# args parse
parser = argparse.ArgumentParser(
    description='This is a project that wraps xxx API by FastAPI.',
    formatter_class=argparse.RawTextHelpFormatter,
    epilog=r'''
  xxx API Helper

    Request params:

    Request examples:

''')
parser.add_argument('--host', type=str, help='listen host')
parser.add_argument('--port', type=int, help='listen port')
parser.set_defaults(host='127.0.0.1', port=8090)
params = parser.parse_args()

# init logger
log = Logger('xxx-API', Logger.INFO)
log.info('xxx API is starting, please wait...')

# init fastapi & init xxx backend
try:
    from fastapi import FastAPI, Request
    from fastapi.responses import PlainTextResponse

    app = FastAPI(openapi_url=None)

except Exception as exc:
    log.exception(exc)
    sys.exit(1)


@app.on_event('startup')
async def print_startup_config():
    log.info(
        textwrap.dedent('''
            xxx API has been started
              Endpoint: POST http://%s:%d/demo
        ''').strip(),
        params.host,
        params.port
    )


@app.get('/ping')
async def pingpong_endpoint():
    return PlainTextResponse('pong')


@app.post('/demo')
async def demo(
        *, request: Request
):
    if 'content-type' in request.headers:
        content_type = request.headers.get('content-type').lower()
        log.info('Request ContentType: %s', content_type)

        response = {}
        if content_type == 'application/json':
            data = await request.json()
            response["foo"] = "bar"
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

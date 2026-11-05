"""Team-side example; run behind YOUR HTTPS reverse proxy on public port 443.
Defaults to local Ollama (http://127.0.0.1:11434/v1/chat/completions) with model qwen3.5:4b.
Set TEAM_GATEWAY_TOKEN. TEAM_PROVIDER_URL, TEAM_MODEL, and TEAM_PROVIDER_KEY are optional for local Ollama.
Disable ingress request/body logging; enforce concurrency/body/time/rate limits.
Never submit this server or credentials in your frozen controller ZIP.
"""
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import os
from urllib.request import HTTPRedirectHandler, Request, build_opener, ProxyHandler, HTTPSHandler


class NoProviderRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Decline the follow-up request; urllib treats the 3xx as an HTTP error.
        return None


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Length', '2')
            self.end_headers()
            self.wfile.write(b'ok')
        else:
            self.send_error(404)

    def do_POST(self):
        try:
            token = os.environ.get('TEAM_GATEWAY_TOKEN', '')
            if self.path != '/gateway' or not token or not hmac.compare_digest(
                    self.headers.get('Authorization', ''), 'Bearer ' + token):
                self.send_error(403); return
            size = int(self.headers.get('Content-Length', '0'))
            if not 0 < size <= 65536: raise ValueError()
            frame = json.loads(self.rfile.read(size))
            if set(frame) != {'messages', 'max_output_tokens'}: raise ValueError()
            if not isinstance(frame['messages'], list) or not 1 <= len(frame['messages']) <= 24: raise ValueError()
            if type(frame['max_output_tokens']) is not int or not 16 <= frame['max_output_tokens'] <= 2048: raise ValueError()
            url = os.environ.get('TEAM_PROVIDER_URL', 'http://127.0.0.1:11434/v1/chat/completions')
            if not (url.startswith('https://') or url.startswith('http://')): raise ValueError()
            model = os.environ.get('TEAM_MODEL', 'qwen3.5:4b')
            headers = {'Content-Type': 'application/json'}
            key = os.environ.get('TEAM_PROVIDER_KEY')
            if key:
                headers['Authorization'] = 'Bearer ' + key
            payload = {'model': model, 'messages': frame['messages'],
                       'max_tokens': frame['max_output_tokens'], 'stream': False}
            request = Request(url, data=json.dumps(payload).encode(), headers=headers)
            opener = build_opener(ProxyHandler({}), HTTPSHandler(), NoProviderRedirect())
            with opener.open(request, timeout=35) as response:
                raw = response.read(131073)
            if len(raw) > 131072: raise ValueError()
            result = json.loads(raw)
            text = result['choices'][0]['message']['content']
            if not isinstance(text, str) or not 0 < len(text.encode()) <= 65536: raise ValueError()
            usage = result.get('usage', {})
            body = json.dumps({'text': text, 'usage': {out: usage[key] for key, out in (
                ('prompt_tokens', 'input_tokens'), ('completion_tokens', 'output_tokens'))
                if type(usage.get(key)) is int and usage[key] >= 0}}).encode()
            self.send_response(200); self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body))); self.end_headers(); self.wfile.write(body)
        except Exception:
            self.send_error(503, 'Team gateway unavailable')


if __name__ == '__main__':
    if not os.environ.get('TEAM_GATEWAY_TOKEN'):
        raise SystemExit('Configure TEAM_GATEWAY_TOKEN environment variable')
    port = int(os.environ.get('PORT', 8080))
    # Cloud hosts set BIND_HOST=0.0.0.0; local runs stay loopback-only.
    host = os.environ.get('BIND_HOST') or (
        '0.0.0.0' if os.environ.get('K_SERVICE') else '127.0.0.1')
    HTTPServer((host, port), Handler).serve_forever()

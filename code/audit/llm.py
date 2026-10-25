"""Groq intent classification. Standard library only; credentials stay in memory."""
import hashlib
import json
import os
import time
from pathlib import Path
from urllib import error, request

MODEL = 'openai/gpt-oss-120b'
ENDPOINT = 'https://api.groq.com/openai/v1/chat/completions'
USER_AGENT = 'NorthstarDeletionAudit/1.0'
ROOT = Path(__file__).resolve().parents[2]
PROMPT_PATH = Path(__file__).resolve().parents[1]/'prompts'/'intent_classification.md'
# Published Groq on-demand USD rates per million tokens, checked 2026-10-25:
# https://console.groq.com/docs/model/openai/gpt-oss-120b
PRICES_PER_MILLION = {'input': 0.15, 'output': 0.60}
PRICE_NOTE = ('Groq published on-demand rates checked 2026-10-25; '
              'https://console.groq.com/docs/model/openai/gpt-oss-120b . '
              'Recheck https://groq.com/pricing before use. Estimates exclude '
              'account discounts and provider-side prompt-cache reductions.')
POLICY_PATH = Path(__file__).with_name('intent_policy.json')
try:
    DEFAULT_MODE = json.loads(POLICY_PATH.read_text(encoding='utf-8'))['mode']
    if DEFAULT_MODE not in ('primary','shadow','rules'):
        DEFAULT_MODE = 'shadow'
except (OSError, ValueError, KeyError, TypeError):
    DEFAULT_MODE = 'primary'


def parsed_answer(value):
    if (not isinstance(value, dict) or type(value.get('deletes')) is not bool
            or not isinstance(value.get('reason'), str) or not value['reason'].strip()):
        return None
    return {'deletes': value['deletes'], 'reason': value['reason'].strip()[:240]}


class IntentClassifier:
    def __init__(self, cache_dir=None, prompt_path=None, mode='primary'):
        if mode not in ('primary', 'shadow', 'rules'):
            raise ValueError('Invalid intent mode')
        self.cache_dir = Path(cache_dir) if cache_dir is not None else ROOT/'.runtime'/'llm_cache'
        self.prompt_path = Path(prompt_path) if prompt_path is not None else PROMPT_PATH
        self.mode = mode
        self.memory = {}
        self.memory_usage = {}
        self.intent_answers = {}  # Engine-level deduplication of repeated ownership checks.
        self.records = {}
        self.http_failures = {}
        self.unavailable_http_status = None
        self.prompt = None
        self.digests = {}
        self.counters = dict(live_calls=0, cache_hits=0, live_input_tokens=0,
                             live_output_tokens=0, cached_input_tokens=0,
                             cached_output_tokens=0, failures=0, missing_key=0,
                             skipped_unavailable=0)

    def _tokens(self, usage, prefix):
        self.counters[prefix+'_input_tokens'] += usage['input_tokens']
        self.counters[prefix+'_output_tokens'] += usage['output_tokens']

    @staticmethod
    def _usage(usage):
        if not isinstance(usage, dict):
            return None
        result = {name: usage.get(name) for name in ('input_tokens', 'output_tokens')}
        return result if all(type(n) is int and n >= 0 for n in result.values()) else None

    def classify(self, text):
        if self.mode == 'rules':
            return None
        # This is the ONLY credential source. Do not persist keys, headers,
        # request objects, HTTP bodies containing errors, or exception messages.
        key = os.environ.get('GROQ_API_KEY')
        if not key:
            self.counters['missing_key'] += int(text not in self.memory)
            self.memory[text] = None
            return None
        try:
            if self.prompt is None:
                self.prompt = self.prompt_path.read_text(encoding='utf-8')
            prompt = self.prompt
        except (OSError, UnicodeError):
            return None
        if text not in self.digests:
            self.digests[text] = hashlib.sha256(json.dumps([MODEL, prompt, text],ensure_ascii=False,
                                                   separators=(',', ':')).encode('utf-8')).hexdigest()
        digest = self.digests[text]
        if digest in self.memory:
            if self.memory[digest] is not None:
                self.counters['cache_hits'] += 1
                self._tokens(self.memory_usage[digest], 'cached')
            return self.memory[digest]
        path = self.cache_dir/(digest+'.json')
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            answer = parsed_answer(data.get('answer'))
            usage = self._usage(data.get('usage'))
            if data.get('model') == MODEL and answer and usage and key not in json.dumps(data):
                self.counters['cache_hits'] += 1
                self._tokens(usage, 'cached')
                self.memory[digest] = answer
                self.memory_usage[digest] = usage
                return answer
        except (OSError, ValueError, TypeError, AttributeError):
            pass
        if self.unavailable_http_status is not None:
            self.counters['skipped_unavailable'] += 1
            self.memory[digest] = None
            return None
        payload = json.dumps(dict(model=MODEL, temperature=0,
            response_format={'type': 'json_object'}, max_completion_tokens=512,
            reasoning_effort='low',include_reasoning=False,
            messages=[{'role': 'system', 'content': prompt},
                      {'role': 'user', 'content': text}]),ensure_ascii=False).encode('utf-8')
        # A request accidentally containing the credential must never be sent.
        if key.encode('utf-8') in payload:
            self.memory[digest] = None
            return None
        for attempt in range(2):
            self.counters['live_calls'] += 1
            try:
                req = request.Request(ENDPOINT, data=payload, method='POST',
                    headers={'Content-Type': 'application/json', 'Authorization': 'Bearer '+key,
                             'User-Agent': USER_AGENT})
                with request.urlopen(req, timeout=20) as response:
                    envelope = json.loads(response.read().decode('utf-8'))
                tokens = envelope.get('usage', {})
                usage = self._usage(dict(input_tokens=tokens.get('prompt_tokens'),
                                         output_tokens=tokens.get('completion_tokens')))
                if usage:
                    self._tokens(usage, 'live')
                answer = parsed_answer(json.loads(envelope['choices'][0]['message']['content']))
                if not answer or usage is None or key in json.dumps(answer):
                    break
                cache = dict(model=MODEL, answer=answer, usage=usage)
                try:
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    temporary = path.with_suffix('.tmp')
                    temporary.write_text(json.dumps(cache,ensure_ascii=False),encoding='utf-8')
                    temporary.replace(path)
                except OSError:
                    pass  # A read-only cache must not discard a valid answer.
                self.memory[digest] = answer
                self.memory_usage[digest] = usage
                return answer
            except error.HTTPError as exc:
                self.http_failures[str(exc.code)] = self.http_failures.get(str(exc.code),0)+1
                if exc.code in (401,403,404):
                    # Authentication/access/model availability applies to this
                    # entire client; avoid repeating the same rejection for
                    # every request. A new run/client resets this circuit.
                    self.unavailable_http_status = exc.code
                retryable = exc.code == 429 or 500 <= exc.code <= 599
                exc.close()
                if attempt == 0 and retryable:
                    time.sleep(1)
                    continue
                break
            except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError):
                break
        self.counters['failures'] += 1
        self.memory[digest] = None
        return None

    def record(self, text, rules, answer, selected, case_id=None, explicit_refusal=False):
        identifier = case_id or hashlib.sha256(text.encode('utf-8')).hexdigest()
        self.records[identifier] = dict(case_id=case_id, rules_deletes=rules,
            llm_deletes=answer['deletes'] if answer else None, selected_deletes=selected,
            explicit_refusal=explicit_refusal, reason=answer['reason'] if answer else None)

    def agreement(self, case_ids=None):
        records = [v for k,v in self.records.items() if case_ids is None or k in case_ids]
        classified = [v for v in records if v['llm_deletes'] is not None]
        agreed = sum(v['rules_deletes'] == v['llm_deletes'] for v in classified)
        return dict(cases=len(records), classified=len(classified), agreed=agreed,
                    disagreements=len(classified)-agreed,
                    agreement_rate=agreed/len(classified) if classified else None,
                    unavailable=len(records)-len(classified))

    def usage(self):
        result = dict(self.counters)
        result.update(provider='Groq',model=MODEL, mode=self.mode, price_note=PRICE_NOTE)
        result['http_failures_by_status'] = dict(sorted(self.http_failures.items()))
        result['input_tokens'] = result['live_input_tokens']+result['cached_input_tokens']
        result['output_tokens'] = result['live_output_tokens']+result['cached_output_tokens']
        result['total_tokens'] = result['input_tokens']+result['output_tokens']
        result['estimated_live_cost_usd'] = (result['live_input_tokens']*PRICES_PER_MILLION['input']+
                                            result['live_output_tokens']*PRICES_PER_MILLION['output'])/1e6
        result['estimated_uncached_equivalent_cost_usd'] = (result['input_tokens']*PRICES_PER_MILLION['input']+
                                                         result['output_tokens']*PRICES_PER_MILLION['output'])/1e6
        return result


_default_client = None


def get_client():
    global _default_client
    if _default_client is None:
        _default_client = IntentClassifier(mode=DEFAULT_MODE)
    return _default_client


def configure(mode=DEFAULT_MODE):
    global _default_client
    _default_client = IntentClassifier(mode=mode)
    return _default_client


def write_usage_report(path, summary):
    u = summary['intent_usage']
    count = summary['requests']
    live_total = u['live_input_tokens']+u['live_output_tokens']
    cache_total = u['cached_input_tokens']+u['cached_output_tokens']
    agreement = summary['intent_agreement']
    rate = f"{agreement['agreement_rate']:.4%}" if agreement['agreement_rate'] is not None else 'N/A (no valid LLM answers)'
    lines = ['# Final-run usage report','',
        f"Output: `{summary['output_name']}`; requests: {count}; SHA-256: `{summary['output_sha256']}`.",
        f"Elapsed: {summary['seconds']} s. Intent mode: {u['mode']}; valid request-level agreement: {rate}.",'',
        '| Provider / model / source | Live HTTP attempts | Disk cache hits | Input tokens | Output tokens | Total tokens | Estimated incremental API cost |',
        '|---|---:|---:|---:|---:|---:|---:|',
        f"| Groq / {MODEL} / live | {u['live_calls']} | 0 | {u['live_input_tokens']} | {u['live_output_tokens']} | {live_total} | ${u['estimated_live_cost_usd']:.8f} |",
        f"| Groq / {MODEL} / local response cache | 0 | {u['cache_hits']} | {u['cached_input_tokens']} | {u['cached_output_tokens']} | {cache_total} | $0.00000000 |",
        f"| Per-model total: Groq / {MODEL} | {u['live_calls']} | {u['cache_hits']} | {u['input_tokens']} | {u['output_tokens']} | {u['total_tokens']} | ${u['estimated_live_cost_usd']:.8f} |",
        f"| Overall token-billed total | {u['live_calls']} | {u['cache_hits']} | {u['input_tokens']} | {u['output_tokens']} | {u['total_tokens']} | ${u['estimated_live_cost_usd']:.8f} |",'',
        f"Average tokens per output request: {u['total_tokens']/count:.4f}; live {live_total/count:.4f}; cached {cache_total/count:.4f}.",
        f"Estimated incremental cost per request: ${u['estimated_live_cost_usd']/count:.10f}. Estimated uncached-equivalent total cost (including reused responses): ${u['estimated_uncached_equivalent_cost_usd']:.8f}.",
        f"Price assumptions (USD / 1M tokens): input {PRICES_PER_MILLION['input']}; output {PRICES_PER_MILLION['output']}. {PRICE_NOTE}",'',
        f"Failed classifications: {u['failures']}; distinct texts unavailable because no environment key: {u['missing_key']}.",
        f"HTTP failures by status (no error bodies retained): {json.dumps(u['http_failures_by_status'],sort_keys=True)}.",
        f"Classifications skipped after a terminal provider access/model rejection: {u['skipped_unavailable']} (rules fallback; a new client/run retries).",
        'Live calls count HTTP attempts, including retries. Tokens on a successful API envelope count even if answer JSON is rejected. Failed requests without returned usage have unknown tokens, not estimated tokens. Local cache tokens are counted separately and incur no new API charge. Repeated in-process lookups reuse memory without counting the same response again.',
        'The global ownership solver can classify other supplied requests as context; their usage is included. Requests are processed sequentially, with no concurrent API calls. Cache identity includes the model, full prompt and exact request text.',
        f"Local OCR: {summary['ocr_usage']['calls']} calls; {summary['ocr_usage']['cache_hits']} cache hits. Windows.Media.Ocr model identifier is OS-managed and unavailable; tokens N/A; API cost $0. Local compute and development-chat costs are not measured.",'']
    if not u['total_tokens']:
        cause = ('Supply GROQ_API_KEY through the process environment and rerun.' if u['missing_key']
                 else 'The environment credential was present, but no usable token-bearing responses were received; check provider status/model access.')
        lines += ['Live Groq validation has NOT been established: no real response tokens were observed. Mock-test tokens are excluded. '+cause,'']
    Path(path).write_text('\n'.join(lines),encoding='utf-8')

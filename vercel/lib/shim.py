"""Shims: consts + states + dummies injected into _ported_raw namespace. NO Fly."""
import os
import re
import threading


def install(R):
    R.BASE_URL = "https://aifreeforever.com"
    R.UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0 Safari/537.36")
    R.POL_URL = "https://text.pollinations.ai/"
    R.GZ_BASE = "https://www.giz.ai"
    R.GZ_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36")
    R.GZ_PFB9 = "c7380813ca955a386914044983fbcf6a082dbf2bea2eb91917b37ba33d6ff05b"
    R.GZ_COOLDOWN = {"quota": 600.0, "login": 600.0}
    R.GZ_CDN = "https://cdnwww.giz.ai/api/model/choices/textGeneration"
    R.GZ_SKIP = {"dynamic"}
    R.LR_B = "https://www.app.lorka.ai"
    R.LR_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
               "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")
    R.KURDISH_NUMS = ["الأول", "الثاني", "الثالث", "الرابع", "الخامس",
                      "السادس", "السابع", "الثامن", "التاسع", "العاشر"]
    R.SERVER_PRIORITY = [["gemini"], ["gpt"]]
    R.ACH_API = "https://us-central1-allchatprod.cloudfunctions.net"
    R.ACH_ORIG = {"Origin": "https://app.askallchat.com",
                  "Referer": "https://app.askallchat.com/"}
    R.ACH_MODELS = [("consensus", "GPT-5 Consensus", ""),
                     ("code", "GPT-5 Code", ""),
                     ("math", "GPT-5 Math", ""),
                     ("deep", "Deep Analysis", ""),
                     ("web", "Live Web Search", ""),
                     ("gemini", "Gemini Flash-Lite", "google/gemini-2.5-flash-lite"),
                     ("gpt4o", "GPT-4o Mini", "openai/gpt-4o-mini"),
                     ("llama", "Llama 3.1 8B", "meta-llama/llama-3.1-8b-instruct")]
    R.ACH_REAL = {k: m for k, _, m in R.ACH_MODELS if m}
    R.ACH_SMART = ("consensus", "code", "math", "deep", "web")
    R.ACH_WRAPS = {
        "consensus": "\n\n(تکایە بە شیکردنەوەیەکی قووڵ، بەراوردی فرە-ڕوانگە، و هەنگاوە بیرکارییەکان وەڵام بدەوە)",
        "code": "\n\n(تکایە بە کۆدی تەواو و ڕوونکردنەوەی تەکنیکی قووڵ وەڵام بدەوە)",
        "math": "\n\n(تکایە بە هاوکێشەی ماتماتیکی و سەلماندنی هەنگاو بە هەنگاو وەڵام بدەوە)",
        "deep": "\n\n(تکایە بە بەراوردی فرە-ڕوانگەی قووڵ و شیکردنەوەی ڕەخنەگرانە وەڵام بدەوە)",
        "web": "\n\n(تکایە بە دوایین زانیاری و سەرچاوەی تازە لە ئینتەرنێت وەڵام بدەوە)",
    }
    R.ACH_BUDGET = 3
    R.ACH_DAY_CAP = 500  # #119: 250→500 (fill 1000 in ~2d once proxy-fixed)
    R.ACH_FB_KEY = os.environ.get("ACH_FB_KEY") or ""
    R.ACH_ST = {}
    R.ACH_LOCK = threading.Lock()
    R.ACH_ACC_FILE = "/tmp/vpx_ach.json"
    R.DATA_DIR = "/tmp"
    R._UA_POOL = [R.UA, R.LR_UA, R.GZ_UA]
    # dummies — file-json path never runs (KV overrides), but keep import/call safe
    R._ENC_MAGIC = ""
    R._JSON_LOCKS = {}
    R._JSON_LOCKS_G = threading.Lock()
    R._get_fernet = None

    def _nope(*a, **k):
        raise RuntimeError("file-json disabled on Vercel (KV only)")

    R._json_save_locked = _nope
    # proxy defaults (providers.py overrides with KV versions)
    R._proxy_get = lambda n=3: []
    R._proxy_mark_bad = lambda px: None
    # ---- pools (V2) ----
    C153 = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36")
    R.AC_BASE = "https://askaichat.app"
    R.AC_UA = C153
    R.AC_FALLBACK = {'gpt-5.4-nano': ('gpt-5.4-nano', 'GPT-5.4 Nano')}
    R.AC_KEY = os.environ.get("AC_FB_KEY") or ""
    R.AL_SB = "https://felzqwdxfitazkrktyke.supabase.co"
    R.AL_BASE = "https://allchatbots.ai"
    R.AL_UA = C153
    R.AL_COOKIE = "sb-felzqwdxfitazkrktyke-auth-token"
    R.AL_KEY = os.environ.get("AL_KEY") or ""
    R.ALLE_API = "https://api.alle-ai.com/api/v1"
    R.ALLE_WSS = "wss://api.alle-ai.com/app/pb1ry0ntlug7dm2fga0s?protocol=7&client=js&version=8.4.0-1reverb&flash=false"
    R.ALLE_AUTH_EP = "https://api.alle-ai.com/broadcasting/auth"
    R._ALLE_UA = C153
    R.CA_BASE = "https://chatbotai.co"
    R.CA_UA = C153
    R.CA_FALLBACK = {'gpt-5.4-nano': ('gpt-5.4-nano', 'GPT-5.4 Nano'), 'gpt-5.4-instant': ('gpt-5.4-instant-2026-03-05', 'GPT-5.4 Instant'), 'gemini-3.1-pro': ('gemini-3.1-pro-preview', 'Gemini 3.1 Pro'), 'claude': ('claude-sonnet-5', 'Claude Sonnet 5'), 'perplexity': ('sonar', 'Perplexity'), 'deepseek': ('deepseek-4-pro-0813', 'DeepSeek-V4-Pro'), 'grok': ('grok-4.6', 'Grok 4.6'), 'claude-fable': ('claude-fable-5-1', 'Claude Fable 5.1'), 'claude-opus': ('claude-opus-5', 'Claude Opus 5'), 'gemini': ('gemini-3.8-flash', 'Gemini 3.8 Flash'), 'gpt-5.6-sol': ('gpt-5.6-sol', 'GPT-5.6 Sol'), 'gpt-5.6-terra': ('gpt-5.6-terra', 'GPT-5.6 Terra'), 'gpt-5.6-luna': ('gpt-5.6-luna', 'GPT-5.6 Luna'), 'gpt-6-astra': ('gpt-6-astra', 'GPT-6 Astra'), 'gpt-5.5': ('gpt-5.5-2026-04-23', 'GPT-5.5'), 'kimi': ('kimi-k3', 'Kimi K3'), 'kimi-k2.6': ('kimi-k2.6', 'Kimi K2.6'), 'kimi-k3-thinking': ('kimi-k3-thinking', 'Kimi K3 Thinking'), 'deepseek-v4-pro-thinking': ('deepseek-4-pro-0813-thinking', 'DeepSeek-V4-Pro Thinking'), 'o3': ('o3-2025-04-16', 'OpenAI o3'), 'llama': ('llama-4-maverick', 'Llama 4'), 'gpt-4': ('gpt-4o-2024-08-06', 'GPT-4o'), 'gpt-4o-mini': ('gpt-4o-mini-2024-07-18', 'GPT-4o-mini'), 'gpt-4.1': ('gpt-4.1-2025-04-14', 'GPT-4.1')}
    R.CB_BASE = "https://api.chatbotapp.ai"
    R.CB_UA = C153
    R.NV_BASE = "https://api.novaapp.ai"
    R.NV_UA = C153
    R.RWD_BASE = "https://api.rewind.ai"
    R.RWD_ABSMAX = 10000
    R.RWD_BUDGET = 2300
    R.EM_ST = {}
    R.PIA_ST = {}
    R.MS = {"duck": {}, "ak_ok": {}, "ak_block": {}, "l7_ok": {}, "l7_bad": {}, "ct_ok": {}, "ct_bad": {}, "yl_ok": {}, "yl_bad": {}, "hk_ok": {}, "hk_bad": {}, "hf_ok": {}, "hf_bad": {}, "aka_ok": {}, "aka_bad": {}, "hb_ok": {}, "hb_bad": {}, "gk_ok": {}, "gk_bad": {}, "gz_ok": {}, "gz_bad": {}, "pi_ok": {}, "pi_bad": {}, "cb_ok": {}, "cb_bad": {}, "nv_ok": {}, "nv_bad": {}, "al_ok": {}, "al_bad": {}, "aiml_ok": {}, "ac_ok": {}, "ca_ok": {}}
    R.MODEL_SYNC_FILE = "/tmp/vpx_msync.json"
    R._TLS = threading.local()
    R.CA_ST = {}
    R.CB_ST = {}
    R.NV_ST = {}
    R.AC_ST = {}
    R.AL_ST = {}
    R.ALLE_ST = {}
    R.RWD_ST = {"day": "", "used": {}, "dead": {}, "total": 0}
    R._RWD_STATE = {"i": 0}
    R._CA_LK = threading.Lock()
    R._CB_LK = threading.Lock()
    R._NV_LK = threading.Lock()
    R._AC_LK = threading.Lock()
    R._RWD_LK = threading.Lock()
    R.ALLE_LOCK = threading.Lock()
    R._REPLACE_SEM = threading.Semaphore(2)
    R._FERNET_KEY = ""

    R.PROXY_ST = {"pool": {}, "strikes": {}, "bad": set()}
    R.PIA_API = 'https://piax-api.piax.org'
    R.PIA_LOCK = threading.Lock()
    R._SG_BREAKER = {}
    R._SG_BREAKER_LK = threading.Lock()
    R._RWD_FREE_HINTS = ('flash', 'mini', 'lite', 'nano', 'small', 'turbo')
    R._RWD_VERIFIED = ['deepseek/deepseek-v4-pro', 'deepseek/deepseek-r1', 'qwen/qwen3.7-max', 'qwen/qwen3-max', 'z-ai/glm-5.3', 'z-ai/glm-5.2', 'moonshotai/kimi-k2.6', 'thinkingmachines/inkling', 'mistralai/mistral-large', 'microsoft/phi-4', 'amazon/nova-pro-v1', 'inception/mercury-2.5', 'google/gemini-3.8-flash', 'x-ai/grok-4.3', 'deepseek/deepseek-v4-flash', 'z-ai/glm-5.3-flash', 'qwen/qwen3.8-flash', 'meta-llama/llama-4-maverick', 'qwen/qwen-2.5-7b-instruct']

    R._RWD_UAS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:131.0) Gecko/20100101 Firefox/131.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Fedora; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0', 'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 OPR/112.0.0.0', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:127.0) Gecko/20100101 Firefox/127.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64; rv:126.0) Gecko/20100101 Firefox/126.0', 'Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64; rv:123.0) Gecko/20100101 Firefox/123.0']

    R.ACT_BASE = 'https://aga-api.aichatting.net'
    R.ACT_MODELS = ['gpt-5.6-luna']
    R.ACT_PUBKEY = '-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDCAdf/EyIbLBxjGqmh7qLU6/CPCzru+75+82OSPZ+nf4BFvg88drpZ6KigNW0J8TNgxe6Yms1irCZNVDyu+RXsl4y/7c2KOHc4OGTzHB5fUMiMasFUvcEs2P70e6yA/sKHZfBLG1XPhlb84Ibs3nhD3W5e2SuC+4EuVkaqzN08LQIDAQAB\n-----END PUBLIC KEY-----'
    R.ACT_UAS = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36']
    R.AIML_ST = {'tok': None, 'tok_t': 0.0, 'key': None, 'email': 'pimeyax560@dreameg.com', 'password': '12345678Rkjk@&'}
    R.AKA_BASE = 'https://chat.akash.network'
    R.AKA_LIMIT = {'until': 0.0}
    R.AKA_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.CBC_BASE = 'https://chatbotchatapp.com'
    R.CBOX_API = 'https://chat-box.ai/app/api/v1'
    R.CBOX_DAY_CAP = 100
    R.CBOX_FREE_ID = '88cc1733-9cf1-4652-a7be-f9a6dbe01737'
    R.CBOX_MODELS = [('aichat', 'AI Chat', 'Chatbox AI'), ('websearch', 'AI WebSearch', 'Chatbox WebSearch')]
    R.CBOX_ST = {'accounts': [], 'idx': 0, 'signups': {'date': '', 'n': 0}}
    R.CT_LIMIT = {'quota_until': 0.0, 'wobble_until': 0.0}
    R.CT_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.DUCK_FE_VERSION = 'serp_20260917_083005_ET-742796f26a61a81dbee67db3e7dd403a0e16294e'
    R.DUCK_JWK = [None]
    R.DUCK_STUBS_JS = 'var __ua = __DDG_REAL_UA__;\nvar __HTML_LOOKUP = __DDG_HTML_LOOKUP__;\n\nfunction __makeHtmlElement(tag) {\n  var state = { _innerHTML: \'\', _qsaCount: 0, _cssText: \'\' };\n  var styleObj = {};\n  Object.defineProperty(styleObj, \'cssText\', {\n    get: function(){ return state._cssText; },\n    set: function(v){ state._cssText = String(v||\'\'); },\n    enumerable: true, configurable: true\n  });\n  var el = {\n    tagName: String(tag).toUpperCase(),\n    nodeName: String(tag).toUpperCase(),\n    nodeType: 1,\n    children: [], childNodes: [], classList: [],\n    style: styleObj, dataset: {},\n    offsetWidth: 100, offsetHeight: 20, scrollHeight: 20,\n    offsetTop: 100, offsetLeft: 0, offsetParent: null,\n    clientWidth: 100, clientHeight: 20,\n    getBoundingClientRect: function(){\n      return { width: 100, height: 20, top: 100, left: 0, right: 100, bottom: 120, x: 0, y: 100 };\n    },\n    getClientRects: function(){\n      return [{ width: 100, height: 20, top: 100, left: 0, right: 100, bottom: 120 }];\n    },\n    setAttribute: function(){}, removeAttribute: function(){},\n    getAttribute: function(a){ if(a===\'srcdoc\') return state._srcdoc||\'\'; return null; },\n    hasAttribute: function(){ return false; },\n    appendChild: function(c){ return c; },\n    removeChild: function(c){ return c; },\n    addEventListener: function(){}, removeEventListener: function(){},\n    querySelector: function(){ return null; },\n    querySelectorAll: function(s){\n      if (s === \'*\') {\n        var arr = []; arr.length = state._qsaCount; return arr;\n      }\n      return [];\n    },\n    cloneNode: function(){ return __makeHtmlElement(tag); },\n    _getState: function(){ return state; }\n  };\n  Object.defineProperty(el, \'innerHTML\', {\n    get: function(){ return state._innerHTML; },\n    set: function(v){\n      var key = String(v);\n      var entry = __HTML_LOOKUP && __HTML_LOOKUP[key];\n      if (entry) { state._innerHTML = String(entry.html); state._qsaCount = entry.count|0; }\n      else { state._innerHTML = key; state._qsaCount = 0; }\n    },\n    enumerable: true, configurable: true\n  });\n  Object.defineProperty(el, \'outerHTML\', { get: function(){ return \'<\' + tag + \'>\' + state._innerHTML + \'</\' + tag + \'>\'; }, enumerable: true });\n  Object.defineProperty(el, \'srcdoc\', { get: function(){ return state._srcdoc||\'\'; }, set: function(v){ state._srcdoc = String(v); }, enumerable: true });\n  Object.defineProperty(el, \'contentWindow\', { get: function(){\n    var w = {};\n    w.document = __ifDoc;\n    w.Proxy = Proxy;\n    w.self = w;\n    w.top = w;\n    w.parent = w;\n    w.window = w;\n    return w;\n  }, enumerable: true });\n  Object.defineProperty(el, \'contentDocument\', { get: function(){ return __ifDoc; }, enumerable: true });\n  return el;\n}\n\nfunction __mkObj(name, base) {\n  base = base || {};\n  return new Proxy(base, {\n    get: function(t, k) {\n      if (k in t) return t[k];\n      if (k === Symbol.toPrimitive) return function(){ return \'\'; };\n      if (k === Symbol.iterator) return undefined;\n      if (k === \'then\' || k === \'catch\' || k === \'finally\') return undefined;\n      if (k === \'constructor\') return Object;\n      if (k === \'toString\' || k === \'valueOf\') return function(){ return \'[object \' + name + \']\'; };\n      if (k === \'length\') return 0;\n      if (k === \'nodeType\') return 1;\n      if (k === \'tagName\' || k === \'nodeName\') return \'DIV\';\n      if (k === \'innerHTML\' || k === \'outerHTML\' || k === \'textContent\' || k === \'innerText\' || k === \'value\') return \'\';\n      if (k === \'children\' || k === \'childNodes\' || k === \'classList\') return [];\n      if (typeof k === \'string\' && (k.indexOf(\'get\') === 0 || k.indexOf(\'query\') === 0 || k.indexOf(\'find\') === 0)) {\n        return function(arg){\n          if (k === \'querySelectorAll\' || k === \'getElementsByTagName\' || k === \'getElementsByClassName\') return [];\n          return null;\n        };\n      }\n      return function(){ return __mkObj(name + \'.\' + String(k)); };\n    },\n    has: function(t, k){ return k in t; },\n    set: function(t, k, v){ t[k] = v; return true; }\n  });\n}\n\nvar __ifMeta = __mkObj(\'meta\', {\n  getAttribute: function(a){ return a===\'content\' ? "default-src \'none\'; script-src \'unsafe-inline\';" : null; },\n  hasAttribute: function(a){ return a===\'content\'; },\n  tagName: \'META\', nodeName: \'META\'\n});\nvar __ifDoc;\n__ifDoc = __mkObj(\'iframeDoc\', {\n  querySelector: function(s){\n    if (s && s.indexOf(\'Content-Security-Policy\') !== -1) return __ifMeta;\n    if (s === \'meta\') return __ifMeta;\n    return null;\n  },\n  querySelectorAll: function(s){\n    if (s && s.indexOf(\'Content-Security-Policy\') !== -1) return [__ifMeta];\n    if (s === \'meta\') return [__ifMeta];\n    return [];\n  },\n  getElementsByTagName: function(t){ return t && t.toLowerCase()===\'meta\' ? [__ifMeta] : []; },\n  body: __mkObj(\'iframeBody\', {\n    querySelector: function(s){ return s && s.indexOf(\'Content-Security-Policy\')!==-1 ? __ifMeta : null; },\n    querySelectorAll: function(s){ return s && s.indexOf(\'Content-Security-Policy\')!==-1 ? [__ifMeta] : []; },\n    appendChild: function(){}, removeChild: function(){}\n  }),\n  head: __mkObj(\'iframeHead\', {\n    querySelector: function(s){ return s && s.indexOf(\'Content-Security-Policy\')!==-1 ? __ifMeta : null; },\n    querySelectorAll: function(s){ return s && s.indexOf(\'Content-Security-Policy\')!==-1 ? [__ifMeta] : []; },\n    appendChild: function(){}, removeChild: function(){}\n  }),\n  documentElement: __mkObj(\'iframeRoot\'),\n  createElement: function(){ return __mkObj(\'elem\', {setAttribute:function(){}, appendChild:function(){}, removeChild:function(){}, getAttribute:function(){return null;}, hasAttribute:function(){return false;}}); },\n  cookie: \'\', readyState: \'complete\'\n});\n\nvar __iframeEl = __mkObj(\'iframe\', {\n  contentDocument: __ifDoc,\n  contentWindow: __mkObj(\'iframeWin\', { document: __ifDoc, top: undefined, parent: undefined }),\n  document: __ifDoc,\n  getAttribute: function(a){\n    if (a===\'sandbox\') return \'allow-scripts allow-same-origin\';\n    if (a===\'srcdoc\') return \'\';\n    if (a===\'id\') return \'jsa\';\n    return null;\n  },\n  hasAttribute: function(a){ return a===\'sandbox\'||a===\'id\'; },\n  tagName: \'IFRAME\', nodeName: \'IFRAME\', id: \'jsa\'\n});\n\nvar document = __mkObj(\'document\', {\n  querySelector: function(s){\n    if (s === \'#jsa\') return __iframeEl;\n    if (s && s.indexOf(\'Content-Security-Policy\') !== -1) return __ifMeta;\n    return null;\n  },\n  querySelectorAll: function(s){\n    if (s === \'#jsa\') return [__iframeEl];\n    if (s && s.indexOf(\'Content-Security-Policy\') !== -1) return [__ifMeta];\n    return [];\n  },\n  getElementById: function(id){ return id===\'jsa\' ? __iframeEl : null; },\n  getElementsByTagName: function(t){ if(t&&t.toLowerCase()===\'iframe\') return [__iframeEl]; return []; },\n  getElementsByClassName: function(){ return []; },\n  body: __mkObj(\'body\', {appendChild:function(){}, removeChild:function(){}, querySelector:function(s){return s===\'#jsa\'?__iframeEl:null;}, querySelectorAll:function(s){return s===\'#jsa\'?[__iframeEl]:[];}}),\n  head: __mkObj(\'head\', {appendChild:function(){}, removeChild:function(){}, querySelector:function(){return null;}, querySelectorAll:function(){return [];}}),\n  documentElement: __mkObj(\'root\'),\n  createElement: function(tag){ return __makeHtmlElement(tag||\'div\'); },\n  createTextNode: function(t){ return {nodeType:3, nodeValue:String(t||\'\'), textContent:String(t||\'\')}; },\n  cookie: \'\', readyState: \'complete\', title: \'\',\n  addEventListener: function(){}, removeEventListener: function(){}\n});\n\nvar window;\nwindow = __mkObj(\'window\', {\n  document: document,\n  __DDG_BE_VERSION__: 1, __DDG_FE_CHAT_HASH__: 1,\n  navigator: __mkObj(\'navigator\', { userAgent: __ua, webdriver: false, language: \'en-US\', languages: [\'en-US\',\'en\'], platform: \'MacIntel\', vendor: \'Apple Computer, Inc.\', appVersion: \'5.0\', cookieEnabled: true, onLine: true, hardwareConcurrency: 8, deviceMemory: 8 }),\n  innerWidth: 1280, innerHeight: 800, outerWidth: 1280, outerHeight: 800, devicePixelRatio: 1,\n  screen: __mkObj(\'screen\', { width:1920, height:1080, availWidth:1920, availHeight:1080, colorDepth:24, pixelDepth:24 }),\n  location: __mkObj(\'location\', { href:\'https://duckduckgo.com/\', origin:\'https://duckduckgo.com\', host:\'duckduckgo.com\', hostname:\'duckduckgo.com\', protocol:\'https:\', pathname:\'/\', search:\'\', hash:\'\', port:\'\' }),\n  performance: __mkObj(\'perf\', { now: function(){ return 0; }, timeOrigin: 0 }),\n  history: __mkObj(\'history\', { length: 1, state: null }),\n  localStorage: __mkObj(\'ls\', { getItem:function(){return null;}, setItem:function(){}, removeItem:function(){}, clear:function(){}, length:0, key:function(){return null;} }),\n  sessionStorage: __mkObj(\'ss\', { getItem:function(){return null;}, setItem:function(){}, removeItem:function(){}, clear:function(){}, length:0, key:function(){return null;} }),\n  addEventListener: function(){}, removeEventListener: function(){}, dispatchEvent: function(){return true;},\n  getComputedStyle: function(el){\n    var css = (el && el.style && el.style.cssText) || \'\';\n    return {\n      getPropertyValue: function(p){\n        var m = css.match(new RegExp(p + \'\\\\s*:\\\\s*([^;]+)\', \'i\'));\n        if (m) return m[1].trim();\n        if (p === \'display\') return \'block\';\n        return \'\';\n      },\n      display: (css.match(/display\\s*:\\s*([^;]+)/i)||[])[1]||\'block\'\n    };\n  },\n  setTimeout: function(fn){ try{fn();}catch(e){} return 0; }, clearTimeout: function(){},\n  setInterval: function(){ return 0; }, clearInterval: function(){},\n  requestAnimationFrame: function(fn){ try{fn();}catch(e){} return 0; }, cancelAnimationFrame: function(){},\n  matchMedia: function(){ return __mkObj(\'mq\', {matches:false, media:\'\', addListener:function(){}, removeListener:function(){}, addEventListener:function(){}, removeEventListener:function(){}}); },\n  hasOwnProperty: function(k){\n    if (k===\'__DDG_BE_VERSION__\'||k===\'__DDG_FE_CHAT_HASH__\') return true;\n    return Object.prototype.hasOwnProperty.call(this,k);\n  },\n  alert: function(){}, confirm: function(){return true;}, prompt: function(){return \'\';},\n  open: function(){return null;}, close: function(){}, focus: function(){}, blur: function(){}\n});\nwindow.top = window; window.self = window; window.window = window; window.parent = window; window.globalThis = window;\nvar top = window, self = window, parent = window;\nvar navigator = window.navigator;\nvar location = window.location;\nvar screen = window.screen;\nvar performance = window.performance;\nvar history = window.history;\nvar localStorage = window.localStorage;\nvar sessionStorage = window.sessionStorage;\nvar getComputedStyle = function(el){ return window.getComputedStyle(el); };\nvar __R = null, __E = null;\nfunction __HTMLClass(name){ var c = function(){}; c.prototype = __mkObj(name+\'.proto\'); return c; }\nvar HTMLElement = __HTMLClass(\'HTMLElement\');\nvar HTMLDivElement = __HTMLClass(\'HTMLDivElement\');\nvar HTMLIFrameElement = __HTMLClass(\'HTMLIFrameElement\');\nvar HTMLDocument = __HTMLClass(\'HTMLDocument\');\nvar Document = __HTMLClass(\'Document\');\nvar Element = __HTMLClass(\'Element\');\nvar Node = __HTMLClass(\'Node\');\nvar Window = __HTMLClass(\'Window\');\nvar Event = __HTMLClass(\'Event\');\nvar MouseEvent = __HTMLClass(\'MouseEvent\');\nvar KeyboardEvent = __HTMLClass(\'KeyboardEvent\');\nvar TouchEvent = __HTMLClass(\'TouchEvent\');\nvar XMLHttpRequest = __HTMLClass(\'XMLHttpRequest\');\nvar WebSocket = __HTMLClass(\'WebSocket\');\nvar Image = __HTMLClass(\'Image\');\nvar FormData = __HTMLClass(\'FormData\');\nvar Blob = __HTMLClass(\'Blob\');\nvar File = __HTMLClass(\'File\');\nvar FileReader = __HTMLClass(\'FileReader\');\nvar URL = __HTMLClass(\'URL\');\nvar URLSearchParams = __HTMLClass(\'URLSearchParams\');\nvar Headers = __HTMLClass(\'Headers\');\nvar Request = __HTMLClass(\'Request\');\nvar Response = __HTMLClass(\'Response\');\nvar fetch = function(){ return Promise.resolve(__mkObj(\'resp\', {ok:true, status:200, json:function(){return Promise.resolve({});}, text:function(){return Promise.resolve(\'\');}})); };\n'
    R.DUCK_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.DUCK_WARMED = [False]
    R.FLA_AJAX = 'https://flatai.org/wp-admin/admin-ajax.php'
    R.G4F_BASE = 'https://g4f.space'
    R.G4F_LIMIT = {'until': 0.0}
    R.GK_BASE = 'https://www.gadegetkit.com'
    R.GK_LIMIT = {'until': 0.0}
    R.GK_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.HB_BASE = 'https://www.hotbot.com'
    R.HB_LIMIT = {'until': 0.0}
    R.HB_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.HF_BASE = 'https://router.huggingface.co/v1'
    R.HF_LIMIT = {'until': 0.0}
    R.HK_BASE = 'https://api.heckai.weight-wave.com/api/ha/v1'
    R.HK_CATALOG = [('deepseek/deepseek-v4-flash', 'DeepSeek v4 Flash'), ('deepseek/deepseek-v4-pro', 'DeepSeek v4 Pro'), ('tencent/hy3-preview', 'Tencent Hy3 Preview'), ('qwen/qwen3.7-plus', 'Qwen 3.7 Plus'), ('stepfun/step-3.7-flash', 'Step 3.7 Flash'), ('google/gemini-3.1-flash-lite', 'Gemini 3.1 Flash Lite'), ('google/gemini-3-flash-preview', 'Gemini 3.0 Flash'), ('openai/gpt-5.4-mini', 'GPT 5.4 mini'), ('minimax/minimax-m3', 'Minimax M3'), ('anthropic/claude-opus-4.8', 'Claude Opus 4.8')]
    R.HK_LIMIT = {'until': 0.0}
    R.HK_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.L7_BASE = 'https://api.llm7.io/v1'
    R.L7_FALLBACK = [('codestral-latest', 'Codestral'), ('mistral-Nemo-Instruct-2407', 'Mistral Nemo'), ('minimax-m2.7', 'MiniMax M2.7'), ('GLM-5.3-Flash', 'GLM 5.3 Flash')]
    R.L7_LIMIT = {'until': 0.0}
    R.MC_ACC_DAY = 45
    R.MC_API = 'https://www.multichats.ai/api/chat'
    R.MC_CONVEX = 'https://wary-cuttlefish-113.convex.cloud/api/action'
    R.MC_MODELS = [('gpt-5.4-nano', 'GPT-5.4 Nano'), ('gemini-3.1-flash-lite', 'Gemini 3.1 Flash Lite'), ('gemini-2.5-flash', 'Gemini 2.5 Flash'), ('openai/gpt-oss-120b:exacto', 'GPT-OSS 120B'), ('meta-llama/llama-4-maverick', 'Llama 4 Maverick'), ('mistralai/mistral-small-3.2-24b-instruct', 'Mistral Small 3.2'), ('mistralai/mistral-small-2603', 'Mistral Small 2603')]
    R.MC_ST = {'accounts': [], 'idx': 0, 'signups': {'date': '', 'n': 0}}
    R.NG_LIMIT = {'until': 0.0}
    R.PIA_AGENTS = [('32', 'gpt-4.1-nano', 'GPT 4.1 Nano'), ('33', 'o3-mini', 'o3 Mini'), ('167', 'deepseek-v3.2', 'DeepSeek V3.2'), ('136', 'glm-4.7', 'GLM 4.7'), ('163', 'kimi-k2.5', 'Kimi K2.5'), ('175', 'minimax-m3', 'MiniMax M3')]
    R.PI_BASE = 'https://pi.ai'
    R.PI_LIMIT = {'until': 0.0}
    R.PI_STATE = {'s': None, 'did': None}
    R.PI_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.QB_URL = 'https://quillbot.com/api/ai-chat/chat/conversation/'
    R.YL_BASE = 'https://www.yollo.ai'
    R.YL_BOT = 147747
    R.YL_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R.Z02_API = 'https://api.zerotwo.ai'
    R.Z02_SB = 'https://jdbcevjbqaoxrxxwqwux.supabase.co'
    R._ACT_STATE = {'i': 0}
    R._AKA = {'ses': None, 't': 0.0}
    R._AKA_CHARS = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    R._AKA_NEUTRAL = "You are a helpful assistant. Follow the user's instructions precisely."
    R._CBC_KEY_TOKEN = 'XXXXXXYYY'
    R._CBC_PROXY = {'on': True}
    R._CBC_STATE = {'csrf': None, 'cookies': None, 't': 0.0}
    R._CBOX_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R._CT_E = 65537
    R._CT_FALLBACK = [('gpt-5.6-luna', 'GPT 5.6 Luna')]
    R._HK = {'sid': '', 't': 0.0}
    R._MC_HIH = {'tok': '', 'ts': 0}
    R._MERGE_SUFFIXES = ('-orbio', '-0731', '-0813', '-preview')
    R._PIA_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36'
    R._UA_STICK = {}
    R._YL = {'tok': '', 'sid': '', 'finger': '', 't': 0.0}
    R._Z02_CACHE = {'token': None, 'exp': 0.0}
    R._Z02_PROVIDERS = {'gemini-2.5-flash-lite': 'gemini', 'grok-4-1-fast-non-reasoning': 'xai', 'gpt-5.6-luna': 'openai', 'venice-uncensored-role-play': 'venice'}
    R.DUCK_LOCK = threading.Lock()
    R.MC_LOCK = threading.Lock()
    R.CBOX_LOCK = threading.Lock()
    R.AIML_ACC_FILE = "/tmp/vpx_aiml.json"
    R.MC_ACC_FILE = "/tmp/vpx_mc.json"
    R.MC_HIH_FILE = "/tmp/vpx_mc_hih.json"
    R.CBOX_ACC_FILE = "/tmp/vpx_cbox.json"

    R.MC_TARGET = 1100
    R.MC_COOL_429 = 420
    R._CT_N = int("c201d7ff13221b2c1c631aa9a1eea2d4ebf08f0b3aeefbbe7ef363923d9fa77f8045be0f3c76ba59e8a8a0356d09f13360c5ee989acd62ac264d543caef915ec978cbfedcd8a3877383864f31c1e5f50c88c6ac154bdc12cd8fef47bac80fec28765f04b1b55cf8656fce086ecde7843dd6e5ed92b82fb812e5646aaccdd3c2d", 16)

    R.Z02_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpkYmNldmpicWFveHJ4eHdxd3V4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTgyNDcyMzUsImV4cCI6MjA3MzgyMzIzNX0.UcUJUjMocwijFTtYFKYuTgIODYWc4uxDByu2tI6XGQg'

    R.DUCK_SESSION = None

    R._G4F_CREDIT = {'v': 0}
    R._G4F_BAKE_LOCK = threading.Lock()


    R.MC_DAILY_CAP = 800

    R.CB_CMS = 'https://webcms.chatbotapp.ai/api/ai-models?populate[]=tags&populate[]=examples&populate[]=suggestions&pagination[pageSize]=100'
    R.CB_FREE_BOTS = {104: '4o-mini', 107: 'gpt-4.1-mini', 113: 'gpt-5.1', 117: 'gpt-5.4-mini', 200: 'gemini-2.5-flash', 202: 'gemini-3-flash', 204: 'gemini-3.1-flash-lite', 301: 'deepSeek', 302: 'deepseek-v4-flash', 502: 'claude-4.5-haiku'}
    R.CB_HTTP400_BOTS = {123, 115, 501, 14}
    R.CB_SKIP_KEYS = {'logo-generator', 'tattoo-generator', 'youtube-summarizer', 'link-and-ask', 'aiapp', 'image-generator', 'ai-search', 'document', 'editor', 'superbot', 'music-generation', 'chatbotapp'}
    R._CB_SYNC = {'t': 0.0}
    R.NV_CMS = 'https://webcms.novaapp.ai/api/ai-models?populate[]=tags&populate[]=examples&populate[]=suggestions&pagination[pageSize]=100'
    R.NV_FREE_BOTS = {0: '4o-mini', 9: 'auto', 10: 'gemini-2.5-flash', 15: 'claude', 21: 'deepSeek', 26: 'gpt-4.1', 44: 'claude-4.5-haiku', 49: 'gpt-5.1', 100: 'gemini-3-flash', 108: 'gpt-5.6-luna', 111: 'deepseek-v4-flash'}
    R.NV_SKIP_KEYS = {'logo-generator', 'tattoo-generator', 'youtube-summarizer', 'link-and-ask', 'aiapp', 'image-generator', 'ai-search', 'document', 'nova', 'editor', 'superbot', 'music-generation', 'chatbotapp'}
    R.NV_HTTP400_BOTS = {5, 201, 45, 403, 23}
    R._NV_SYNC = {'t': 0.0}
    R._CA_SYNC = {'t': 0.0}
    R._AC_SYNC = {'t': 0.0}
    R._AIML_SYNC = {'t': 0.0}
    R._AL_SYNC = {'t': 0.0}
    R._CT_SYNC = {'t': 0.0}
    R._GK_SYNC = {'t': 0.0}
    R._HB_SYNC = {'t': 0.0}
    R._HF_SYNC = {'t': 0.0}
    R._PI_SYNC = {'t': 0.0}
    R.MS_T = {'duck': 0.0, 'ak': 0.0, 'l7': 0.0, 'ct': 0.0, 'yl': 0.0, 'hk': 0.0, 'hf': 0.0, 'aka': 0.0, 'hb': 0.0, 'gk': 0.0, 'gz': 0.0, 'pi': 0.0, 'cb': 0.0, 'ac': 0.0, 'nv': 0.0, 'al': 0.0}
    R.MS_LOCK = threading.Lock()

    R._CT_ARR_RE = re.compile(r'\[\{name:"[^"]{1,50}",value:"[^"]{1,50}"\}(?:,\{name:"[^"]{1,50}",value:"[^"]{1,50}"\}){0,30}\]')
    R._CT_VAL_RE = re.compile(r'\{name:"([^"]{1,50})",value:"([^"]{1,50})"\}')

    R.ALLE_SHARE = "4df75c05-26a6-4be6-aa6f-5758e1c5206c"
    R.HF_TOKEN = "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"
    R.NODE_BIN = "node"
    R.AK_CLIENT = ""

    R._FB_BLOCK = ('TOO_MANY_ATTEMPTS_TRY_LATER', 'OPERATION_NOT_ALLOWED', 'QUOTA_EXCEEDED', 'RESOURCE_EXHAUSTED')
    R._FB_DIRECT_BAD = {}

    return R

"""
classic_rules.py — Industry-Standard Classic Vulnerability Rules
================================================================
AST-based detection for the mainstream OWASP/CWE vulnerability classes that real
SAST tools (Bandit, Semgrep, CodeQL) cover — so Q-Trace is not only a
logic-bomb/obfuscation auditor but a complete Python security scanner.

Every rule is written to fire on a genuine *interpolation / dynamic / unsafe*
construct and stay quiet on the parameterised/constant-safe form, keeping false
positives low (each rule is paired with safe-variant tests in test_qtrace.py).

Coverage:
  CWE-89  SQL injection            CWE-78  command injection (shell=True/tainted)
  CWE-502 insecure deserialization CWE-798 hard-coded credentials
  CWE-327 weak hash / weak cipher  CWE-330 insufficiently random values
  CWE-918 SSRF                     CWE-22  path traversal
  CWE-295 disabled TLS validation  CWE-611 XXE
  CWE-377 insecure temp file       CWE-489 debug mode in production
  CWE-319 cleartext transmission
"""
from __future__ import annotations

import ast
import re
from typing import List

from findings import Finding, get_meta

# Names that strongly imply a secret when assigned a literal.
_SECRET_NAME = re.compile(
    r"(?i)(pass(word|wd)?|secret|api[_-]?key|access[_-]?key|auth[_-]?token|"
    r"token|credential|private[_-]?key|client[_-]?secret)")
_SECRETish_VALUE_OK = {"", "changeme", "password", "xxx", "none", "example",
                       "your-password", "test", "todo", "placeholder"}
_RANDOM_SECRET_NAME = re.compile(r"(?i)(token|secret|key|password|nonce|otp|salt|session)")
_WEAK_HASHES = {"md5", "md4", "sha1"}
_WEAK_CIPHERS = {"DES", "DES3", "ARC4", "RC4", "Blowfish", "XOR"}
_HTTP_LIBS_URL_ARG = {"get", "post", "put", "delete", "patch", "head", "request", "urlopen"}


def _attr_chain(node: ast.AST) -> str:
    """Return a dotted name for Name/Attribute chains (e.g. 'os.path.join')."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def _is_interpolated_str(node: ast.AST) -> bool:
    """True if node builds a string via f-string, %, +concat, or .format()."""
    if isinstance(node, ast.JoinedStr):  # f-string with a substitution
        return any(isinstance(v, ast.FormattedValue) for v in node.values)
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Mod, ast.Add)):
        return _contains_dynamic(node)
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) \
            and node.func.attr == "format":
        return True
    return False


def _contains_dynamic(node: ast.AST) -> bool:
    """True if the subtree references a variable/call (not purely constant)."""
    for n in ast.walk(node):
        if isinstance(n, (ast.Name, ast.Call, ast.Attribute, ast.Subscript,
                          ast.FormattedValue)):
            return True
    return False


def _is_dynamic_arg(node: ast.AST) -> bool:
    if isinstance(node, ast.Constant):
        return False
    return True


def _kw(call: ast.Call, name: str):
    for k in call.keywords:
        if k.arg == name:
            return k.value
    return None


class ClassicRuleVisitor(ast.NodeVisitor):
    def __init__(self, code: str):
        self.code = code
        self.lines = code.splitlines()
        self.hits: List[tuple] = []  # (rule_key, line, confidence, evidence)

    def _add(self, rule_key, node, confidence, evidence):
        self.hits.append((rule_key, getattr(node, "lineno", 1), confidence, evidence))

    # --- Assignments: secrets, insecure randomness -----------------------
    def visit_Assign(self, node: ast.Assign):
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        # Hard-coded credentials (CWE-798)
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            val = node.value.value
            for nm in names:
                if _SECRET_NAME.search(nm) and len(val) >= 6 \
                        and val.strip().lower() not in _SECRETish_VALUE_OK \
                        and not val.startswith("${") and "os.environ" not in val:
                    self._add("HARDCODED_SECRET", node, "Medium",
                              f"`{nm}` assigned a hard-coded string literal")
                    break
        # Insecure randomness for a secret-looking target (CWE-330)
        if any(_RANDOM_SECRET_NAME.search(n) for n in names):
            for sub in ast.walk(node.value):
                if isinstance(sub, ast.Call) and _attr_chain(sub.func).startswith("random."):
                    self._add("INSECURE_RANDOM", node, "Medium",
                              "non-cryptographic random used for a secret/token")
                    break
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        name = _attr_chain(node.func)
        short = node.func.attr if isinstance(node.func, ast.Attribute) else \
            (node.func.id if isinstance(node.func, ast.Name) else "")

        # SQL injection (CWE-89): cursor.execute(f"... {x} ...")
        if short in {"execute", "executemany", "executescript"} and node.args:
            if _is_interpolated_str(node.args[0]):
                self._add("SQL_INJECTION", node, "High",
                          "interpolated string passed to SQL execute()")

        # Command injection (CWE-78)
        if name in {"subprocess.call", "subprocess.run", "subprocess.Popen",
                    "subprocess.check_output", "subprocess.check_call"} or \
           short in {"call", "run", "Popen", "check_output", "check_call"}:
            shell = _kw(node, "shell")
            if isinstance(shell, ast.Constant) and shell.value is True:
                conf = "High" if (node.args and _is_dynamic_arg(node.args[0])) else "Medium"
                self._add("COMMAND_INJECTION", node, conf, "subprocess called with shell=True")
        if name in {"os.system", "os.popen"} and node.args and _is_interpolated_str(node.args[0]):
            self._add("COMMAND_INJECTION", node, "High",
                      "interpolated command string passed to os.system/popen")

        # Insecure deserialization (CWE-502)
        if name in {"pickle.loads", "pickle.load", "cPickle.loads", "cPickle.load",
                    "marshal.loads", "marshal.load", "dill.loads", "dill.load",
                    "shelve.open"}:
            self._add("INSECURE_DESERIALIZATION", node, "High",
                      f"untrusted deserialization via {name}")
        if name in {"yaml.load"}:
            loader = _kw(node, "Loader")
            safe = isinstance(loader, ast.Attribute) and loader.attr in {"SafeLoader", "CSafeLoader"}
            if not safe:
                self._add("INSECURE_DESERIALIZATION", node, "High",
                          "yaml.load() without SafeLoader")

        # Weak hashing (CWE-327)
        if name in {"hashlib.md5", "hashlib.sha1", "hashlib.md4"} or \
           (name == "hashlib.new" and node.args and isinstance(node.args[0], ast.Constant)
                and str(node.args[0].value).lower() in _WEAK_HASHES):
            ufs = _kw(node, "usedforsecurity")
            if not (isinstance(ufs, ast.Constant) and ufs.value is False):
                self._add("WEAK_HASH", node, "Medium",
                          "broken/weak hash algorithm for security use")

        # Disabled TLS validation (CWE-295)
        verify = _kw(node, "verify")
        if isinstance(verify, ast.Constant) and verify.value is False:
            self._add("DISABLED_CERT_VALIDATION", node, "High",
                      "TLS certificate verification disabled (verify=False)")
        if name in {"ssl._create_unverified_context"}:
            self._add("DISABLED_CERT_VALIDATION", node, "High",
                      "unverified SSL context created")

        # SSRF (CWE-918): requests/urlopen with a dynamic URL
        if short in _HTTP_LIBS_URL_ARG and node.args and _is_dynamic_arg(node.args[0]) \
                and ("request" in name or "urlopen" in name or name.startswith("requests.")
                     or name.startswith("httpx.") or name.startswith("urllib")):
            self._add("SSRF", node, "Low", "outbound request to a non-constant URL")

        # Cleartext transmission (CWE-319)
        if short in _HTTP_LIBS_URL_ARG and node.args and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str) and node.args[0].value.startswith("http://") \
                and "localhost" not in node.args[0].value and "127.0.0.1" not in node.args[0].value:
            self._add("CLEARTEXT_TRANSMISSION", node, "Low", "request over cleartext http://")

        # Path traversal (CWE-22): open() with an interpolated/tainted path
        if name == "open" or short == "open":
            if node.args and (_is_interpolated_str(node.args[0])
                              or (isinstance(node.args[0], ast.Constant)
                                  and isinstance(node.args[0].value, str)
                                  and ".." in node.args[0].value)):
                self._add("PATH_TRAVERSAL", node, "Low", "file path built from dynamic input")

        # XXE (CWE-611): xml parsing of potentially untrusted input.
        # defusedxml is the hardened drop-in -> never flag when it is in use.
        if "defusedxml" not in self.code and name in {
                "xml.etree.ElementTree.parse", "xml.etree.ElementTree.fromstring",
                "etree.parse", "etree.fromstring", "ET.parse", "ET.fromstring",
                "xml.dom.minidom.parse", "xml.sax.parse"}:
            self._add("XXE", node, "Low", "XML parsed without an XXE-hardened parser")

        # Insecure temp file (CWE-377)
        if name in {"tempfile.mktemp"}:
            self._add("INSECURE_TEMP_FILE", node, "Medium", "tempfile.mktemp() is race-prone")

        # Debug mode in production (CWE-489)
        if short == "run":
            debug = _kw(node, "debug")
            if isinstance(debug, ast.Constant) and debug.value is True:
                self._add("DEBUG_ENABLED", node, "Medium", "web app started with debug=True")

        self.generic_visit(node)

    # --- weak cipher via `from Crypto.Cipher import DES` -----------------
    def visit_ImportFrom(self, node: ast.ImportFrom):
        module = node.module or ""
        if any(lib in module for lib in ("Crypto", "Cryptodome", "cryptography")):
            for alias in node.names:
                if alias.name in _WEAK_CIPHERS:
                    self._add("WEAK_CIPHER", node, "Medium", f"weak cipher {alias.name} imported")
        self.generic_visit(node)

    # --- weak cipher via attribute access (e.g. Crypto.Cipher.DES) -------
    def visit_Attribute(self, node: ast.Attribute):
        if node.attr in _WEAK_CIPHERS:
            chain = _attr_chain(node)
            if any(lib in chain for lib in ("Crypto", "Cryptodome", "cryptography", "Cipher")):
                self._add("WEAK_CIPHER", node, "Medium", f"weak cipher {node.attr}")
        self.generic_visit(node)


def _snippet(code_lines, line):
    return code_lines[line - 1].strip() if 1 <= line <= len(code_lines) else ""


def scan_classic(code: str) -> List[Finding]:
    """Return classic-vulnerability findings (empty on parse error)."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []
    v = ClassicRuleVisitor(code)
    v.visit(tree)
    findings: List[Finding] = []
    for rule_key, line, confidence, evidence in v.hits:
        meta = get_meta(rule_key)
        findings.append(Finding(
            pattern=rule_key, meta=meta, confidence=confidence,
            risk_score=_risk_for(meta.severity), line=line, column=1,
            snippet=_snippet(v.lines, line), evidence=[evidence],
        ))
    return findings


def _risk_for(severity: str) -> float:
    return {"Critical": 0.9, "High": 0.75, "Medium": 0.5, "Low": 0.3, "Info": 0.1}.get(severity, 0.4)


if __name__ == "__main__":
    demo = (
        "import subprocess, hashlib, pickle, requests\n"
        "password = 'hunter2secret'\n"
        "cur.execute(f'SELECT * FROM u WHERE n={name}')\n"
        "subprocess.run(cmd, shell=True)\n"
        "hashlib.md5(data)\n"
        "pickle.loads(blob)\n"
        "requests.get(url, verify=False)\n"
    )
    for f in scan_classic(demo):
        print(f"[{f.severity:8s}/{f.confidence:6s}] {f.meta.cwe} {f.meta.title} @ line {f.line}")

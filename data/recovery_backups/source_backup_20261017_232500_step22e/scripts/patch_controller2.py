import re

def main():
    with open('app/controller/controller.py', 'r') as f:
        code = f.read()

    if 'import time' not in code:
        code = 'import time\n' + code

    # 1. Signature update for _stage
    code = code.replace(
        'metadata: Optional[Dict[str, Any]] = None,\n    ) -> ControllerStageResult:',
        'metadata: Optional[Dict[str, Any]] = None,\n        latency_seconds: float = 0.0,\n    ) -> ControllerStageResult:'
    )
    code = code.replace(
        'metadata=metadata or {},\n        )',
        'metadata=metadata or {},\n            latency_seconds=latency_seconds,\n        )'
    )

    # 2. Add local timer to run()
    code = code.replace(
        'def run(self, request: ControllerRequest) -> ControllerResult:\n        stages: List[ControllerStageResult] = []',
        'def run(self, request: ControllerRequest) -> ControllerResult:\n        stages: List[ControllerStageResult] = []\n        _t0 = time.time()'
    )

    # 3. We will find every block that appends to stages, and inject _t1 computation, pass latency_seconds, and update _t0.
    
    # Let's match stages.append( ... self._stage( ... ) )
    
    def replacer(match):
        text = match.group(0)
        # inject latency_seconds before the closing bracket of self._stage
        # find the last closing parenthesis
        idx = text.rfind(')')
        idx2 = text.rfind(')', 0, idx)
        
        # text is like:
        # stages.append(
        #     self._stage(
        #         ...
        #     )
        # )
        
        inner = text[:idx2] + ',\n                    latency_seconds=time.time() - _t0,\n                ' + text[idx2:]
        return inner + '\n            _t0 = time.time()'
    
    # Need a regex that captures stages.append( ... self._stage( ... ) )
    # It might span multiple lines.
    pattern = r'stages\.append\(\s*self\._stage\((?:[^)(]+|\((?:[^)(]+|\([^)(]*\))*\))*\)\s*\)'
    
    code, count = re.subn(pattern, replacer, code)
    print(f"Replaced {count} occurrences of stages.append")

    with open('app/controller/controller.py', 'w') as f:
        f.write(code)

if __name__ == "__main__":
    main()

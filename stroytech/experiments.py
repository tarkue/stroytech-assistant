"""Reproducible small synthetic corpus evaluation; no fabricated measurements."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import time
from .extraction import ExtractionError, PROMPT_VERSION, extract_rules
from .config import load_settings


def _signature(rule):
    # Exact rule semantics: conjunction/effect ordering ignored, labels ignored.
    def canonical(items):
        return sorted(json.dumps(item,ensure_ascii=False,sort_keys=True,separators=(',',':')) for item in items)
    return json.dumps([canonical(rule['conditions']),canonical(rule['effects'])],ensure_ascii=False)


def score_rules(predicted, gold):
    """Set exact-match: textual effect values are compared exactly, NOT semantically graded.

    Empty/empty gets 1; precision of empty predictions with nonempty gold is 0.
    Errors are passed as [] by the runner, hence false negatives remain counted.
    """
    actual={_signature(rule) for rule in predicted}
    expected={_signature(rule) for rule in gold}
    tp=len(actual & expected); fp=len(actual-expected); fn=len(expected-actual)
    precision=tp/len(actual) if actual else float(not expected)
    recall=tp/len(expected) if expected else float(not actual)
    return dict(tp=tp,fp=fp,fn=fn,precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0)


def run_experiment(corpus_path, output_dir, *, model=None, provider=None, limit=None, timeout=None):
    settings=load_settings(provider,model=model,timeout=timeout)
    model,provider,timeout=settings.model,settings.provider,settings.timeout
    corpus_bytes=Path(corpus_path).read_bytes()
    cases=json.loads(corpus_bytes)['cases']
    if limit is not None: cases=cases[:limit]
    output=Path(output_dir); output.mkdir(parents=True,exist_ok=True)
    records=[]
    for pipeline in ('filter_first','extract_first'):
        for case in cases:
            transcript=[]; start=time.monotonic(); predicted=[]; error=None
            try:
                predicted=extract_rules(case['text'],model,pipeline,provider=provider,timeout=timeout,transcript=transcript)
            except ExtractionError as exc:
                error=str(exc)
            record=dict(case_id=case['id'],pipeline=pipeline,predicted=predicted,gold=case['gold'],error=error,elapsed_seconds=round(time.monotonic()-start,3),transcript=transcript,metrics=score_rules(predicted,case['gold']))
            records.append(record)
            (output/(pipeline+'-'+case['id']+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding='utf-8')
    summaries={}
    for pipeline in ('filter_first','extract_first'):
        selected=[record for record in records if record['pipeline']==pipeline]
        tp=sum(r['metrics']['tp'] for r in selected); fp=sum(r['metrics']['fp'] for r in selected); fn=sum(r['metrics']['fn'] for r in selected)
        precision=tp/(tp+fp) if tp+fp else float(not fn)
        recall=tp/(tp+fn) if tp+fn else float(not fp)
        summaries[pipeline]=dict(cases=len(selected),errors=sum(r['error'] is not None for r in selected),tp=tp,fp=fp,fn=fn,precision=precision,recall=recall,f1=2*precision*recall/(precision+recall) if precision+recall else 0,seconds=sum(r['elapsed_seconds'] for r in selected),
            usable_outputs=sum(r['error'] is None for r in selected),
            usable_positive_outputs=sum(r['error'] is None and bool(r['predicted']) for r in selected),
            exact_cases=sum(r['error'] is None and r['metrics']['fp']==0 and r['metrics']['fn']==0 for r in selected),
            negative_cases=sum(not r['gold'] for r in selected),
            negative_correct=sum(not r['gold'] and r['error'] is None and not r['predicted'] for r in selected),
            negative_errors=sum(not r['gold'] and r['error'] is not None for r in selected),
            negative_false_positives=sum(not r['gold'] and bool(r['predicted']) for r in selected))
    try:
        if provider!='ollama': raise OSError()
        version=subprocess.run(['ollama','--version'],capture_output=True,text=True,timeout=5).stdout.strip()
        installed=subprocess.run(['ollama','list'],capture_output=True,text=True,timeout=5).stdout.strip()
    except (OSError,subprocess.TimeoutExpired):
        version=installed='unavailable'
    result=dict(created_at=datetime.now(timezone.utc).isoformat(),provider=provider,model=model,ollama_version=version,installed_models=installed,prompt_version=PROMPT_VERSION,corpus_sha256=hashlib.sha256(corpus_bytes).hexdigest(),limitation='Small manually annotated synthetic corpus, not an independent benchmark. Exact text effect matching is conservative; errors on nonempty gold count as missed gold rules; errors on empty gold are NOT correct negative inference. Report usable_outputs, exact_cases, negative_correct and errors alongside F1.',summaries=summaries)
    (output/'summary.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--corpus',default='data/extraction_cases.json')
    parser.add_argument('--output',default='work/experiments')
    parser.add_argument('--limit',type=int)
    parser.add_argument('--timeout',type=float)
    parser.add_argument('--model')
    parser.add_argument('--provider',choices=['ollama','openrouter'])
    args=parser.parse_args()
    print(json.dumps(run_experiment(args.corpus,args.output,model=args.model,provider=args.provider,limit=args.limit,timeout=args.timeout),ensure_ascii=False,indent=2))


if __name__=='__main__': main()

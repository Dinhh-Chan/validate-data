"""Build the folder TRUONG_HOP_SAI/: one folder per logging tool with the cases where the tool's OWN evaluation metric
misjudges the tool's OWN outputs, plus an overview. Everything is rendered from the rescored data, nothing is copied by
hand. Re-run after any rescoring:  python build.py"""
import collections, csv, json, re, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
EXT = HERE.parent/'external_methods'
LCS = HERE.parent/'logging_condition_study'
PDL = HERE.parent/'pdlogger_repro'
sys.path.insert(0, str(EXT))
from analyze_external import lvl, msg

fam = lambda vd: ('A1' if vd.startswith('wrong_condition') else 'A2' if vd == 'invalid'
                  else 'A3' if vd in ('order_changed', 'value_changed', 'log_order_changed') else 'OK')
VERDICT_VI = {'same_point': 'đúng y vị trí', 'equivalent_move': 'lệch nhưng tương đương', 'invalid': 'không chạy được',
              'wrong_condition:weaker': 'in quá thường (mất điều kiện)', 'wrong_condition:stronger': 'in quá ít / sai phạm vi (thừa điều kiện)',
              'wrong_condition:disjoint': 'nhầm nhánh (không bao giờ cùng in)', 'wrong_condition:overlapping': 'điều kiện khác',
              'order_changed': 'vượt qua một thao tác', 'value_changed': 'giá trị biến được in đã đổi', 'log_order_changed': 'đổi thứ tự với log khác'}

# ----------------------------------------------------------------------------------------------------- types
TYPES = [
    ('T1', 'Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC',
     'Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log '
     'không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau).', 'ER'),
    ('T2', 'Metric cộng điểm level / message cho log IN SAI LÚC',
     'Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** '
     'với log của developer: in quá thường, quá ít, nhầm nhánh.', 'CA'),
    ('T3', 'Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan)',
     'Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí '
     'không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương.', 'RPA'),
    ('T4', 'Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán)',
     'Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi '
     'vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold.', 'CA (chẩn đoán)'),
    ('T5', 'Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được)',
     'Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này '
     'là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính.', 'RPA'),
]
TNAME = {t[0]: t[1] for t in TYPES}


def classify(r, metric='exact'):
    """Types for one rescored instance of an exact-match tool."""
    out = []
    lo, mo = r['lvl_ok'], r['msg_ok']
    if r['verdict'] == 'invalid' and (r['same_point'] or lo or mo): out.append('T1')
    if fam(r['verdict']) == 'A1' and (lo or mo): out.append('T2')
    if not r['same_point'] and r['rpa']: out.append('T3')
    if not r['same_point'] and not r['rpa']: out.append('T4')
    if fam(r['verdict']) == 'A3' and lo and mo: out.append('T5')
    return out


def load(key):
    rows = [json.loads(l) for l in (EXT/key/'rescored.jsonl').open()]
    for r in rows:
        if r['status'] == 'ok':
            r['lvl_ok'] = lvl(r['gold']) is not None and lvl(r['gold']) == lvl(r['pred'])
            r['msg_ok'] = msg(r['gold']) == msg(r['pred'])
            r['types'] = classify(r)
    return rows


def code(r, maxw=160):
    L = r['code'].splitlines(); out = []
    for j, l in enumerate(L + ['']):
        if j == r['gold_line']: out.append('G>  ' + r['gold'])
        if j == r['pred_line']: out.append('P>  ' + r['pred'])
        if j < len(L): out.append('    ' + (l if l.strip() else '// «dòng trống benchmark để lại ở chỗ log bị xoá»')[:maxw])
    return '```java\n' + '\n'.join(out) + '\n```'


def their(r, pos_name):
    pos = 'đúng' if r['same_point'] else 'sai'
    return (f'vị trí **{pos}** ({pos_name}) · level **{"đúng" if r["lvl_ok"] else "sai"}** · '
            f'message **{"đúng" if r["msg_ok"] else "sai"}** (khớp chính xác)')


def example(r, title, why, pos_name):
    return '\n'.join([f'#### {title} (mẫu `{r["id"]}`)', '',
                      'Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.', '',
                      code(r), '',
                      f'- **Metric của công cụ chấm:** {their(r, pos_name)}',
                      f'- **Verifier của mình:** `{r["verdict"]}` ({VERDICT_VI.get(r["verdict"], "")}) · CA {int(r["ca"])} · ER {int(r["er"])} · RPA {int(r["rpa"])}',
                      f'- **Vì sao metric chấm sai:** {why}', ''])


def write_cases_csv(folder, rows):
    (folder/'cases').mkdir(parents=True, exist_ok=True)
    for t, *_ in TYPES:
        sel = [r for r in rows if r['status'] == 'ok' and t in r['types']]
        with (folder/'cases'/f'{t}.csv').open('w', newline='') as f:
            w = csv.writer(f)
            w.writerow(['id', 'verdict_verifier', 'giai_thich', 'vi_tri_khop_chinh_xac', 'level_dung', 'message_dung', 'CA', 'ER', 'RPA', 'gold_log', 'log_sinh_ra'])
            for r in sel:
                w.writerow([r['id'], r['verdict'], VERDICT_VI.get(r['verdict'], ''), int(r['same_point']), int(r['lvl_ok']), int(r['msg_ok']),
                            int(r['ca']), int(r['er']), int(r['rpa']), r['gold'], r['pred']])


ALB_PAPER = {'unilog_warmup_cl': ' (AL-Bench Table 2 báo cáo UniLog_cl PA 23,49%)', 'al_lance': ' (AL-Bench Table 2 báo cáo LANCE PA 35,97%, tính trên mọi mẫu)', 'al_leonid': ' (AL-Bench báo cáo LEONID_S PA 11,26%, tính trên mọi mẫu)', 'al_fastlog': ' (AL-Bench Table 2 báo cáo FastLog PA 58,39%)'}
EXPECTED = {'unilog_deepseek_base': 39600, 'unilog_warmup_cl': 39600}


# ------------------------------------------------------------------ raw input / prompt / output of each tool
def fence(lang, body): return f'```{lang}\n{(body or "").rstrip()}\n```'


def details(summary, body): return f'<details>\n<summary>{summary}</summary>\n\n{body}\n\n</details>'


class Raw:
    """Lazy access to the ORIGINAL files of each tool, by instance id."""
    def __init__(self): self.c = {}

    def get(self, key):
        if key in self.c: return self.c[key]
        d = EXT/key
        if key == 'lance':
            rows = list(csv.reader((d/'test.tsv').open(), delimiter='\t'))
            pr = (d/'predictions.txt').read_text().splitlines()
            val = dict(inp=[r[0] for r in rows], tgt=[r[1] for r in rows], out=pr)
        elif key in ('lance2', 'leonid'):
            val = dict(inp=(d/'inputs').read_text().splitlines(), tgt=(d/'targets').read_text().splitlines(),
                       out=(d/'predictions.txt').read_text().splitlines())
        elif key == 'fastlog':
            res = list(csv.DictReader((d/'results_beam_search.csv').open()))
            pos = list(csv.DictReader((d/'positions.csv').open()))
            st = list(csv.DictReader((d/'statements_beam_search.csv').open()))
            val = dict(inp=[r['Input'] for r in res], tgt=(d/'target.txt').read_text().splitlines(), out=[r['Prediction'] for r in res],
                       pos=[r['Pred_Position'] for r in pos], stmt=[r['LogStatement'] for r in st])
        elif key.startswith('unilog_'):
            var = key[len('unilog_'):]
            val = json.load((EXT/'albench'/'res_all'/'unilog'/var/f'static_test_data_{var}_cleaned.json').open())
        else:
            val = None
        self.c[key] = val
        return val


RAW = Raw()
csv.field_size_limit(10**9)
TOOL_KEY = {'LANCE': 'lance', 'LANCE_2.0': 'lance2', 'LEONID': 'leonid', 'FastLog': 'fastlog', 'UniLog': 'unilog_deepseek_base'}


def raw_io(tool, i):
    key = TOOL_KEY[tool]; R = RAW.get(key)
    if R is None: return ''
    if key.startswith('unilog_'):
        x = R[i]; q = x['prompt'].rsplit('<Query>:', 1)
        parts = [details('Prompt đầy đủ AL-Bench gửi cho UniLog (5 ví dụ mẫu + câu hỏi)', fence('text', x['prompt'])),
                 details('Input (phần <code>&lt;Query&gt;</code> của prompt: method đã xoá log, dòng có thẻ <code>&lt;lineN&gt;</code>)', fence('text', '<Query>:' + q[-1] if len(q) > 1 else x['prompt'])),
                 details('Output thô của UniLog và ground truth trong metadata', fence('text', f'response: {x.get("response")}\nmetadata (gold): {json.dumps(x["metadata"], ensure_ascii=False)}'))]
        return '\n\n'.join(parts)
    notes = {'lance': 'LANCE là model T5 fine-tune: **không có prompt**; input là method (đã tách token) bị xoá một log.',
             'lance2': 'LANCE 2.0 là model T5 fine-tune: **không có prompt**; input có tiền tố tác vụ <code>SINGLE_LOG_INJECTION:</code>.',
             'leonid': 'LEONID là model T5 fine-tune: **không có prompt LLM**; input gồm method và 5 log message tương tự truy hồi được (<code>&lt;log_message&gt;</code>, độ tương đồng).',
             'fastlog': 'FastLog là model fine-tune (phân loại token + PLBART): **không có prompt**; input là method bị xoá một log.'}
    parts = [f'*{notes[key]}*',
             details('Input gốc (đúng dòng trong file test của tác giả)', fence('text', R['inp'][i])),
             details('Output gốc của công cụ (đúng dòng trong file prediction của tác giả)', fence('text', R['out'][i] + (f'\n\n# vị trí dự đoán (<LOG>):\n{R["pos"][i]}\n# câu log sinh ra:\n{R["stmt"][i]}' if key == 'fastlog' else ''))),
             details('Ground truth (method gốc có log của developer)', fence('text', R['tgt'][i] if i < len(R['tgt']) else ''))]
    return '\n\n'.join(parts)


_P = None
def pdl_io(sid):
    """PDLogger: annotated input, verbatim prompt of every block + raw answers, message prompt + raw answer."""
    global _P
    if _P is None:
        sys.path.insert(0, str(HERE.parent)); sys.path.insert(0, str(PDL))
        import pdlogger_run as P_
        S_ = {s['sample_id']: s for s in (json.loads(l) for l in (HERE.parent/'logbench_runs/v2_corrected/samples.jsonl').open())}
        O_ = {o['sample_id']: o for o in (json.loads(l) for l in (PDL/'runs/rerun_O/outputs.jsonl').open())}
        _P = (P_, S_, O_)
    P_, S_, O_ = _P
    s, o = S_[sid], O_[sid]
    numbered, blocks, logs = P_.annotate(s['visible_code'])
    parts = [details('Ground truth (LogBench-O: method với <code>&lt;LOG_HERE&gt;</code> và log của developer)', fence('java', s['code_with_marker'] + '\n// gold: ' + s['gold'].strip())),
             details('Input đưa vào PDLogger (đã gắn chú thích block, đánh số dòng)', fence('java', numbered))]
    for b, a in zip(blocks, o['answers']):
        parts.append(details(f'Prompt vị trí của {a["block"]} (nguyên văn <code>position_generation.sh</code>) và câu trả lời thô',
                             fence('text', P_.block_prompt(numbered, logs, b)) + '\n\nCâu trả lời thô:\n\n' + fence('text', a['raw'])))
    N = o.get('chosen_line_1based')
    if N is not None:
        mp = P_.fill(P_.T_MSG, closest_value=str(N), function_with_annotation=P_.NUMBERING + numbered, methodcode=P_.NA,
                     logslice='\n'.join(logs) if logs else '(none)', backwardslice=P_.NA)
        parts.append(details(f'Prompt message cho dòng {N} (nguyên văn <code>message_generation.sh</code>) và câu trả lời thô',
                             fence('text', mp) + '\n\nCâu trả lời thô:\n\n' + fence('text', o.get('message_raw') or '')))
    parts.append(f'*Output cuối: chèn `{(o.get("predicted_statement") or "").strip()}` **sau** dòng {N} (quy ước của paper).*')
    return '\n\n'.join(parts)


N_CODE, N_TABLE = 30, 500
TDEF = {t[0]: (t[1], t[2], t[3]) for t in TYPES}


def esc(s, n=140):
    s = (s or '').replace('|', '\\|').replace('\n', ' ')
    return s if len(s) <= n else s[:n] + '…'


def write_cases_md(folder, tool, t, sel, render, row_cells, header, sort_key):
    """cases/<t>.md: definition, verdict counts, N_CODE cases with full code, compact table (≤ N_TABLE rows)."""
    name, defi, need = TDEF[t]
    sel = sorted(sel, key=sort_key)
    vc = collections.Counter(r['verdict'] for r in sel)
    L = [f'# {tool} · {t}: {name}', '', f'*Bản dễ xem của `{t}.csv` (cùng thư mục). Sinh tự động bằng `TRUONG_HOP_SAI/build.py`.*', '',
         f'**Định nghĩa:** {defi}', '', f'**Metric cần:** {need}', '', f'**Tổng số ca:** {len(sel):,}', '']
    if sel:
        L += ['| Verdict của verifier | Ý nghĩa | Số ca |', '|---|---|---:|',
              *[f'| `{k}` | {VERDICT_VI.get(k, k)} | {c:,} |' for k, c in vc.most_common()], '',
              f'## {min(N_CODE, len(sel))} ca có code đầy đủ (method ngắn nhất trước)', '',
              '`G>` = log của developer (ground truth) · `P>` = log công cụ sinh ra.', '']
        for k, r in enumerate(sel[:N_CODE], 1):
            L += [f'### {k}. {render[0](r)}', '', render[1](r), '', render[2](r), '']
            if len(render) > 3: L += [render[3](r), '']
        L += [f'## Bảng tất cả các ca' + (f' (hiển thị {N_TABLE:,}/{len(sel):,}; phần còn lại xem `{t}.csv`)' if len(sel) > N_TABLE else ''), '',
              '| ' + ' | '.join(header) + ' |', '|' + '---|' * len(header)]
        L += ['| ' + ' | '.join(row_cells(r)) + ' |' for r in sel[:N_TABLE]]
    (folder/'cases'/f'{t}.md').write_text('\n'.join(L) + '\n')


def write_cases_md_tool(folder, tool, rows, pos_name):
    for t in TDEF:
        sel = [r for r in rows if r['status'] == 'ok' and t in r['types']]
        render = (lambda r: f'mẫu `{r["id"]}` · `{r["verdict"]}` ({VERDICT_VI.get(r["verdict"], "")})',
                  code,
                  lambda r: (f'- Metric của công cụ: {their(r, pos_name)}\n'
                             f'- Verifier: CA {int(r["ca"])} · ER {int(r["er"])} · RPA {int(r["rpa"])}'),
                  lambda r: raw_io(tool, r['id']))
        cells = lambda r: [str(r['id']), f'`{r["verdict"]}`', 'đúng' if r['same_point'] else 'sai', 'đúng' if r['lvl_ok'] else 'sai',
                           'đúng' if r['msg_ok'] else 'sai', str(int(r['ca'])), str(int(r['er'])), str(int(r['rpa'])), esc(r['gold']), esc(r['pred'])]
        write_cases_md(folder, tool, t, sel, render, cells,
                       ['id', 'verdict', 'vị trí (M)', 'level (M)', 'message (M)', 'CA', 'ER', 'RPA', 'log gold', 'log sinh ra'],
                       lambda r: (len(r['code'].splitlines()), r['id']))


def stats(rows, key=None):
    if key in EXPECTED and len(rows) < EXPECTED[key]:      # records without a usable <lineK> answer were not written
        rows = rows + [dict(status='no_prediction')] * (EXPECTED[key] - len(rows))
    ok = [r for r in rows if r['status'] == 'ok']
    c = collections.Counter(t for r in ok for t in r['types'])
    off = [r for r in ok if not r['same_point']]
    return dict(total=len(rows), ok=len(ok), status=collections.Counter(r['status'] for r in rows), exact=sum(r['same_point'] for r in ok),
                types=c, off=len(off), off_verdict=collections.Counter(r['verdict'] for r in off),
                t1_exact=sum(r['verdict'] == 'invalid' and r['same_point'] for r in ok))


STATUS_VI = {'ok': 'chấm được', 'pred_changes_other_code': 'công cụ sửa cả code khác ngoài việc chèn log',
             'verifier_crash': 'log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ)', 'not_statement_boundary': 'vị trí không rơi vào ranh giới câu lệnh',
             'gold_not_single_insert': 'dữ liệu gold không phải đúng một lần chèn', 'pred_insertion_unparsable': 'log sinh ra làm hỏng cú pháp tại vị trí chèn',
             'input_or_insertion_unparsable': 'input không parse được', 'verifier_segfault': 'thư viện parse bị crash', 'no_prediction': 'không có output hợp lệ (không trả `<lineK>`, hoặc dòng ngoài phạm vi)'}


def status_table(s):
    L = ['| Trạng thái | Số mẫu |', '|---|---:|']
    for k, v in s['status'].most_common(): L.append(f'| {STATUS_VI.get(k, k)} | {v:,} |')
    return '\n'.join(L)


def type_table(s, notes):
    L = ['| Loại | Số ca | Ghi chú |', '|---|---:|---|']
    for t, name, *_ in TYPES:
        L.append(f'| **{t}** {name} | {s["types"].get(t, 0):,} | {notes.get(t, "")} |')
    return '\n'.join(L)


def diag_table(s):
    L = ['| Chẩn đoán của verifier (trên các ca vị trí không khớp) | Số ca | % |', '|---|---:|---:|']
    for v, c in s['off_verdict'].most_common():
        L.append(f'| `{v}`: {VERDICT_VI.get(v, v)} | {c:,} | {100*c/max(1, s["off"]):.1f}% |')
    return '\n'.join(L)


# ----------------------------------------------------------------------------------------------- tool configs
TOOLS = {
 'LANCE': dict(
   main='lance', alb='al_lance', pos_name='khớp chính xác vị trí token',
   paper='Mastropaolo, Pascarella, Bavota. *Using Deep Learning to Generate Complete Log Statements*. ICSE 2022. arXiv 2201.04837',
   kind='Model T5 (60M tham số) được huấn luyện trước rồi fine-tune; **không dùng prompt**. Input là method đã xoá một log; output là toàn bộ method có chèn log (tự chọn vị trí, level, message).',
   metric=['**Vị trí:** đúng khi trùng vị trí developer đặt, so theo vị trí token (*"injecting it in the correct position in the method (i.e., the same position adopted by developers)"*, §3.1). Không có dung sai.',
           '**Level, message:** khớp chính xác, chấm **độc lập** với vị trí (*"the log level was correctly predicted, independently from the prediction of the position and message"*, Table 3).',
           '**Chạy được:** chỉ báo tỉ lệ output không parse được bằng JavaParser (2,33%). Không kiểm compile, không kiểm điều kiện.'],
   data=['**Nguồn:** gói replication của tác giả, `github.com/antonio-mastropaolo/LANCE` → Google Drive.',
         '- Test set: thư mục `Fine-tuning/test.tsv` (Drive id `1o2ScvTnDQaxH-Y5ACPvFKWnM-wkY_g5z`): 12.020 dòng `input <TAB> target` (method đã xoá log / method gốc).',
         '- Output: biến thể tốt nhất (Denoising), `predictions.txt` (Drive id `1CdNUuVo2glDjV7IQ4cR4LbdZXlXEi4Ek`): 12.020 method có chèn log.',
         '- Kết quả tác giả: `Stats.txt` (khớp số trong paper), `correctLogPosition/Level/Message.csv`, `ID_Perfect.txt`.',
         '**Bản tải về:** `analysis/external_methods/lance/`.',
         '**Dữ liệu gốc của test set:** method Java từ 1.465 project GitHub có dùng Log4j (lấy theo file POM); method dài 10–512 token; đã bỏ trùng.',
         '**Lưu ý:** các file kết quả theo từng mẫu của tác giả (`correctLog*.csv`) **bị lệch chỉ số** so với `predictions.txt` (dòng 30 chứa prediction của một method khác), nên mình **tự tính lại** metric theo định nghĩa trong paper và không dùng file đó. Các con số tổng (`Stats.txt`) vẫn khớp paper.'],
   check='Tỉ lệ vị trí khớp chính xác mình tính lại trên các mẫu chấm được: **71,0%** (paper: 65,4% trên toàn bộ 12.020 mẫu, tính cả mẫu không parse được).',
   ex={'T1': [(3293, 'Ví dụ T1-a: vị trí trùng gold, nhưng in biến chưa khai báo', 'log in `socket`, nhưng `socket` khai báo ở dòng ngay sau, nên không biên dịch được ("cannot find symbol").'),
              (4730, 'Ví dụ T1-b: message và level trùng gold từng chữ, nhưng đặt trước khai báo', 'log in `queryPrepareHandle1` trước câu khai báo biến này, nên không biên dịch được. Paper vẫn tính level đúng, message đúng.')],
       'T2': [(4792, 'Ví dụ T2-a: message và level trùng gold, nhưng log bị đưa vào trong `if`', 'gold in **mọi lần** gọi method; log sinh ra chỉ in khi `webContext instanceof SIPWebContext` (`stronger`).'),
              (835, 'Ví dụ T2-b', 'gold in **mọi lần** timeout; log sinh ra chỉ in khi `pendingRequest != null` (`stronger`). Level vẫn tính đúng.')],
       'T3': [(2157, 'Ví dụ T3-a', 'giữa hai vị trí chỉ có phép gán field `splitBlobStore`, mà log không in field đó; thứ tự không đổi gì.'),
              (6343, 'Ví dụ T3-b', 'giữa hai vị trí chỉ có phép gán `this.configProps`; tương đương.')],
       'T4': [(10658, 'Ví dụ T4-a: log chạy mỗi vòng lặp thay vì một lần', 'gold in **một lần** trước vòng lặp; log sinh ra in **mỗi phần tử** (`stronger`). Vẫn chỉ là "vị trí sai" như mọi lỗi khác.'),
              (3868, 'Ví dụ T4-b: nhầm nhánh', 'log sinh ra nằm trong nhánh `return` sớm, gold ở nhánh tiếp tục xử lý: hai log không bao giờ cùng in (`disjoint`).')],
       'T5': [(2117, 'Ví dụ T5-a', '"Job scheduler shut down" bị in **sau** `super.shutDown()`, trong khi gold in ngay sau khi tắt service và trước `super.shutDown()`.')]}),
 'LANCE_2.0': dict(
   main='lance2', alb=None, pos_name='khớp chính xác vị trí',
   paper='LANCE 2.0 = LANCE được huấn luyện lại trên dataset của paper LEONID: Mastropaolo, Ferrari, Pascarella, Bavota. *Log statement generation via deep learning: Widening the support provided to developers*. JSS 2024. arXiv 2311.04587',
   kind='Model T5 như LANCE, huấn luyện lại trên dataset lớn hơn; **không dùng prompt**.',
   metric=['**Vị trí, tên biến logger, level, message:** khớp chính xác; mỗi thành phần chấm **độc lập** (*"correctly predicted (✓), independently from whether the other three components were correct or not"*, §5.1).',
           '**Thêm:** BLEU, METEOR, ROUGE, Levenshtein cho message.',
           '**Chạy được / điều kiện:** không kiểm.'],
   data=['**Nguồn:** `github.com/antonio-mastropaolo/automating-logging-acitivities` → Drive, thư mục prediction LANCE-2.0 (id `1R4ZfUcVuvHfPKd5YnLFz-Uw0dp5xzUKf`): `inputs`, `predictions`, `targets` (28.698 dòng mỗi file).',
         '**Bản tải về:** `analysis/external_methods/lance2/`.',
         '**Dữ liệu gốc:** method Java từ 2.978 project GitHub dùng Log4j/SLF4J (Maven/Gradle); test single-log 28.698 mẫu.'],
   check='Vị trí khớp chính xác tính lại: **83,9%** (paper: 82,28%).',
   ex={'T1': [(7910, 'Ví dụ T1-a', 'log in `apiUser2` trước câu khai báo `ApiUser2 apiUser2 = …`.'), (8952, 'Ví dụ T1-b', 'log in `session` trước câu khai báo `RemoteSession session = …`.')],
       'T2': [(1101, 'Ví dụ T2-a: log bị đặt sau một `return` có điều kiện', 'gold in **mọi lần**; log sinh ra chỉ in khi `key % 2 != 1` (`stronger`).'),
              (26454, 'Ví dụ T2-b', 'log sinh ra in cả khi consumer đã đóng (trước lệnh `throw`), còn gold chỉ in khi chưa đóng (`weaker`).')],
       'T3': [(1548, 'Ví dụ T3-a', 'chỉ vượt qua phép gán field `this.userFeedback`, mà log không in field này.'), (50, 'Ví dụ T3-b', 'chỉ vượt qua phép gán field.')],
       'T4': [(22487, 'Ví dụ T4-a', 'log bị đặt sau `if (!removed) throw …`, nên chỉ in khi thành công (`stronger`); vẫn chỉ là "sai vị trí".')],
       'T5': [(6047, 'Ví dụ T5-a', 'log lỗi được in trước `response.sendError(...)` thay vì sau; tranh cãi được.')]}),
 'LEONID': dict(
   main='leonid', alb='al_leonid', pos_name='khớp chính xác vị trí',
   paper='Mastropaolo, Ferrari, Pascarella, Bavota. *Log statement generation via deep learning: Widening the support provided to developers*. JSS 2024. arXiv 2311.04587',
   kind='Model T5 kết hợp truy hồi thông tin: input có thêm k = 5 log message tương tự lấy bằng Jaccard; **không dùng prompt LLM**.',
   metric=['Giống LANCE 2.0: vị trí, tên biến logger, level, message khớp chính xác, chấm độc lập; thêm BLEU, METEOR, ROUGE.',
           '**Chạy được / điều kiện:** không kiểm.'],
   data=['**Nguồn:** cùng repo với LANCE 2.0 → Drive, `LEONID Single Log/TOP-5/Test/` (`inputs`, `predictions`, `targets`; id thư mục `1VTD6M5bt8LYJYnOTzcLn0j4aERrJu-Yv`).',
         '**Bản tải về:** `analysis/external_methods/leonid/`. Input có dạng `b\'SINGLE_LOG_INJECTION: <method> <log_message> … </log_message>\'`; mình bỏ phần log message mẫu ở cuối để lấy method.',
         '**Dữ liệu gốc:** như LANCE 2.0 (28.698 mẫu test).'],
   check='Vị trí khớp chính xác tính lại: **84,0%** (paper: 82,35%).',
   ex={'T1': [(21900, 'Ví dụ T1-a: vị trí trùng gold, in biến chưa khai báo', 'log in `groupList` trước câu `List<TbGroup> groupList = …`.'), (25933, 'Ví dụ T1-b', 'log in `data` trước câu khai báo `data`.'),
              (988, 'Ví dụ T1-c: dùng biến của vòng lặp trước vòng lặp', '`tripValidator` chỉ tồn tại bên trong `for`. Paper vẫn tính level đúng.')],
       'T2': [(14210, 'Ví dụ T2-a', 'log bị đặt sau `if (impassable == null) return false;`, nên không in khi `impassable == null` (`stronger`).'),
              (2244, 'Ví dụ T2-b: log ra khỏi vòng lặp', 'gold in **mỗi script** trong vòng lặp; log sinh ra in **một lần** trước vòng lặp (`weaker`).')],
       'T3': [(738, 'Ví dụ T3-a', 'chỉ vượt qua phép gán `released = true`, mà log không in biến này.'), (1548, 'Ví dụ T3-b', 'chỉ vượt qua phép gán field.')],
       'T4': [(70, 'Ví dụ T4-a', 'log bị đặt sau `if (... isEmpty()) return;` và sau một vòng lặp (`stronger`).')],
       'T5': [(6250, 'Ví dụ T5-a', 'log "Received a stop agent message" in sau `setReceived(STOP)` thay vì trước; tranh cãi được.')]}),
 'FastLog': dict(
   main='fastlog', alb='al_fastlog', pos_name='khớp chính xác chỉ số token',
   paper='Xie et al. *FastLog: An End-to-End Method to Efficiently Generate and Insert Logging Statements*. ISSTA 2024. arXiv 2311.02862',
   kind='Hai giai đoạn: (1) model phân loại token chọn vị trí chèn, (2) PLBART sinh câu log tại vị trí đó; **không dùng prompt**.',
   metric=['**Vị trí:** đúng khi chỉ số token dự đoán bằng chỉ số token gold (*"whether the predicted position or level is the same as the ground-truth label"*, §6; code `data["match"] = data["prediction"] == data["target"]`).',
           '**Level, message:** accuracy và BLEU/ROUGE trên **toàn bộ** mẫu, **độc lập** với vị trí (trong paper, level 71,6% > vị trí 70,5%).',
           '**Chạy được / điều kiện:** không kiểm.'],
   data=['**Nguồn:** `github.com/zhipeng-cai/FastLog` → Drive: `predictions/original-dataset/` (`results_beam_search.csv`, `positions.csv`, `statements_beam_search.csv`) và `datasets/raw/original-test/` (`input.txt`, `target.txt`, `logsta.txt`).',
         '**Bản tải về:** `analysis/external_methods/fastlog/`.',
         '**Dữ liệu gốc:** đúng test set của LANCE (12.020 mẫu).'],
   check='Vị trí khớp chính xác tính lại: **71,3%** (paper: 70,52%). So từng mẫu với phán quyết của chính FastLog (`True_Position == Pred_Position`): **trùng 10.338/10.339 mẫu**.',
   ex={'T1': [(3516, 'Ví dụ T1-a: vị trí trùng gold, in biến chưa khai báo', 'log in `c.study`, nhưng `c` khai báo ở dòng sau.'), (5673, 'Ví dụ T1-b', 'log in `g.localNode()` trước câu `Grid g = G.start(cfg);`. Level vẫn tính đúng.')],
       'T2': [(4792, 'Ví dụ T2-a: message và level trùng gold từng chữ, nhưng log bị đưa vào trong `if`', 'gold in mọi lần; log sinh ra chỉ in khi `webContext instanceof SIPWebContext` (`stronger`).'),
              (6841, 'Ví dụ T2-b', 'log sinh ra in **mọi lần** gọi `stop()`, gold chỉ in khi `selectorThread.isRunning()` (`weaker`).')],
       'T3': [(5777, 'Ví dụ T3-a', 'chỉ vượt qua phép gán `this.xaTerminator`.'), (10515, 'Ví dụ T3-b', 'chỉ vượt qua phép gán `this.commitStarted`.')],
       'T4': [(2080, 'Ví dụ T4-a: log chạy mỗi vòng lặp thay vì một lần', 'gold in tổng kết **một lần** sau vòng lặp; log sinh ra in **mỗi phần tử** (`stronger`).')],
       'T5': [(7809, 'Ví dụ T5-a: thứ tự làm đổi kết quả thật', 'gold `logger.debug("hello")` được gọi **sau** `inner.setLevel(Level.OFF)` để kiểm rằng log bị chặn; log sinh ra gọi **trước**, nên test kiểm tra một điều khác hẳn.')]}),
 'UniLog': dict(
   main='unilog_deepseek_base', alb='unilog_warmup_cl', pos_name='khớp chính xác dòng (AL-Bench)',
   paper='Xu et al. *UniLog: Automatic Logging via LLM and In-Context Learning*. ICSE 2024 (bản đóng, không có bản mở). Output dùng ở đây do **AL-Bench** (Tan et al., arXiv 2502.03160) chạy lại và công bố',
   kind='LLM + in-context learning: prompt gồm 5 ví dụ mẫu, code đánh thẻ `<lineN>`; model trả `<lineK>câu log`. AL-Bench chạy với hai backbone: DeepSeek-V3 (UniLog_ds) và CodeLlama-7B (UniLog_cl).',
   metric=['**AL-Bench chấm vị trí khớp chính xác dòng** (*"we rigorously compare the predicted positions … PA = P_c/N_a"*; code `if pos_gth == pos_pred`).',
           '**Level, message, biến:** chia cho toàn bộ mẫu, **độc lập** với vị trí.',
           '**Đánh giá động** (compile và chạy test) chỉ trên 2.238 mẫu; không kiểm điều kiện.',
           'Bài gốc UniLog: không truy cập được bản đầy đủ, nên không xác minh được metric gốc.'],
   data=['**Nguồn:** `github.com/shuaijiumei/logging-benchmark` → Drive AL-Bench, `static evaluation/res_all.zip` → `res_all/unilog/deepseek_base/static_test_data_deepseek_base_cleaned.json` và `…/warmup_cl/…` (39.600 bản ghi: `prompt`, `metadata.position` = dòng gold, `response` = `<lineK>câu log`).',
         '**Bản tải về:** `analysis/external_methods/albench/`.',
         '**Dữ liệu gốc:** AL-Bench, 10 project (Hadoop, Kafka, Flink, Pulsar, Doris, DBeaver, DolphinScheduler, Keycloak, ThingsBoard, ZooKeeper), 39.600 mẫu.',
         '**Lưu ý quan trọng về dữ liệu:** input của AL-Bench để lại **một dòng trống** đúng chỗ log bị xoá, tức là lộ vị trí gold.'],
   check='Vị trí khớp chính xác tính lại (DeepSeek-V3): **37,9%** (AL-Bench Table 2: 37,11%). So từng mẫu với `pos_gth == pos_pred`: trùng 100%.',
   ex={'T1': [(19335, 'Ví dụ T1-a: vị trí trùng gold, in biến chưa khai báo', 'log in `rawConfiguration`, khai báo ở dòng sau.'), (11558, 'Ví dụ T1-b', 'log in `ret` trước câu khai báo `Resource ret = …`; level vẫn tính đúng.')],
       'T2': [(25140, 'Ví dụ T2-a: message và level trùng gold, nhưng log ra ngoài vòng `while`', 'gold "still waiting…" in **mỗi vòng chờ**; log sinh ra chỉ in **một lần** trước vòng lặp (`weaker`).'),
              (23472, 'Ví dụ T2-b', 'log "Unable to delete" in **trước** khi thử xoá, tức là in cả khi xoá thành công; gold chỉ in khi `!file.delete()` (`weaker`).')],
       'T3': [(39070, 'Ví dụ T3-a: lệch đúng một dòng trống (7.807 ca như vậy)', 'hai vị trí chỉ cách nhau dòng trống do AL-Bench để lại; trong Java đây là **cùng một chỗ**.'),
              (1165, 'Ví dụ T3-b', 'tương tự: chỉ cách nhau dòng trống.')],
       'T4': [(4726, 'Ví dụ T4-a', 'log "Dropping resource" in mọi lần, gold chỉ in khi resource không tồn tại (`weaker`).')],
       'T5': [(2348, 'Ví dụ T5-a', 'log "WorkerRpcServer closed" in **trước** khi `nettyRemotingServer.close()` chạy.')]}),
}


def build_tool(name, cfg):
    folder = HERE/name; folder.mkdir(exist_ok=True)
    rows = load(cfg['main']); s = stats(rows, cfg['main']); idx = {r['id']: r for r in rows}
    write_cases_csv(folder, rows)
    write_cases_md_tool(folder, name, rows, cfg['pos_name'])
    notes = {'T1': f'trong đó **{s["t1_exact"]}** ca vị trí trùng **y hệt** gold', 'T3': '', 'T4': f'= toàn bộ {s["off"]:,} ca vị trí không khớp trừ T3'}
    if name == 'UniLog':
        blank = sum(1 for r in rows if r['status'] == 'ok' and 'T3' in r['types'] and not any(l.strip() for l in r['code'].splitlines()[min(r['gold_line'], r['pred_line']):max(r['gold_line'], r['pred_line'])]))
        notes['T3'] = f'**{blank:,}** ca chỉ lệch qua **một dòng trống** do AL-Bench để lại'
    L = [f'# {name}: các trường hợp metric của công cụ chấm sai output của chính công cụ', '',
         f'*Sinh tự động bằng `analysis/TRUONG_HOP_SAI/build.py`. Danh sách mọi ca theo từng loại: `cases/T1.md` … `cases/T5.md` (bản dễ xem) và `cases/T*.csv` (đầy đủ). Định nghĩa các loại T1–T5: `../README.md`.*', '',
         '## 1. Phương pháp và cách nó tự đánh giá', '', f'**Paper:** {cfg["paper"]}.', '', f'**Cách sinh log:** {cfg["kind"]}', '',
         '**Metric của chính paper (M):**', *[f'- {x}' for x in cfg['metric']], '',
         '## 2. Dữ liệu lấy ở đâu', '', *[x if x.startswith('-') else f'{x}\n' for x in cfg['data']], '',
         f'**Kiểm tra cách chuyển đổi:** {cfg["check"]}', '',
         '**Cách chấm lại:** output là method đã tách token (LANCE, LEONID, FastLog) hoặc code có thẻ dòng (UniLog). Mình xác định chỗ chèn của log gold và log sinh ra, xếp method mỗi câu lệnh một dòng, rồi (1) tính lại M đúng theo định nghĩa của paper, (2) chạy verifier (CA / ER / RPA). Script: `analysis/external_methods/rescore_lance.py`, `rescore_unilog.py`.', '',
         f'**Số mẫu chấm được: {s["ok"]:,}/{s["total"]:,}**', '', status_table(s), '',
         '## 3. Tổng hợp các trường hợp sai', '', f'Vị trí khớp chính xác theo M: **{s["exact"]:,}/{s["ok"]:,} ({100*s["exact"]/s["ok"]:.1f}%)**. Một mẫu có thể thuộc nhiều loại.', '',
         type_table(s, notes), '', '**Chẩn đoán các ca vị trí không khớp** (M cho 0 điểm như nhau cho tất cả):', '', diag_table(s), '']
    if cfg.get('alb') and (EXT/cfg['alb']/'rescored.jsonl').exists():
        r2 = load(cfg['alb']); s2 = stats(r2, cfg['alb'])
        lab = 'UniLog với backbone CodeLlama-7B (cũng do AL-Bench chạy)' if name == 'UniLog' else f'{name} trên AL-Bench (do nhóm AL-Bench chạy lại)'
        L += [f'### Bổ sung: {lab}', '',
              f'Nguồn: `res_all.zip` của AL-Bench. Chấm được **{s2["ok"]:,}/{s2["total"]:,}** mẫu; vị trí khớp chính xác **{100*s2["exact"]/max(1, s2["ok"]):.1f}%**' + ALB_PAPER.get(cfg['alb'], '') + '.', '',
              status_table(s2), '', type_table(s2, {'T1': f'trong đó **{s2["t1_exact"]}** ca vị trí trùng y hệt gold'}), '']
        if name == 'LEONID':
            L += ['*Lưu ý: trên AL-Bench, LEONID sửa luôn code khác ngoài việc chèn log ở phần lớn mẫu (khả năng cao do method dài bị cắt ở 512 token), nên chỉ chấm được khoảng 22%; con số ở bảng này kém đại diện.*', '']
    L += ['## 4. Ví dụ theo từng loại', '']
    for t, tname, tdef, need in TYPES:
        L += [f'### {t}. {tname} → cần **{need}**', '', tdef, '', f'Số ca: **{s["types"].get(t, 0):,}**. Xem tất cả: [cases/{t}.md](cases/{t}.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/{t}.csv` (đầy đủ).', '']
        for i, title, why in cfg['ex'].get(t, []):
            r = idx.get(i)
            if r is None or r['status'] != 'ok': continue
            L.append(example(r, title, why, cfg['pos_name']))
        if t == 'T5': L += ['*Nhiều ca T5 là công cụ log một sự kiện khác nhưng hợp lý; cần đọc message mới phán được. Chỉ dùng để minh hoạ.*', '']
    L += ['## 5. Giới hạn', '',
          '- Tham chiếu đúng/sai là verifier của mình, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện (T2, T4). Cần đánh giá bởi người (E6).',
          '- ER chưa kiểm bằng javac; các ví dụ T1 ở trên đã đọc tay, đều là dùng biến trước khai báo, chắc chắn không biên dịch được.',
          '- Mẫu có log nằm trong lambda / lớp ẩn danh bị loại, vì verifier chưa hỗ trợ.',
          '- Level và message so khớp chính xác (đúng định nghĩa của paper); BLEU/ROUGE chưa tính lại.', '']
    (folder/'README.md').write_text('\n'.join(L))
    return s


# ---------------------------------------------------------------------------------------------------- PDLogger
def build_pdlogger():
    folder = HERE/'PDLogger'; folder.mkdir(exist_ok=True)
    io = json.load((LCS/'example_io.json').open())
    SC = [json.loads(l) for l in (PDL/'runs/rerun_O/scored.jsonl').open()]
    A = {json.loads(l)['sample_id']: json.loads(l) for l in (PDL/'attribution_rows.jsonl').open()}
    P = [r for r in SC if r.get('has_pred')]
    t1 = [r for r in P if r.get('pa_pdl') and r['verdict'] == 'invalid']
    t5 = [r for r in P if r.get('pa_pdl') and not r.get('rpa') and r['verdict'] != 'invalid']
    t3 = [r for r in P if r.get('rpa') and not r.get('pa_pdl')]
    t4 = [r for r in P if not r.get('pa_pdl') and not r.get('rpa')]
    (folder/'cases').mkdir(exist_ok=True)
    for t, sel in [('T1', t1), ('T3', t3), ('T4', t4), ('T5', t5)]:
        with (folder/'cases'/f'{t}.csv').open('w', newline='') as f:
            w = csv.writer(f); w.writerow(['sample_id', 'verdict_verifier', 'giai_thich', 'PA', 'PDLogger_PA@1', 'CA', 'ER', 'RPA', 'loi_cua_PDLogger_qua_C1_C5'])
            for r in sel:
                a = A.get(r['sample_id'], {})
                w.writerow([r['sample_id'], r['verdict'], VERDICT_VI.get(r['verdict'], ''), int(bool(r.get('pa0'))), int(bool(r.get('pa_pdl'))),
                            int(bool(r.get('ca'))), int(bool(r.get('er'))), int(bool(r.get('rpa'))), a.get('robust', '')])
    S_ = {s['sample_id']: s for s in (json.loads(l) for l in (HERE.parent/'logbench_runs/v2_corrected/samples.jsonl').open())}
    O_ = {o['sample_id']: o for o in (json.loads(l) for l in (PDL/'runs/rerun_O/outputs.jsonl').open())}
    def pcode(r):
        s, o = S_[r['sample_id']], O_[r['sample_id']]; Ls = s['visible_code'].splitlines(); g, k = s['gold_line'], o['predicted_line']; out = []
        for j, l in enumerate(Ls + ['']):
            if j == g: out.append('G>  ' + s['gold'].strip())
            if j == k: out.append('P>  ' + (o['predicted_statement'] or '').strip())
            if j < len(Ls): out.append('    ' + l[:160])
        return '```java\n' + '\n'.join(out) + '\n```'
    for t, sel in [('T1', t1), ('T3', t3), ('T4', t4), ('T5', t5)]:
        render = (lambda r: f'`{r["sample_id"]}` · `{r["verdict"]}` ({VERDICT_VI.get(r["verdict"], "")})', pcode,
                  lambda r: (f'- PDLogger chọn dòng {O_[r["sample_id"]]["chosen_line_1based"]} (chèn sau dòng đó) · PA {int(bool(r.get("pa0")))} · PDLogger PA@1 {int(bool(r.get("pa_pdl")))}\n'
                             f'- Verifier: CA {int(bool(r.get("ca")))} · ER {int(bool(r.get("er")))} · RPA {int(bool(r.get("rpa")))} · lỗi của PDLogger qua C1–C5: {A.get(r["sample_id"], {}).get("robust", "—")}'),
                  lambda r: pdl_io(r['sample_id']))
        cells = lambda r: [f'`{r["sample_id"][2:]}`', f'`{r["verdict"]}`', str(int(bool(r.get('pa0')))), str(int(bool(r.get('pa_pdl')))), str(int(bool(r.get('ca')))),
                           str(int(bool(r.get('er')))), str(int(bool(r.get('rpa')))), str(A.get(r['sample_id'], {}).get('robust', '—')),
                           esc(S_[r['sample_id']]['gold'].strip()), esc((O_[r['sample_id']]['predicted_statement'] or '').strip())]
        write_cases_md(folder, 'PDLogger', t, sel, render, cells,
                       ['mẫu', 'verdict', 'PA', 'PA@1', 'CA', 'ER', 'RPA', 'lỗi của PDLogger (C1–C5)', 'log gold', 'log sinh ra'],
                       lambda r: (len(S_[r['sample_id']]['visible_code'].splitlines()), r['sample_id']))
    blk = lambda k, title, why: '\n'.join([f'#### {title}', '', io[k]['inline'].rsplit('\n', 1)[0], '', io[k]['merged'], '', f'- **Vì sao metric chấm sai:** {why}', ''])
    diag = collections.Counter(r['verdict'] for r in t4)
    L = ['# PDLogger: các trường hợp metric của PDLogger chấm sai output của chính PDLogger', '',
         '*Danh sách mọi ca: `cases/T1.md`, `T3.md`, `T4.md`, `T5.md` (bản dễ xem) và `cases/*.csv`. Định nghĩa T1–T5: `../README.md`. Chi tiết thêm: `analysis/logging_condition_study/BAO_CAO_PAK_METRIC.md` mục 4 (đặc biệt 4.8) và `analysis/pdlogger_repro/KIEM_CHUNG_PDLOGGER.md`.*', '',
         '## 1. Phương pháp và cách nó tự đánh giá', '',
         '**Paper:** PDLogger, arXiv 2507.19951 (2025). Repo: `github.com/qlbdsc/PDLogger` (chỉ có prompt và script phụ; **không** có dữ liệu, output, script đánh giá).', '',
         '**Cách sinh log:** LLM (paper dùng o3-mini). Mỗi block (if, try, loop, method) được hỏi riêng bằng một prompt "vị trí" để chọn dòng N; sau đó một prompt "message" sinh câu log; log được chèn **sau** dòng N; có bước khử trùng lặp và tinh chỉnh level.', '',
         '**Metric của chính paper (M):**',
         '- **Vị trí (PA@1):** *"A prediction is counted as correct (PA = 1) if the predicted line number deviates from the true line number by at most one and both lines are located within the same code block"* (§4.1).',
         '- **Nội dung:** L-ACC, AOD, biến P/R, BLEU, ROUGE, BERTScore. Paper không ghi rõ có chỉ chấm trên log khớp vị trí không.',
         '- **Chạy được / điều kiện:** không kiểm.', '',
         '## 2. Dữ liệu lấy ở đâu', '',
         '**PDLogger không công bố output, nên mình tự tái hiện** (`analysis/pdlogger_repro/`):',
         '- **Prompt nguyên văn** từ `block-type-based-prompting/position_generation.sh` và `message_generation.sh` (kiểm bằng hash). Bộ gán nhãn block chuyển từ `block_abstract.java` sang Python.',
         '- Backbone **gpt-4o-mini** (paper dùng o3-mini); **không có** ngữ cảnh Joern, bước khử trùng lặp, tinh chỉnh level; chọn 1 vị trí có quality score cao nhất (do mình thêm).',
         '- Chèn log **sau** dòng N, đúng quy ước của paper (§3.4).',
         '- **Dữ liệu:** 1.000 method đầu của **LogBench-O** (`analysis/logbench_runs/v2_corrected/samples.jsonl`); ground truth là log thật của developer bị che bằng `<LOG_HERE>`.',
         '- Output: `analysis/pdlogger_repro/runs/rerun_O/outputs.jsonl`; kết quả chấm: `scored.jsonl`.', '',
         f'PDLogger trả vị trí cho **{len(P)}/1.000** mẫu.', '',
         '**Kiểm chứng lỗi thuộc về PDLogger** (`attribution_check.py`): mỗi lỗi được kiểm 5 điều kiện: C1 prompt nguyên văn; C2 vẫn sai nếu đọc N là "trước dòng N"; C3 mọi ứng viên PDLogger đề xuất đều sai; C4 parse đúng; C5 không phải log trùng mà bước dedup của paper sẽ xoá. Kết quả: **266/638 lỗi (42%)** qua cả 5 điều kiện. Cột `loi_cua_PDLogger_qua_C1_C5` trong CSV ghi kết quả này cho từng ca.', '',
         '## 3. Tổng hợp các trường hợp sai', '',
         '| Loại | Số ca | Ghi chú |', '|---|---:|---|',
         f'| **T1** PA@1 chấm đúng nhưng log **không chạy được** | **{len(t1)}** | log nằm sau `return`/`throw`. Đọc theo cả hai quy ước dòng, PA@1 đều = 1 (một cách đọc thì log không chạy được, cách kia thì log đúng y gold), nên PA@1 không biết log có chạy được không |',
         '| **T2** nội dung được tính đúng dù in sai lúc | — | Với PDLogger, lỗi điều kiện đều bị PA@1 chấm 0; không có trường hợp metric cộng điểm |',
         f'| **T3** PA và PA@1 chấm 0 cho log đặt đúng | **{len(t3)}** | log ra ngoài guard `isDebugEnabled()` nhưng vẫn in đúng lúc; 1 ca trong đó là verifier chấm nhầm (`RecoverableThreadScheduler`), còn 4 |',
         f'| **T4** cùng điểm 0 cho mọi kiểu sai | {len(t4)} | xem bảng chẩn đoán |',
         f'| **T5** PA@1 chấm đúng nhưng sai thứ tự | {len(t5)} | 14 ca qua C1–C5; đọc tay khoảng 4 sai rõ |', '',
         '**Chẩn đoán các ca PA@1 = 0 và RPA = 0:**', '', '| Verdict | Số ca |', '|---|---:|',
         *[f'| `{k}`: {VERDICT_VI.get(k, k)} | {v} |' for k, v in diag.most_common()], '',
         '## 4. Ví dụ theo từng loại', '',
         '### T1. PA@1 chấm đúng nhưng log không chạy được → cần ER', '',
         blk('QSP', 'Ví dụ T1-a: message trùng gold từng chữ, nằm sau `throw`', 'PDLogger trả lời dòng của `throw`; paper chèn **sau** dòng đó nên log không bao giờ chạy. Lệch 1 dòng, cùng block, nên PA@1 = 1.'),
         blk('PLUG', 'Ví dụ T1-b: log sau `return false;`', 'tương tự: log nằm sau `return`, PA@1 = 1.'),
         '### T3. PA và PA@1 chấm 0 cho log đặt đúng → cần CA / RPA', '',
         blk('TEMPT', 'Ví dụ T3-a: log ra ngoài guard `isDebugEnabled()`', 'log ở level debug vốn chỉ in khi debug bật, nên guard chỉ để tiết kiệm hiệu năng; điều kiện in ra giống hệt gold. Khác block nên PA@1 = 0.'),
         blk('CA-3', 'Ví dụ T3-b', 'tương tự (`SAAJUniverse.unset`).'),
         '### T4. Cùng điểm 0 cho mọi kiểu sai → cần CA (chẩn đoán)', '',
         blk('CA-2', 'Ví dụ T4-a: log trong vòng lặp, in 40.000 lần', 'prompt của PDLogger dặn đặt log ở đầu block bên trong; message "Starting to send 40000 messages" mô tả sự kiện một lần (`stronger`).'),
         blk('CA-4', 'Ví dụ T4-b: nhầm nhánh', 'nhánh lỗi `else` mất log; log "Checking if…" chỉ in khi kiểm tra đã thành công (`disjoint`).'),
         blk('AMQ3932', 'Ví dụ T4-c', 'log "Attempting to receive…" nằm trong `catch`, chỉ in khi có lỗi (`stronger`).'),
         '### T5. PA@1 chấm đúng nhưng sai thứ tự → RPA (minh hoạ)', '',
         blk('LOGMED', 'Ví dụ T5-a', 'log "Sending request" in **sau** khi đã gửi và nhận phản hồi.'),
         blk('CLAIM', 'Ví dụ T5-b', 'log "Attempting to retrieve" in **sau** khi đã lấy xong.'),
         '### Không quy cho PDLogger: log trùng log có sẵn', '',
         blk('HL7', 'Ví dụ', 'PDLogger chép lại y nguyên log đã có trong `catch`; bước khử trùng lặp của paper (không tái hiện) nhiều khả năng sẽ xoá log này. Có 144 ca như vậy, mình **không** tính là lỗi của PDLogger.'),
         '## 5. Giới hạn', '',
         '- Bản tái hiện dùng gpt-4o-mini và không có ngữ cảnh Joern; chưa kiểm được với o3-mini.',
         '- Quy ước "sau dòng N" là của paper, nhưng prompt của PDLogger lại hỏi dòng một cách mơ hồ; nhóm T1 vì vậy là hệ quả của chính thiết kế PDLogger (prompt và quy tắc chèn mâu thuẫn nhau).',
         '- Tham chiếu là verifier của mình, so với một gold; đọc tay cho thấy khoảng một nửa lỗi điều kiện là "log khác nhưng hợp lý".', '']
    (folder/'README.md').write_text('\n'.join(L))
    return dict(T1=len(t1), T3=len(t3), T4=len(t4), T5=len(t5), ok=len(P))


def build_sclogger():
    """SCLogger: approximate re-implementation on AL-Bench / Hadoop 3.4.0 (analysis/sclogger_repro)."""
    folder = HERE/'SCLogger'; folder.mkdir(exist_ok=True)
    R = HERE.parent/'sclogger_repro'/'run'
    if not (R/'scored.jsonl').exists():
        return None
    Pp = {json.loads(l)['id']: json.loads(l) for l in (R/'prepared.jsonl').open()}
    Oo = {json.loads(l)['id']: json.loads(l) for l in (R/'outputs.jsonl').open()}
    S_ = [json.loads(l) for l in (R/'scored.jsonl').open()]
    ok = [d for d in S_ if d['status'] == 'ok']
    st = collections.Counter(d['status'] for d in S_)
    B = lambda d: d['before']
    def lvl_ok(d): return lvl(d['gold']) is not None and lvl(d['gold']) == lvl(d['statement'] or '')
    def msg_ok(d): return msg(d['gold']) == msg(d['statement'] or '')
    t1 = [d for d in ok if B(d)['pa1'] and not B(d)['er']]
    t3 = [d for d in ok if not B(d)['pa1'] and B(d)['rpa']]
    t4 = [d for d in ok if not B(d)['pa1'] and not B(d)['rpa']]
    t5 = [d for d in ok if B(d)['pa1'] and not B(d)['rpa'] and B(d)['er']]
    both = sum(1 for d in ok if not B(d)['rpa'] and isinstance(d.get('after'), dict) and 'rpa' in d['after'] and not d['after']['rpa'])
    wrong = sum(1 for d in ok if not B(d)['rpa'])
    mean = lambda conv, m: 100 * sum(d[conv][m] for d in ok if 'rpa' in d.get(conv, {})) / max(1, sum('rpa' in d.get(conv, {}) for d in ok))
    def scode(d):
        Ls = Pp[d['id']]['lines']; g, k = d['gold_line'], B(d)['pred_line']; out = []
        for j, l in enumerate(Ls + ['']):
            if j == g: out.append('G>  ' + d['gold'])
            if j == k: out.append('P>  ' + (d['statement'] or ''))
            if j < len(Ls): out.append('    ' + l[:160])
        return '```java\n' + '\n'.join(out) + '\n```'
    def sio(d):
        o = Oo[d['id']]; pr = Pp[d['id']]
        parts = [details('Prompt ngữ cảnh đầy đủ (khuôn chép từ Fig. 6; code, code slice, log slice, danh sách biến, 5 ví dụ BM25)', fence('text', pr['prompt'])),
                 details(f'Output lần 1 của LLM (cách đọc: <code>{o.get("parse_initial")}</code>)', fence('text', o['initial_raw']))]
        if o.get('refined'):
            parts += [details('Prompt tinh chỉnh biến (lượt 2)', fence('text', o['refine_prompt'])),
                      details(f'Output lượt 2 (cách đọc: <code>{o.get("parse_refined")}</code>)', fence('text', o['refined_raw'] or ''))]
        parts.append(f'*Output cuối: `<Line Number>: {o["line_1based"]}` → log nằm ở dòng {o["line_1based"]} (chèn trước dòng đó của input); câu log `{o["statement"]}`.*')
        return '\n\n'.join(parts)
    (folder/'cases').mkdir(exist_ok=True)
    for f in (folder/'cases').glob('*'): f.unlink()
    sets = {'T1': t1, 'T3': t3, 'T4': t4, 'T5': t5}
    for t, sel in sets.items():
        with (folder/'cases'/f'{t}.csv').open('w', newline='') as f:
            w = csv.writer(f); w.writerow(['albench_id', 'verdict_verifier', 'giai_thich', 'PA', 'SCLogger_PA@1', 'CA', 'ER', 'RPA', 'level_dung', 'message_dung', 'gold_log', 'log_sinh_ra'])
            for d in sel:
                w.writerow([d['id'], B(d)['verdict'], VERDICT_VI.get(B(d)['verdict'], ''), int(B(d)['pa0']), int(B(d)['pa1']), int(B(d)['ca']), int(B(d)['er']), int(B(d)['rpa']),
                            int(lvl_ok(d)), int(msg_ok(d)), d['gold'], d['statement']])
        for d in sel: d['verdict'] = B(d)['verdict']
        render = (lambda d: f'mẫu AL-Bench `{d["id"]}` · `{B(d)["verdict"]}` ({VERDICT_VI.get(B(d)["verdict"], "")})', scode,
                  lambda d: (f'- Metric của SCLogger: PA@1 **{int(B(d)["pa1"])}** (±1 dòng, cùng block) · PA đúng dòng {int(B(d)["pa0"])}'
                             f' · nội dung (chỉ chấm khi PA@1 = 1): level {"đúng" if lvl_ok(d) else "sai"}, message {"đúng" if msg_ok(d) else "sai"}\n'
                             f'- Verifier: CA {int(B(d)["ca"])} · ER {int(B(d)["er"])} · RPA {int(B(d)["rpa"])}'), sio)
        cells = lambda d: [str(d['id']), f'`{B(d)["verdict"]}`', str(int(B(d)['pa0'])), str(int(B(d)['pa1'])), str(int(B(d)['ca'])), str(int(B(d)['er'])),
                           str(int(B(d)['rpa'])), esc(d['gold']), esc(d['statement'])]
        write_cases_md(folder, 'SCLogger (xấp xỉ)', t, sel, render, cells, ['id', 'verdict', 'PA', 'PA@1', 'CA', 'ER', 'RPA', 'log gold', 'log sinh ra'],
                       lambda d: (len(Pp[d['id']]['lines']), d['id']))
    diag = collections.Counter(B(d)['verdict'] for d in t4)
    t1_both = sum(1 for d in t1 if isinstance(d.get('after'), dict) and d['after'].get('verdict') in ('invalid', 'invalid_insertion', 'out_of_range'))
    def ex(sel, k, title, why):
        sel = sorted(sel, key=lambda d: len(Pp[d['id']]['lines']))[k:k + 1]
        return '\n'.join([f'#### {title} (mẫu AL-Bench `{d["id"]}`)\n\n{scode(d)}\n\n- Metric của SCLogger: PA@1 {int(B(d)["pa1"])} · Verifier: `{B(d)["verdict"]}` · CA {int(B(d)["ca"])} · ER {int(B(d)["er"])} · RPA {int(B(d)["rpa"])}\n- {why}\n' for d in sel])
    L = ['# SCLogger (TÁI HIỆN XẤP XỈ): các trường hợp metric của SCLogger chấm sai', '',
         '> ⚠️ **Đây là bản tái hiện XẤP XỈ**, không phải output gốc của SCLogger. Tác giả không công bố prompt, pipeline gọi LLM, dữ liệu hay output. Mọi con số và ví dụ trong thư mục này phải được gọi là "SCLogger (xấp xỉ)".', '',
         '*Danh sách mọi ca: `cases/T1.md`, `T3.md`, `T4.md`, `T5.md` (bản dễ xem, có prompt, input, output) và `cases/*.csv`. Code: `analysis/sclogger_repro/sclogger_run.py`.*', '',
         '## 1. Phương pháp và cách nó tự đánh giá', '',
         '**Paper:** Li et al. *Go Static: Contextualized Logging Statement Generation*. FSE 2024. arXiv 2402.12958. Repo: `github.com/YichenLi00/SCLogger` (README: "Under Construction", lần push cuối 04/08/2024).', '',
         '**Cách sinh log:** phân tích tĩnh toàn project để lấy (1) code slice: method gọi tới và được gọi trong vòng 2 bước, (2) log slice: log có thể chạy trước và sau, (3) danh sách biến dùng được; (4) chọn 5 ví dụ mẫu cùng project bằng BM25; (5) ghép thành prompt chain-of-thought gửi LLM, nhận `<Line Number>` và `<Statement>`; (6) lượt 2 "tinh chỉnh biến" với thông tin kiểu chi tiết.', '',
         '**Metric của chính paper (M):**',
         '- **Vị trí:** *"PA as 1 … if the distance between the predicted line number and the actual line number is less than or equal to one line and both … must be within the same block"* (§4.3.1). Giống hệt PDLogger.',
         '- **Nội dung:** *"we only calculate the metrics for what-to-log when the logging position … is predicted correctly"* (§4.3.2).',
         '- **Chạy được / điều kiện:** không kiểm.', '',
         '## 2. Tái hiện thế nào, và trung thực tới đâu', '',
         '| Thành phần | Bản này dùng | Mức trung thực |', '|---|---|---|',
         '| Danh sách biến (§3.2.3) | **chính `Src/Var/AvaVarList.java` của tác giả**, biên dịch và chạy nguyên trạng (Eclipse JDT, source và jar Hadoop 3.4.0) | code của tác giả |',
         '| 5 ví dụ mẫu (§3.3) | logic `bm25_selection` của tác giả (`Scripts/demo_case_selection.py`): tách từ camelCase, lấy top-5; BM25 của gensim 3.8.3 chép lại công thức (gensim 3.8.3 không cài được trên Python 3.12) | logic của tác giả |',
         '| Call graph (§3.2.1) | java-callgraph (BCEL) trên jar Hadoop 3.4.0, đúng định dạng đầu vào mà `CodeSlicer.java` của tác giả đọc; paper dùng phân tích con trỏ nhạy ngữ cảnh | xấp xỉ |',
         '| Code slice | method gọi tới và được gọi trong vòng 2 bước, chọn ngẫu nhiên 1 đường (quy tắc của paper); lấy source method như `MethodFinder.java` | quy tắc của paper, code của mình |',
         '| Log slice (§3.2.2) | các câu log trong các method trên đường 2 bước đó (trước = method gọi tới, sau = method được gọi); công cụ log graph của paper không được công bố | xấp xỉ |',
         '| Prompt (§3.4) | **chép từ hình Fig. 6** (không có bản text) | xấp xỉ |',
         '| Tinh chỉnh biến (§3.5) | lượt 2 "Please rethink the variable usage with detailed type information about <Var>" kèm chữ ký thành viên của kiểu biến (paper in cả source class) | xấp xỉ |',
         '| Backbone | **gpt-4o-mini**, temperature 0 (paper: gpt-3.5-turbo-0301, đã ngừng cung cấp) | khác |',
         '| Chia dữ liệu | chia method 8:2 ngẫu nhiên (§4.1); ví dụ mẫu và các slice không dùng method test | như paper |', '',
         '**Dữ liệu:** AL-Bench (`cleaned_static_test_data.json`), phần **main code của 11 module lõi Hadoop** (common, hdfs, hdfs-client, mapreduce-client-core/app, yarn-api/common/client/server-common/resourcemanager/nodemanager). Paper và code của tác giả cũng làm trên Hadoop (paper: 3.3.0; code `VarRefine.java` của tác giả trỏ tới jar Hadoop 3.3.6). Source **Hadoop 3.4.0** tải từ `archive.apache.org`; jar 3.4.0 từ Maven Central. Pool: 6.746 mẫu (3.830 method); train 5.457 mẫu; **lấy ngẫu nhiên 500 mẫu test**.', '',
         '**Lộ vị trí:** input AL-Bench có dòng trống ở chỗ log bị xoá; ở đây **đã xoá dòng trống này**.', '',
         '**Một điểm phải xử lý:** gpt-4o-mini thường **không theo định dạng** `<Line Number>: N <Statement>: …` mà trả về cả method đã chèn log. Mình **không sửa prompt**; output được đọc theo hai cách và ghi lại cách đọc cho từng mẫu: (1) đúng định dạng; (2) so code trả về với input để tìm log được chèn (lấy log đầu tiên nếu model chèn nhiều log).', '',
         f'**Trạng thái 500 mẫu:** chấm được {st.get("ok", 0)} · không đọc được output {st.get("no_or_unparsable_output", 0)} · không chấm được {st.get("not_scorable", 0)} · thư viện parse bị crash {st.get("verifier_segfault", 0)}.', '',
         '**Quy ước dòng:** các ví dụ mẫu trong prompt dùng nhãn "log nằm ở dòng N", tức chèn trước dòng N của input; đây là cách đọc chính. Cách đọc "chèn sau dòng N" cũng được tính để đối chiếu.', '',
         '| Cách đọc N | PA đúng dòng | **PA@1 (metric SCLogger)** | RPA | CA | ER |', '|---|---:|---:|---:|---:|---:|',
         f'| log ở dòng N (chính) | {mean("before","pa0"):.1f} | **{mean("before","pa1"):.1f}** | {mean("before","rpa"):.1f} | {mean("before","ca"):.1f} | {mean("before","er"):.1f} |',
         f'| chèn sau dòng N | {mean("after","pa0"):.1f} | {mean("after","pa1"):.1f} | {mean("after","rpa"):.1f} | {mean("after","ca"):.1f} | {mean("after","er"):.1f} |', '',
         f'**Đối chiếu thô với số đã công bố:** paper PDLogger chạy SCLogger trên Hadoop 3.4.1 và ActiveMQ được PA@1 = 0,417; bản xấp xỉ này được {mean("before","pa1")/100:.3f} trên Hadoop 3.4.0 (khác dữ liệu, khác backbone, khác prompt; chỉ để tham khảo).', '',
         f'**Lỗi sai dưới cả hai cách đọc N:** {both}/{wrong} lỗi.', '',
         '## 3. Tổng hợp các trường hợp sai', '',
         '| Loại | Số ca | Ghi chú |', '|---|---:|---|',
         f'| **T1** PA@1 chấm đúng nhưng log **không chạy được** | **{len(t1)}** | theo M của SCLogger, các ca này còn được **cộng điểm nội dung** vì nội dung chỉ chấm khi PA@1 = 1 |',
         '| **T2** nội dung được tính đúng dù in sai lúc | — | nội dung chỉ chấm khi PA@1 = 1, nên không có loại này |',
         f'| **T3** PA@1 chấm 0 cho log đặt đúng | **{len(t3)}** | |',
         f'| **T4** cùng điểm 0 cho mọi kiểu sai | {len(t4)} | xem bảng chẩn đoán |',
         f'| **T5** PA@1 chấm đúng nhưng sai thứ tự | {len(t5)} | minh hoạ |', '',
         '**Chẩn đoán các ca PA@1 = 0 và RPA = 0:**', '', '| Verdict | Ý nghĩa | Số ca |', '|---|---|---:|',
         *[f'| `{k}` | {VERDICT_VI.get(k, k)} | {c} |' for k, c in diag.most_common()], '',
         '## 4. Ví dụ', '', '### T1. PA@1 chấm đúng nhưng log không chạy được → cần ER', '',
         f'*Lưu ý khi đọc T1: {t1_both}/{len(t1)} ca vẫn không chạy được nếu đọc N theo cách "chèn sau dòng N". Đọc câu trả lời thô thấy model thường **đếm sai dòng** (ví dụ viết "thêm sau câu gán X, ở dòng 11" nhưng dòng 11 lại là chính câu gán X). Prompt của SCLogger (theo Fig. 6) đưa code **không đánh số dòng** nhưng bắt model trả số dòng; AL-Bench cũng nhận xét "LLM không giỏi đếm số dòng". Lỗi này thuộc thiết kế của SCLogger, nhưng độ lớn của nó có thể khác ở SCLogger gốc.*', '',
         ex(t1, 0, 'Ví dụ T1-a', 'Log lệch ≤ 1 dòng, cùng block nên PA@1 = 1, và theo SCLogger còn được chấm nội dung; nhưng log không chạy được (đọc code để thấy lý do: nằm sau return/throw hoặc in biến khai báo phía sau).'),
         ex(t1, 1, 'Ví dụ T1-b', 'Tương tự.'), '',
         '### T3. PA@1 chấm 0 cho log đặt đúng → cần RPA / CA', '',
         ex(t3, 0, 'Ví dụ T3-a', 'Vị trí lệch nhưng cùng điều kiện, chạy được, không vượt qua câu lệnh làm đổi điều log mô tả.'), '',
         '### T4. Cùng điểm 0 cho mọi kiểu sai → cần CA (chẩn đoán)', '',
         ex([d for d in t4 if B(d)['verdict'] == 'wrong_condition:weaker'], 0, 'Ví dụ T4-a: in quá thường (loại lỗi phổ biến nhất)', 'Log bị đặt ra ngoài điều kiện của developer.'),
         ex([d for d in t4 if B(d)['verdict'] == 'wrong_condition:disjoint'], 0, 'Ví dụ T4-b: nhầm nhánh', 'Hai log không bao giờ cùng in.'), '',
         '### T5. PA@1 chấm đúng nhưng sai thứ tự (minh hoạ)', '',
         ex(t5, 0, 'Ví dụ T5-a', 'Log vượt qua một thao tác; tranh cãi được.'), '',
         'Prompt, input và output đầy đủ của từng ca: xem `cases/T*.md`.', '',
         '## 5. Giới hạn', '',
         '- **Bản xấp xỉ**: prompt chép từ hình, backbone khác (gpt-4o-mini), log slice và call graph xấp xỉ, gpt-4o-mini thường không theo định dạng nên phải đọc vị trí từ code trả về. Lỗi ở đây chưa chắc là lỗi của SCLogger gốc.',
         '- `AvaVarList.java` của tác giả khớp method theo **tên**: nếu một file có nhiều class con cùng có method trùng tên, biến của các method đó bị gộp vào danh sách. Giữ nguyên hành vi này.',
         '- Chỉ chạy 500 mẫu, chỉ trên Hadoop.',
         '- Tham chiếu "sai" là verifier của mình, so với một log gold.',
         '- Muốn chính xác cần xin tác giả prompt, pipeline hoặc output.', '']
    (folder/'README.md').write_text('\n'.join(L))
    return dict(ok=len(ok), T1=len(t1), T3=len(t3), T4=len(t4), T5=len(t5), pa1=mean('before', 'pa1'))


def build_overview(tool_stats, pdl, scl=None):
    alln = {k: v for k, v in tool_stats.items()}
    rows = []
    for name, s in alln.items():
        rows.append(f'| [{name}]({name}/README.md) | khớp chính xác | {s["ok"]:,} | {s["types"].get("T1", 0):,} (vị trí trùng y hệt: {s["t1_exact"]}) | {s["types"].get("T2", 0):,} | **{s["types"].get("T3", 0):,}** | {s["types"].get("T4", 0):,} | {s["types"].get("T5", 0):,} |')
    if scl:
        rows.insert(0, f'| [SCLogger](SCLogger/README.md) (**tái hiện xấp xỉ**, 500 mẫu Hadoop) | ±1 dòng, cùng block | {scl["ok"]} | **{scl["T1"]}** (PA@1 = 1) | — | {scl["T3"]} | {scl["T4"]} | {scl["T5"]} |')
    rows.insert(0, f'| [PDLogger](PDLogger/README.md) (tự tái hiện) | ±1 dòng, cùng block | {pdl["ok"]} | **{pdl["T1"]}** (PA@1 = 1) | — | {pdl["T3"]} (4 ca thật) | {pdl["T4"]} | {pdl["T5"]} |')
    L = ['# Các trường hợp metric của các công cụ sinh log chấm sai output của chính chúng', '',
         '*Tổng hợp cho thầy nhận xét, 15/10/2026. Mỗi công cụ có một thư mục riêng gồm `README.md` (phương pháp, metric của paper, dữ liệu lấy ở đâu, bảng số, ví dụ theo từng loại, giới hạn) và `cases/` (mỗi loại có `T*.md` dễ xem và `T*.csv` đầy đủ). Toàn bộ sinh tự động từ dữ liệu chấm lại bằng `build.py`, không chép tay.*', '',
         '## 1. Mục đích', '',
         'Trước khi đề xuất metric mới, cần chứng minh **metric hiện có không đánh giá đúng**. Chuỗi lập luận:', '',
         '> **Công cụ X tự đánh giá bằng metric M → M chấm sai trên output thật của X (có số, có ví dụ) → lặp lại cho nhiều X → đề xuất metric mới (CA, ER, RPA).**', '',
         'Thư mục này là phần "M chấm sai trên output thật của X" cho 7 công cụ: PDLogger (tự tái hiện), LANCE, LANCE 2.0, LEONID, FastLog, UniLog (output gốc), và **SCLogger (tái hiện xấp xỉ trên Hadoop, vì tác giả không công bố prompt và output; xem `SCLogger/`)**.', '',
         '## 2. Mỗi công cụ tự đánh giá thế nào (M)', '',
         '| Công cụ | Năm | Metric vị trí của paper | Level / message chấm khi nào | Kiểm log chạy được? | Kiểm điều kiện thực thi? |', '|---|---|---|---|---|---|',
         '| LANCE | ICSE 2022 | khớp chính xác (token) | độc lập với vị trí | chỉ đếm không parse được | không |',
         '| LANCE 2.0, LEONID | JSS 2024 | khớp chính xác | độc lập với vị trí | không | không |',
         '| FastLog | ISSTA 2024 | khớp chính xác (token) | độc lập với vị trí | không | không |',
         '| UniLog | ICSE 2024 | (paper đóng); AL-Bench chấm khớp chính xác dòng | độc lập với vị trí (AL-Bench) | AL-Bench: compile và chạy test trên khoảng 6% mẫu | không |',
         '| SCLogger | FSE 2024 | ±1 dòng, cùng block | chỉ khi vị trí đúng | không | không |',
         '| PDLogger | 2025 | ±1 dòng, cùng block | không ghi rõ | không | không |', '',
         'Trích dẫn nguyên văn cho từng ô: `analysis/logging_condition_study/KHAO_SAT_CACH_DANH_GIA.md`.', '',
         '## 3. Các loại trường hợp sai', '',
         '| Loại | Tên | Định nghĩa | Metric của mình cần cho loại này |', '|---|---|---|---|',
         *[f'| **{t}** | {n} | {d} | {need} |' for t, n, d, need in TYPES], '',
         '**Ba metric đề xuất** (định nghĩa đầy đủ trong `BAO_CAO_PAK_METRIC.md` mục 3):',
         '- **CA**: log có được in đúng những lúc log của developer được in không (điều kiện đường đi ∧ level, kiểm bằng Z3).',
         '- **ER**: log có chạy được không (tới được, biến đã khai báo); không cần gold.',
         '- **RPA**: log có nằm trong khoảng vị trí tương đương với developer không (cùng điều kiện, chạy được, không vượt qua câu lệnh làm đổi điều log mô tả).', '',
         '## 4. Kết quả tổng hợp', '',
         '| Công cụ | Metric vị trí của paper | Mẫu chấm được | **T1** cho điểm nhưng không chạy được | **T2** cộng điểm level/message cho log in sai lúc | **T3** chấm oan log đúng | **T4** vị trí sai, cùng điểm 0 | T5 sai thứ tự |', '|---|---|---:|---|---:|---:|---:|---:|',
         *rows, '',
         '**Đọc bảng:**',
         '1. **T1 có ở mọi công cụ.** Với nhóm khớp chính xác, có những log nằm **đúng y** vị trí developer nhưng in một biến khai báo ở dòng sau, nên không biên dịch được, mà metric vẫn cho điểm vị trí. Với PDLogger, 30 log nằm sau `return`/`throw` được PA@1 chấm đúng.',
         '2. **T2 lớn ở nhóm chấm level độc lập vị trí** (LANCE, LEONID, FastLog, UniLog): hàng trăm đến hàng nghìn log in sai lúc vẫn được cộng điểm level.',
         '3. **T3 nặng nhất ở UniLog trên AL-Bench**: phần lớn là lệch qua **một dòng trống** mà chính AL-Bench để lại ở chỗ log bị xoá (xem `UniLog/`). Riêng lỗi này chiếm khoảng 23% output.',
         '4. **T4: metric chỉ cho 0 điểm** cho mọi lỗi vị trí, trong khi 38–60% số lỗi đó là sai điều kiện thực thi (in quá thường, quá ít, nhầm nhánh).', '',
         '## 5. Nguồn dữ liệu', '',
         '| Công cụ | Ai chạy ra output | Dataset | File |', '|---|---|---|---|',
         '| PDLogger | **mình tái hiện** (prompt nguyên văn, gpt-4o-mini) | 1.000 method LogBench-O | `analysis/pdlogger_repro/runs/rerun_O/` |',
         '| LANCE | tác giả | test set LANCE, 12.020 mẫu | `analysis/external_methods/lance/` |',
         '| LANCE 2.0 | tác giả | test set LEONID, 28.698 mẫu | `analysis/external_methods/lance2/` |',
         '| LEONID | tác giả | test set LEONID, 28.698 mẫu | `analysis/external_methods/leonid/` |',
         '| FastLog | tác giả | test set LANCE, 12.020 mẫu | `analysis/external_methods/fastlog/` |',
         '| UniLog | **AL-Bench** (UniLog không công bố code) | AL-Bench, 39.600 mẫu | `analysis/external_methods/albench/` |',
         '| LANCE, LEONID, FastLog (bổ sung) | **AL-Bench** | AL-Bench, 39.600 mẫu | `analysis/external_methods/al_*` |', '',
         'Link gốc (repo, Google Drive) ghi trong README của từng công cụ.', '',
         '## 6. Giới hạn chung', '',
         '1. **Tham chiếu "sai" là verifier của mình**, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện. Pilot đọc tay trên PDLogger: khoảng 53% lỗi điều kiện là "log khác nhưng hợp lý", khoảng 28% là lỗi thật. Cần đánh giá bởi người (E6).',
         '2. **ER chưa kiểm bằng javac.** Các ví dụ T1 đã đọc tay: đều là dùng biến trước khai báo hoặc sau `return`/`throw`, chắc chắn không chạy được.',
         '3. **Mẫu có log trong lambda / lớp ẩn danh bị loại** (verifier chưa hỗ trợ): khoảng 2–12% tuỳ công cụ.',
         '4. **PDLogger là bản tái hiện** (gpt-4o-mini, không Joern). Các công cụ khác dùng output gốc của tác giả hoặc của AL-Bench.',
         '5. **T5 tranh cãi được**, chỉ dùng để minh hoạ.', '',
         '## 7. Câu hỏi muốn xin ý kiến thầy', '',
         '1. Các loại T1–T4 có đủ thuyết phục để làm phần "motivation" trước khi đề xuất CA / ER / RPA không?',
         '2. Phát hiện về **dòng trống của AL-Bench** (làm khoảng 23% output UniLog bị chấm sai vị trí) có nên đưa vào bài như một phát hiện về benchmark không?',
         '3. SCLogger đã có **bản tái hiện xấp xỉ** (500 mẫu Hadoop, dùng code phân tích tĩnh và chọn ví dụ mẫu của tác giả, prompt chép từ hình, gpt-4o-mini). Có nên email tác giả xin prompt / output để thay bằng bản chính xác không?', '',
         '## 8. Cách tạo lại', '',
         '```bash', 'cd analysis/external_methods', 'python rescore_lance.py lance     # tương tự: lance2, leonid, fastlog, al_lance, al_leonid, al_fastlog',
         'python rescore_unilog.py deepseek_base   # và warmup_cl', 'cd ../TRUONG_HOP_SAI && python build.py', '```', '']
    (HERE/'README.md').write_text('\n'.join(L))


if __name__ == '__main__':
    ts = {}
    for name, cfg in TOOLS.items():
        ts[name] = build_tool(name, cfg); print(name, dict(ts[name]['types']), ts[name]['ok'])
    pdl = build_pdlogger(); print('PDLogger', pdl)
    scl = build_sclogger(); print('SCLogger', scl)
    build_overview(ts, pdl, scl)

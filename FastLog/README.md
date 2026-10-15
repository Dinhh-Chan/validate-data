# FastLog: các trường hợp metric của công cụ chấm sai output của chính công cụ

*Sinh tự động bằng `analysis/TRUONG_HOP_SAI/build.py`. Danh sách mọi ca theo từng loại: `cases/T1.md` … `cases/T5.md` (bản dễ xem) và `cases/T*.csv` (đầy đủ). Định nghĩa các loại T1–T5: `../README.md`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** Xie et al. *FastLog: An End-to-End Method to Efficiently Generate and Insert Logging Statements*. ISSTA 2024. arXiv 2311.02862.

**Cách sinh log:** Hai giai đoạn: (1) model phân loại token chọn vị trí chèn, (2) PLBART sinh câu log tại vị trí đó; **không dùng prompt**.

**Metric của chính paper (M):**
- **Vị trí:** đúng khi chỉ số token dự đoán bằng chỉ số token gold (*"whether the predicted position or level is the same as the ground-truth label"*, §6; code `data["match"] = data["prediction"] == data["target"]`).
- **Level, message:** accuracy và BLEU/ROUGE trên **toàn bộ** mẫu, **độc lập** với vị trí (trong paper, level 71,6% > vị trí 70,5%).
- **Chạy được / điều kiện:** không kiểm.

## 2. Dữ liệu lấy ở đâu

**Nguồn:** `github.com/zhipeng-cai/FastLog` → Drive: `predictions/original-dataset/` (`results_beam_search.csv`, `positions.csv`, `statements_beam_search.csv`) và `datasets/raw/original-test/` (`input.txt`, `target.txt`, `logsta.txt`).

**Bản tải về:** `analysis/external_methods/fastlog/`.

**Dữ liệu gốc:** đúng test set của LANCE (12.020 mẫu).


**Kiểm tra cách chuyển đổi:** Vị trí khớp chính xác tính lại: **71,3%** (paper: 70,52%). So từng mẫu với phán quyết của chính FastLog (`True_Position == Pred_Position`): **trùng 10.338/10.339 mẫu**.

**Cách chấm lại:** output là method đã tách token (LANCE, LEONID, FastLog) hoặc code có thẻ dòng (UniLog). Mình xác định chỗ chèn của log gold và log sinh ra, xếp method mỗi câu lệnh một dòng, rồi (1) tính lại M đúng theo định nghĩa của paper, (2) chạy verifier (CA / ER / RPA). Script: `analysis/external_methods/rescore_lance.py`, `rescore_unilog.py`.

**Số mẫu chấm được: 10,339/12,020**

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 10,339 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 673 |
| dữ liệu gold không phải đúng một lần chèn | 466 |
| công cụ sửa cả code khác ngoài việc chèn log | 324 |
| vị trí không rơi vào ranh giới câu lệnh | 217 |
| log sinh ra làm hỏng cú pháp tại vị trí chèn | 1 |

## 3. Tổng hợp các trường hợp sai

Vị trí khớp chính xác theo M: **7,367/10,339 (71.3%)**. Một mẫu có thể thuộc nhiều loại.

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 14 | trong đó **5** ca vị trí trùng **y hệt** gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 830 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 153 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 2,819 | = toàn bộ 2,972 ca vị trí không khớp trừ T3 |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 34 |  |

**Chẩn đoán các ca vị trí không khớp** (M cho 0 điểm như nhau cho tất cả):

| Chẩn đoán của verifier (trên các ca vị trí không khớp) | Số ca | % |
|---|---:|---:|
| `wrong_condition:stronger`: in quá ít / sai phạm vi (thừa điều kiện) | 659 | 22.2% |
| `wrong_condition:weaker`: in quá thường (mất điều kiện) | 572 | 19.2% |
| `order_changed`: vượt qua một thao tác | 516 | 17.4% |
| `wrong_condition:disjoint`: nhầm nhánh (không bao giờ cùng in) | 322 | 10.8% |
| `log_order_changed`: đổi thứ tự với log khác | 291 | 9.8% |
| `wrong_condition:overlapping`: điều kiện khác | 228 | 7.7% |
| `value_changed`: giá trị biến được in đã đổi | 219 | 7.4% |
| `equivalent_move`: lệch nhưng tương đương | 153 | 5.1% |
| `invalid`: không chạy được | 12 | 0.4% |

### Bổ sung: FastLog trên AL-Bench (do nhóm AL-Bench chạy lại)

Nguồn: `res_all.zip` của AL-Bench. Chấm được **26,250/39,600** mẫu; vị trí khớp chính xác **58.9%** (AL-Bench Table 2 báo cáo FastLog PA 58,39%).

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 26,250 |
| công cụ sửa cả code khác ngoài việc chèn log | 9,865 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 2,292 |
| vị trí không rơi vào ranh giới câu lệnh | 964 |
| log sinh ra làm hỏng cú pháp tại vị trí chèn | 142 |
| input không parse được | 59 |
| dữ liệu gold không phải đúng một lần chèn | 23 |
| thư viện parse bị crash | 5 |

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 26 | trong đó **11** ca vị trí trùng y hệt gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 2,908 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 553 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 10,227 |  |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 64 |  |

## 4. Ví dụ theo từng loại

### T1. Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC → cần **ER**

Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau).

Số ca: **14**. Xem tất cả: [cases/T1.md](cases/T1.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T1.csv` (đầy đủ).

#### Ví dụ T1-a: vị trí trùng gold, in biến chưa khai báo (mẫu `3516`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    private RestResponse < ObjectMap > getAcl ( ) throws CatalogException , ClientException {
G>  logger . debug ( "Get Acl" ) ;
P>  logger . debug ( "Getting acl for study {}" , c . study ) ;
    StudyCommandOptions . AclsCommandOptions c = studiesCommandOptions . aclsCommandOptions ;
    ObjectMap params = new ObjectMap ( ) ;
    params . putIfNotEmpty ( "member" , c . memberId ) ;
    return openCGAClient . getStudyClient ( ) . acl ( getSingleValidStudy ( c . study ) , params ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác chỉ số token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `c.study`, nhưng `c` khai báo ở dòng sau.

#### Ví dụ T1-b (mẫu `5673`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override protected Object executeJob ( int gridSize , String type ) throws GridException {
G>  log . info ( ">>> Starting new grid node [currGridSize=" + gridSize + ", arg=" + type + "]" ) ;
    if ( type == null ) throw new IllegalArgumentException ( "Node type to start should be specified." ) ;
    GridConfiguration cfg = getConfig ( type ) ;
    String gridName = cfg . getGridName ( ) + " (" + UUID . randomUUID ( ) + ")" ;
    cfg . setGridName ( gridName ) ;
P>  log . info ( ">>> Starting Grid [nodeId=" + g . localNode ( ) . id ( ) + ", name='" + g . name ( ) + "']" ) ;
    Grid g = G . start ( cfg ) ;
    log . info ( ">>> Grid started [nodeId=" + g . localNode ( ) . id ( ) + ", name='" + g . name ( ) + "']" ) ;
    return true ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 0 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `g.localNode()` trước câu `Grid g = G.start(cfg);`. Level vẫn tính đúng.

### T2. Metric cộng điểm level / message cho log IN SAI LÚC → cần **CA**

Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** với log của developer: in quá thường, quá ít, nhầm nhánh.

Số ca: **830**. Xem tất cả: [cases/T2.md](cases/T2.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T2.csv` (đầy đủ).

#### Ví dụ T2-a: message và level trùng gold từng chữ, nhưng log bị đưa vào trong `if` (mẫu `4792`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void postProcessContext ( DeploymentUnit deploymentUnit , StandardContext webContext ) {
G>  logger . debug ( "postProcessContext() for " + deploymentUnit . getName ( ) ) ;
    if ( webContext instanceof SIPWebContext ) {
P>  logger . debug ( "postProcessContext() for " + deploymentUnit . getName ( ) ) ;
    ( ( SIPWebContext ) webContext ) . postProcessContext ( deploymentUnit ) ;
    }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in mọi lần; log sinh ra chỉ in khi `webContext instanceof SIPWebContext` (`stronger`).

#### Ví dụ T2-b (mẫu `6841`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void stop ( ) {
P>  log . info ( "Stopping endpoint" ) ;
    if ( selectorThread . isRunning ( ) ) {
G>  LOGGER . info ( "Stopping low level grizzly container" ) ;
    selectorThread . stopEndpoint ( ) ;
    }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:weaker` (in quá thường (mất điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log sinh ra in **mọi lần** gọi `stop()`, gold chỉ in khi `selectorThread.isRunning()` (`weaker`).

### T3. Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) → cần **RPA**

Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương.

Số ca: **153**. Xem tất cả: [cases/T3.md](cases/T3.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T3.csv` (đầy đủ).

#### Ví dụ T3-a (mẫu `5777`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    private void setXATerminator ( final XATerminator terminator ) {
P>  logger . debug ( "setXATerminator(" + terminator + ")" ) ;
    this . xaTerminator = terminator ;
G>  logger . debug ( "XATerminator set." ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** chỉ vượt qua phép gán `this.xaTerminator`.

#### Ví dụ T3-b (mẫu `10515`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void commit ( Xid xid , boolean b ) throws XAException {
P>  logger . debug ( "DummyXAResource - commit invoked" ) ;
    this . commitStarted = true ;
G>  logger . debug ( "Committing XA TX. {}, One Face: {}" , xid , b ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** chỉ vượt qua phép gán `this.commitStarted`.

### T4. Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) → cần **CA (chẩn đoán)**

Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold.

Số ca: **2,819**. Xem tất cả: [cases/T4.md](cases/T4.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T4.csv` (đầy đủ).

#### Ví dụ T4-a: log chạy mỗi vòng lặp thay vì một lần (mẫu `2080`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void performAction ( List < SimpleClient > objects ) {
    for ( SimpleClient simpleClient : objects ) {
    processedCount ++ ;
P>  LOGGER . info ( "Processed: " + simpleClient . getId ( ) ) ;
    }
G>  LOG . info ( "Total processed: " + processedCount ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in tổng kết **một lần** sau vòng lặp; log sinh ra in **mỗi phần tử** (`stronger`).

### T5. Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) → cần **RPA**

Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính.

Số ca: **34**. Xem tất cả: [cases/T5.md](cases/T5.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T5.csv` (đầy đủ).

#### Ví dụ T5-a: thứ tự làm đổi kết quả thật (mẫu `7809`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Test public void testDebugShortCircuit ( ) {
P>  logger . debug ( "hello" ) ;
    inner . setLevel ( Level . OFF ) ;
G>  logger . debug ( "hello" ) ;
    assertTrue ( handler . isEmpty ( ) ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác chỉ số token) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `order_changed` (vượt qua một thao tác) · CA 1 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold `logger.debug("hello")` được gọi **sau** `inner.setLevel(Level.OFF)` để kiểm rằng log bị chặn; log sinh ra gọi **trước**, nên test kiểm tra một điều khác hẳn.

*Nhiều ca T5 là công cụ log một sự kiện khác nhưng hợp lý; cần đọc message mới phán được. Chỉ dùng để minh hoạ.*

## 5. Giới hạn

- Tham chiếu đúng/sai là verifier của mình, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện (T2, T4). Cần đánh giá bởi người (E6).
- ER chưa kiểm bằng javac; các ví dụ T1 ở trên đã đọc tay, đều là dùng biến trước khai báo, chắc chắn không biên dịch được.
- Mẫu có log nằm trong lambda / lớp ẩn danh bị loại, vì verifier chưa hỗ trợ.
- Level và message so khớp chính xác (đúng định nghĩa của paper); BLEU/ROUGE chưa tính lại.

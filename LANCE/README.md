# LANCE: các trường hợp metric của công cụ chấm sai output của chính công cụ

*Sinh tự động bằng `analysis/TRUONG_HOP_SAI/build.py`. Danh sách mọi ca theo từng loại: `cases/T1.md` … `cases/T5.md` (bản dễ xem) và `cases/T*.csv` (đầy đủ). Định nghĩa các loại T1–T5: `../README.md`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** Mastropaolo, Pascarella, Bavota. *Using Deep Learning to Generate Complete Log Statements*. ICSE 2022. arXiv 2201.04837.

**Cách sinh log:** Model T5 (60M tham số) được huấn luyện trước rồi fine-tune; **không dùng prompt**. Input là method đã xoá một log; output là toàn bộ method có chèn log (tự chọn vị trí, level, message).

**Metric của chính paper (M):**
- **Vị trí:** đúng khi trùng vị trí developer đặt, so theo vị trí token (*"injecting it in the correct position in the method (i.e., the same position adopted by developers)"*, §3.1). Không có dung sai.
- **Level, message:** khớp chính xác, chấm **độc lập** với vị trí (*"the log level was correctly predicted, independently from the prediction of the position and message"*, Table 3).
- **Chạy được:** chỉ báo tỉ lệ output không parse được bằng JavaParser (2,33%). Không kiểm compile, không kiểm điều kiện.

## 2. Dữ liệu lấy ở đâu

**Nguồn:** gói replication của tác giả, `github.com/antonio-mastropaolo/LANCE` → Google Drive.

- Test set: thư mục `Fine-tuning/test.tsv` (Drive id `1o2ScvTnDQaxH-Y5ACPvFKWnM-wkY_g5z`): 12.020 dòng `input <TAB> target` (method đã xoá log / method gốc).
- Output: biến thể tốt nhất (Denoising), `predictions.txt` (Drive id `1CdNUuVo2glDjV7IQ4cR4LbdZXlXEi4Ek`): 12.020 method có chèn log.
- Kết quả tác giả: `Stats.txt` (khớp số trong paper), `correctLogPosition/Level/Message.csv`, `ID_Perfect.txt`.
**Bản tải về:** `analysis/external_methods/lance/`.

**Dữ liệu gốc của test set:** method Java từ 1.465 project GitHub có dùng Log4j (lấy theo file POM); method dài 10–512 token; đã bỏ trùng.

**Lưu ý:** các file kết quả theo từng mẫu của tác giả (`correctLog*.csv`) **bị lệch chỉ số** so với `predictions.txt` (dòng 30 chứa prediction của một method khác), nên mình **tự tính lại** metric theo định nghĩa trong paper và không dùng file đó. Các con số tổng (`Stats.txt`) vẫn khớp paper.


**Kiểm tra cách chuyển đổi:** Tỉ lệ vị trí khớp chính xác mình tính lại trên các mẫu chấm được: **71,0%** (paper: 65,4% trên toàn bộ 12.020 mẫu, tính cả mẫu không parse được).

**Cách chấm lại:** output là method đã tách token (LANCE, LEONID, FastLog) hoặc code có thẻ dòng (UniLog). Mình xác định chỗ chèn của log gold và log sinh ra, xếp method mỗi câu lệnh một dòng, rồi (1) tính lại M đúng theo định nghĩa của paper, (2) chạy verifier (CA / ER / RPA). Script: `analysis/external_methods/rescore_lance.py`, `rescore_unilog.py`.

**Số mẫu chấm được: 10,500/12,020**

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 10,500 |
| công cụ sửa cả code khác ngoài việc chèn log | 756 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 648 |
| vị trí không rơi vào ranh giới câu lệnh | 115 |
| dữ liệu gold không phải đúng một lần chèn | 1 |

## 3. Tổng hợp các trường hợp sai

Vị trí khớp chính xác theo M: **7,451/10,500 (71.0%)**. Một mẫu có thể thuộc nhiều loại.

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 53 | trong đó **24** ca vị trí trùng **y hệt** gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 848 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 147 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 2,902 | = toàn bộ 3,049 ca vị trí không khớp trừ T3 |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 19 |  |

**Chẩn đoán các ca vị trí không khớp** (M cho 0 điểm như nhau cho tất cả):

| Chẩn đoán của verifier (trên các ca vị trí không khớp) | Số ca | % |
|---|---:|---:|
| `wrong_condition:stronger`: in quá ít / sai phạm vi (thừa điều kiện) | 701 | 23.0% |
| `wrong_condition:weaker`: in quá thường (mất điều kiện) | 544 | 17.8% |
| `order_changed`: vượt qua một thao tác | 530 | 17.4% |
| `wrong_condition:disjoint`: nhầm nhánh (không bao giờ cùng in) | 346 | 11.3% |
| `value_changed`: giá trị biến được in đã đổi | 274 | 9.0% |
| `log_order_changed`: đổi thứ tự với log khác | 238 | 7.8% |
| `wrong_condition:overlapping`: điều kiện khác | 228 | 7.5% |
| `equivalent_move`: lệch nhưng tương đương | 147 | 4.8% |
| `invalid`: không chạy được | 41 | 1.3% |

### Bổ sung: LANCE trên AL-Bench (do nhóm AL-Bench chạy lại)

Nguồn: `res_all.zip` của AL-Bench. Chấm được **22,150/39,600** mẫu; vị trí khớp chính xác **57.9%** (AL-Bench Table 2 báo cáo LANCE PA 35,97%, tính trên mọi mẫu).

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 22,150 |
| công cụ sửa cả code khác ngoài việc chèn log | 13,967 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 2,178 |
| log sinh ra làm hỏng cú pháp tại vị trí chèn | 783 |
| vị trí không rơi vào ranh giới câu lệnh | 480 |
| input không parse được | 42 |

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 260 | trong đó **75** ca vị trí trùng y hệt gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 2,387 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 458 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 8,873 |  |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 13 |  |

## 4. Ví dụ theo từng loại

### T1. Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC → cần **ER**

Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau).

Số ca: **53**. Xem tất cả: [cases/T1.md](cases/T1.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T1.csv` (đầy đủ).

#### Ví dụ T1-a: vị trí trùng gold, nhưng in biến chưa khai báo (mẫu `3293`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public Connection accept ( final boolean close ) throws IOException {
G>  log . debug ( "Accepting" ) ;
P>  log . debug ( "Accepted: {}" , socket ) ;
    Socket socket = serverSocket . accept ( ) ;
    log . debug ( "Accepted: {}" , socket ) ;
    if ( close ) {
    close ( ) ;
    }
    return new ConnectionImpl ( socket ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác vị trí token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `socket`, nhưng `socket` khai báo ở dòng ngay sau, nên không biên dịch được ("cannot find symbol").

#### Ví dụ T1-b: message và level trùng gold từng chữ, nhưng đặt trước khai báo (mẫu `4730`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Test public void listAllPreparedQueriesByUser ( ) throws Exception {
    String user = "diff" , pass = "diff" ;
    String session1 = sHelper . openSession ( user , pass , lens . getCurrentDB ( ) ) ;
P>  logger . info ( "PREPARE QUERY HANDLE : " + queryPrepareHandle1 ) ;
    QueryPrepareHandle queryPrepareHandle1 = qHelper . submitPreparedQuery ( QueryInventory . QUERY ) ;
    Assert . assertNotEquals ( queryPrepareHandle1 , null , "Query Execute Failed" ) ;
G>  logger . info ( "PREPARE QUERY HANDLE : " + queryPrepareHandle1 ) ;
    QueryPrepareHandle queryPrepareHandle2 = qHelper . submitPreparedQuery ( QueryInventory . QUERY , null , session1 ) ;
    Assert . assertNotEquals ( queryPrepareHandle2 , null , "Query Execute Failed" ) ;
    logger . info ( "PREPARE QUERY HANDLE : " + queryPrepareHandle2 ) ;
    List < QueryPrepareHandle > list = qHelper . getPreparedQueryHandleList ( null , lens . getUserName ( ) ) ;
    Assert . assertTrue ( list . contains ( queryPrepareHandle1 ) , "List of All QueryPreparedHandle By user failed" ) ;
    list = qHelper . getPreparedQueryHandleList ( null , user ) ;
    Assert . assertTrue ( list . contains ( queryPrepareHandle2 ) , "List of All QueryPreparedHandle By user failed" ) ;
    list = qHelper . getPreparedQueryHandleList ( null , "all" ) ;
    Assert . assertTrue ( list . contains ( queryPrepareHandle1 ) , "List of All QueryPreparedHandle by 'all' user failed" ) ;
    Assert . assertTrue ( list . contains ( queryPrepareHandle2 ) , "List of All QueryPreparedHandle by 'all' user failed" ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `queryPrepareHandle1` trước câu khai báo biến này, nên không biên dịch được. Paper vẫn tính level đúng, message đúng.

### T2. Metric cộng điểm level / message cho log IN SAI LÚC → cần **CA**

Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** với log của developer: in quá thường, quá ít, nhầm nhánh.

Số ca: **848**. Xem tất cả: [cases/T2.md](cases/T2.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T2.csv` (đầy đủ).

#### Ví dụ T2-a: message và level trùng gold, nhưng log bị đưa vào trong `if` (mẫu `4792`)

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

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in **mọi lần** gọi method; log sinh ra chỉ in khi `webContext instanceof SIPWebContext` (`stronger`).

#### Ví dụ T2-b (mẫu `835`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ VisibleForTesting protected void timeoutPendingSlotRequest ( SlotRequestId slotRequestId ) {
G>  log . info ( "Pending slot request [{}] timed out." , slotRequestId ) ;
    final PendingRequest pendingRequest = removePendingRequest ( slotRequestId ) ;
    if ( pendingRequest != null ) {
P>  log . info ( "Request for slot request id {} timed out in SlotPool." , slotRequestId ) ;
    pendingRequest . getAllocatedSlotFuture ( ) . completeExceptionally ( new TimeoutException ( "Pending slot request timed out in SlotPool." ) ) ;
    }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in **mọi lần** timeout; log sinh ra chỉ in khi `pendingRequest != null` (`stronger`). Level vẫn tính đúng.

### T3. Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) → cần **RPA**

Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương.

Số ca: **147**. Xem tất cả: [cases/T3.md](cases/T3.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T3.csv` (đầy đủ).

#### Ví dụ T3-a (mẫu `2157`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void setBlobStore ( BlobStore blobStore ) {
G>  log . info ( "Internal blob store set: {}" , blobStore ) ;
    splitBlobStore = new DefaultSplitBlobStore ( repositoryDir , blobStore , newBlobStore ) ;
P>  log . info ( "Inserting blobBlobStore: {}" , blobStore ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** giữa hai vị trí chỉ có phép gán field `splitBlobStore`, mà log không in field đó; thứ tự không đổi gì.

#### Ví dụ T3-b (mẫu `6343`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void start ( Map < String , String > configProps ) {
G>  LOG . info ( "Connector config keys: {}" , String . join ( ", " , configProps . keySet ( ) ) ) ;
    this . configProps = configProps ;
P>  logger . info ( "Loaded config this connector will handle the following config: {}" , this . connectorName ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** giữa hai vị trí chỉ có phép gán `this.configProps`; tương đương.

### T4. Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) → cần **CA (chẩn đoán)**

Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold.

Số ca: **2,902**. Xem tất cả: [cases/T4.md](cases/T4.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T4.csv` (đầy đủ).

#### Ví dụ T4-a: log chạy mỗi vòng lặp thay vì một lần (mẫu `10658`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    private void loadTimelinesFromTableProperties ( UpdatePeriod updatePeriod , String storageTableName , String timeLineKey ) throws HiveException , LensException 
G>  log . info ( "loading from table properties: {}" , storageTableName ) ;
    for ( String partCol : getTimePartColNamesOfTable ( storageTableName ) ) {
    ensureEntry ( timeLineKey , storageTableName , updatePeriod , partCol ) . init ( getTable ( storageTableName ) ) ;
P>  log . info ( "Loaded time part histogram format for table: {}, timeLineKey: {}" , storageTableName , timeLineKey ) ;
    }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in **một lần** trước vòng lặp; log sinh ra in **mỗi phần tử** (`stronger`). Vẫn chỉ là "vị trí sai" như mọi lỗi khác.

#### Ví dụ T4-b: nhầm nhánh (mẫu `3868`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void accept ( RedisMeta redisMeta ) {
    if ( ! isInterestedInCluster ( redisMeta . parent ( ) . parent ( ) ) ) {
P>  logger . info ( "Not doing anything on the cluster, not the copy of the data store in the cluster" ) ;
    return ;
    }
G>  logger . info ( "[Redis-Change] {}, master: {}" , redisMeta , redisMeta . isMaster ( ) ) ;
    instanceManager . getOrCreate ( redisMeta ) . getCheckInfo ( ) . isMaster ( redisMeta . isMaster ( ) ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:disjoint` (nhầm nhánh (không bao giờ cùng in)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log sinh ra nằm trong nhánh `return` sớm, gold ở nhánh tiếp tục xử lý: hai log không bao giờ cùng in (`disjoint`).

### T5. Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) → cần **RPA**

Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính.

Số ca: **19**. Xem tất cả: [cases/T5.md](cases/T5.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T5.csv` (đầy đủ).

#### Ví dụ T5-a (mẫu `2117`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override protected void shutDown ( ) throws Exception {
    logger . info ( "Shutting down job scheduler" ) ;
    service . shutdown ( ) ;
G>  logger . info ( "Job scheduler shut down" ) ;
    super . shutDown ( ) ;
P>  logger . info ( "Job scheduler shut down" ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí token) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `order_changed` (vượt qua một thao tác) · CA 1 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** "Job scheduler shut down" bị in **sau** `super.shutDown()`, trong khi gold in ngay sau khi tắt service và trước `super.shutDown()`.

*Nhiều ca T5 là công cụ log một sự kiện khác nhưng hợp lý; cần đọc message mới phán được. Chỉ dùng để minh hoạ.*

## 5. Giới hạn

- Tham chiếu đúng/sai là verifier của mình, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện (T2, T4). Cần đánh giá bởi người (E6).
- ER chưa kiểm bằng javac; các ví dụ T1 ở trên đã đọc tay, đều là dùng biến trước khai báo, chắc chắn không biên dịch được.
- Mẫu có log nằm trong lambda / lớp ẩn danh bị loại, vì verifier chưa hỗ trợ.
- Level và message so khớp chính xác (đúng định nghĩa của paper); BLEU/ROUGE chưa tính lại.

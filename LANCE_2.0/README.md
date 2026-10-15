# LANCE_2.0: các trường hợp metric của công cụ chấm sai output của chính công cụ

*Sinh tự động bằng `analysis/TRUONG_HOP_SAI/build.py`. Danh sách mọi ca theo từng loại: `cases/T1.md` … `cases/T5.md` (bản dễ xem) và `cases/T*.csv` (đầy đủ). Định nghĩa các loại T1–T5: `../README.md`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** LANCE 2.0 = LANCE được huấn luyện lại trên dataset của paper LEONID: Mastropaolo, Ferrari, Pascarella, Bavota. *Log statement generation via deep learning: Widening the support provided to developers*. JSS 2024. arXiv 2311.04587.

**Cách sinh log:** Model T5 như LANCE, huấn luyện lại trên dataset lớn hơn; **không dùng prompt**.

**Metric của chính paper (M):**
- **Vị trí, tên biến logger, level, message:** khớp chính xác; mỗi thành phần chấm **độc lập** (*"correctly predicted (✓), independently from whether the other three components were correct or not"*, §5.1).
- **Thêm:** BLEU, METEOR, ROUGE, Levenshtein cho message.
- **Chạy được / điều kiện:** không kiểm.

## 2. Dữ liệu lấy ở đâu

**Nguồn:** `github.com/antonio-mastropaolo/automating-logging-acitivities` → Drive, thư mục prediction LANCE-2.0 (id `1R4ZfUcVuvHfPKd5YnLFz-Uw0dp5xzUKf`): `inputs`, `predictions`, `targets` (28.698 dòng mỗi file).

**Bản tải về:** `analysis/external_methods/lance2/`.

**Dữ liệu gốc:** method Java từ 2.978 project GitHub dùng Log4j/SLF4J (Maven/Gradle); test single-log 28.698 mẫu.


**Kiểm tra cách chuyển đổi:** Vị trí khớp chính xác tính lại: **83,9%** (paper: 82,28%).

**Cách chấm lại:** output là method đã tách token (LANCE, LEONID, FastLog) hoặc code có thẻ dòng (UniLog). Mình xác định chỗ chèn của log gold và log sinh ra, xếp method mỗi câu lệnh một dòng, rồi (1) tính lại M đúng theo định nghĩa của paper, (2) chạy verifier (CA / ER / RPA). Script: `analysis/external_methods/rescore_lance.py`, `rescore_unilog.py`.

**Số mẫu chấm được: 27,197/28,698**

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 27,197 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 578 |
| vị trí không rơi vào ranh giới câu lệnh | 575 |
| công cụ sửa cả code khác ngoài việc chèn log | 330 |
| dữ liệu gold không phải đúng một lần chèn | 18 |

## 3. Tổng hợp các trường hợp sai

Vị trí khớp chính xác theo M: **22,818/27,197 (83.9%)**. Một mẫu có thể thuộc nhiều loại.

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 35 | trong đó **19** ca vị trí trùng **y hệt** gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 836 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 385 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 3,994 | = toàn bộ 4,379 ca vị trí không khớp trừ T3 |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 61 |  |

**Chẩn đoán các ca vị trí không khớp** (M cho 0 điểm như nhau cho tất cả):

| Chẩn đoán của verifier (trên các ca vị trí không khớp) | Số ca | % |
|---|---:|---:|
| `order_changed`: vượt qua một thao tác | 1,339 | 30.6% |
| `wrong_condition:stronger`: in quá ít / sai phạm vi (thừa điều kiện) | 894 | 20.4% |
| `wrong_condition:weaker`: in quá thường (mất điều kiện) | 562 | 12.8% |
| `value_changed`: giá trị biến được in đã đổi | 454 | 10.4% |
| `equivalent_move`: lệch nhưng tương đương | 385 | 8.8% |
| `wrong_condition:disjoint`: nhầm nhánh (không bao giờ cùng in) | 339 | 7.7% |
| `log_order_changed`: đổi thứ tự với log khác | 302 | 6.9% |
| `wrong_condition:overlapping`: điều kiện khác | 80 | 1.8% |
| `invalid`: không chạy được | 24 | 0.5% |

## 4. Ví dụ theo từng loại

### T1. Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC → cần **ER**

Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau).

Số ca: **35**. Xem tất cả: [cases/T1.md](cases/T1.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T1.csv` (đầy đủ).

#### Ví dụ T1-a (mẫu `7910`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public ApiUser2 removeUser ( String mockUuid , String userName ) {
G>  LOGGER . info ( "remove user by {} in cm for {}" , userName , mockUuid ) ;
P>  LOGGER . info ( "remove user in {}, user: {}" , mockUuid , apiUser2 ) ;
    ApiUser2 apiUser2 = getApiUser2 ( mockUuid , userName ) ;
    read ( mockUuid ) . getUsers ( ) . remove ( apiUser2 ) ;
    return apiUser2 ;
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `apiUser2` trước câu khai báo `ApiUser2 apiUser2 = …`.

#### Ví dụ T1-b (mẫu `8952`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public RemoteSession establishSession ( ) {
G>  logger . debug ( "Session requested by client" ) ;
P>  logger . debug ( "Establishing client session: " + session ) ;
    RemoteSession session = createServerSession ( ) . getSession ( ) ;
    logger . debug ( "Established client session: " + session ) ;
    return session ;
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `session` trước câu khai báo `RemoteSession session = …`.

### T2. Metric cộng điểm level / message cho log IN SAI LÚC → cần **CA**

Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** với log của developer: in quá thường, quá ít, nhầm nhánh.

Số ca: **836**. Xem tất cả: [cases/T2.md](cases/T2.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T2.csv` (đầy đủ).

#### Ví dụ T2-a: log bị đặt sau một `return` có điều kiện (mẫu `1101`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public boolean handleEntry ( Long key , Long value , ByteBuffer meta ) {
G>  LOG . info ( "Row : " + key + " IndexValue: " + value + " Meta: " + LongSerializer . get ( ) . fromByteBuffer ( meta ) ) ;
    if ( key % 2 == 1 ) return false ;
P>  log . info ( "Ignore entry {}:{}" , key , value ) ;
    return true ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in **mọi lần**; log sinh ra chỉ in khi `key % 2 != 1` (`stronger`).

#### Ví dụ T2-b (mẫu `26454`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public Message receive ( long timeout ) throws JMSException {
P>  logger . trace ( "receive called - full: {}" , this ) ;
    if ( this . closed || this . closing ) throw new IllegalStateException ( "Consumer is closed or closing." ) ;
G>  logger . trace ( "receive(timeout={}ms)" , timeout ) ;
    return receive ( timeout == 0 ? new TimeTracker ( ) : new TimeTracker ( timeout , TimeUnit . MILLISECONDS ) ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:weaker` (in quá thường (mất điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log sinh ra in cả khi consumer đã đóng (trước lệnh `throw`), còn gold chỉ in khi chưa đóng (`weaker`).

### T3. Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) → cần **RPA**

Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương.

Số ca: **385**. Xem tất cả: [cases/T3.md](cases/T3.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T3.csv` (đầy đủ).

#### Ví dụ T3-a (mẫu `1548`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Autowired public void setUserFeedback ( IUserFeedback userFeedback ) {
P>  logger . info ( "Setting the userFeedback" ) ;
    this . userFeedback = userFeedback ;
G>  LOG . info ( "[DependencyInjection] IUserFeedback injected" ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** chỉ vượt qua phép gán field `this.userFeedback`, mà log không in field này.

#### Ví dụ T3-b (mẫu `50`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void init ( ) {
P>  log . debug ( "init()" ) ;
    postponedDspConsensusResultsMap = new ConcurrentHashMap < > ( ) ;
G>  log . info ( "{} is up" , this . getClass ( ) . getSimpleName ( ) ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **sai** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** chỉ vượt qua phép gán field.

### T4. Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) → cần **CA (chẩn đoán)**

Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold.

Số ca: **3,994**. Xem tất cả: [cases/T4.md](cases/T4.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T4.csv` (đầy đủ).

#### Ví dụ T4-a (mẫu `22487`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public synchronized void releaseRebalancingPermit ( int nodeId ) {
    boolean removed = rebalancePermits . remove ( nodeId ) ;
G>  logger . info ( "Releasing rebalancing permit for node id " + nodeId + ", returned: " + removed ) ;
    if ( ! removed ) throw new VoldemortException ( new IllegalStateException ( "Invalid state, must hold a " + "permit to release" ) ) ;
P>  logger . info ( "Release rebalancing permit for node " + nodeId + ", returned " + removed ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log bị đặt sau `if (!removed) throw …`, nên chỉ in khi thành công (`stronger`); vẫn chỉ là "sai vị trí".

### T5. Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) → cần **RPA**

Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính.

Số ca: **61**. Xem tất cả: [cases/T5.md](cases/T5.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T5.csv` (đầy đủ).

#### Ví dụ T5-a (mẫu `6047`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ ExceptionHandler ( RestServiceException . class ) public void handleException ( RestServiceException ex , HttpServletResponse response ) throws IOException {
P>  log . error ( ex ) ;
    response . sendError ( HttpServletResponse . SC_INTERNAL_SERVER_ERROR , ex . getMessage ( ) ) ;
G>  log . error ( ex ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `order_changed` (vượt qua một thao tác) · CA 1 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log lỗi được in trước `response.sendError(...)` thay vì sau; tranh cãi được.

*Nhiều ca T5 là công cụ log một sự kiện khác nhưng hợp lý; cần đọc message mới phán được. Chỉ dùng để minh hoạ.*

## 5. Giới hạn

- Tham chiếu đúng/sai là verifier của mình, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện (T2, T4). Cần đánh giá bởi người (E6).
- ER chưa kiểm bằng javac; các ví dụ T1 ở trên đã đọc tay, đều là dùng biến trước khai báo, chắc chắn không biên dịch được.
- Mẫu có log nằm trong lambda / lớp ẩn danh bị loại, vì verifier chưa hỗ trợ.
- Level và message so khớp chính xác (đúng định nghĩa của paper); BLEU/ROUGE chưa tính lại.

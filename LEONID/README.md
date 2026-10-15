# LEONID: các trường hợp metric của công cụ chấm sai output của chính công cụ

*Sinh tự động bằng `analysis/TRUONG_HOP_SAI/build.py`. Danh sách mọi ca theo từng loại: `cases/T1.md` … `cases/T5.md` (bản dễ xem) và `cases/T*.csv` (đầy đủ). Định nghĩa các loại T1–T5: `../README.md`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** Mastropaolo, Ferrari, Pascarella, Bavota. *Log statement generation via deep learning: Widening the support provided to developers*. JSS 2024. arXiv 2311.04587.

**Cách sinh log:** Model T5 kết hợp truy hồi thông tin: input có thêm k = 5 log message tương tự lấy bằng Jaccard; **không dùng prompt LLM**.

**Metric của chính paper (M):**
- Giống LANCE 2.0: vị trí, tên biến logger, level, message khớp chính xác, chấm độc lập; thêm BLEU, METEOR, ROUGE.
- **Chạy được / điều kiện:** không kiểm.

## 2. Dữ liệu lấy ở đâu

**Nguồn:** cùng repo với LANCE 2.0 → Drive, `LEONID Single Log/TOP-5/Test/` (`inputs`, `predictions`, `targets`; id thư mục `1VTD6M5bt8LYJYnOTzcLn0j4aERrJu-Yv`).

**Bản tải về:** `analysis/external_methods/leonid/`. Input có dạng `b'SINGLE_LOG_INJECTION: <method> <log_message> … </log_message>'`; mình bỏ phần log message mẫu ở cuối để lấy method.

**Dữ liệu gốc:** như LANCE 2.0 (28.698 mẫu test).


**Kiểm tra cách chuyển đổi:** Vị trí khớp chính xác tính lại: **84,0%** (paper: 82,35%).

**Cách chấm lại:** output là method đã tách token (LANCE, LEONID, FastLog) hoặc code có thẻ dòng (UniLog). Mình xác định chỗ chèn của log gold và log sinh ra, xếp method mỗi câu lệnh một dòng, rồi (1) tính lại M đúng theo định nghĩa của paper, (2) chạy verifier (CA / ER / RPA). Script: `analysis/external_methods/rescore_lance.py`, `rescore_unilog.py`.

**Số mẫu chấm được: 27,191/28,698**

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 27,191 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 588 |
| vị trí không rơi vào ranh giới câu lệnh | 578 |
| công cụ sửa cả code khác ngoài việc chèn log | 323 |
| dữ liệu gold không phải đúng một lần chèn | 18 |

## 3. Tổng hợp các trường hợp sai

Vị trí khớp chính xác theo M: **22,844/27,191 (84.0%)**. Một mẫu có thể thuộc nhiều loại.

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 32 | trong đó **17** ca vị trí trùng **y hệt** gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 824 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 406 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 3,941 | = toàn bộ 4,347 ca vị trí không khớp trừ T3 |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 98 |  |

**Chẩn đoán các ca vị trí không khớp** (M cho 0 điểm như nhau cho tất cả):

| Chẩn đoán của verifier (trên các ca vị trí không khớp) | Số ca | % |
|---|---:|---:|
| `order_changed`: vượt qua một thao tác | 1,325 | 30.5% |
| `wrong_condition:stronger`: in quá ít / sai phạm vi (thừa điều kiện) | 883 | 20.3% |
| `wrong_condition:weaker`: in quá thường (mất điều kiện) | 556 | 12.8% |
| `value_changed`: giá trị biến được in đã đổi | 425 | 9.8% |
| `equivalent_move`: lệch nhưng tương đương | 406 | 9.3% |
| `wrong_condition:disjoint`: nhầm nhánh (không bao giờ cùng in) | 320 | 7.4% |
| `log_order_changed`: đổi thứ tự với log khác | 317 | 7.3% |
| `wrong_condition:overlapping`: điều kiện khác | 92 | 2.1% |
| `invalid`: không chạy được | 23 | 0.5% |

### Bổ sung: LEONID trên AL-Bench (do nhóm AL-Bench chạy lại)

Nguồn: `res_all.zip` của AL-Bench. Chấm được **8,624/39,600** mẫu; vị trí khớp chính xác **73.6%** (AL-Bench báo cáo LEONID_S PA 11,26%, tính trên mọi mẫu).

| Trạng thái | Số mẫu |
|---|---:|
| công cụ sửa cả code khác ngoài việc chèn log | 29,105 |
| chấm được | 8,624 |
| log sinh ra làm hỏng cú pháp tại vị trí chèn | 921 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 749 |
| vị trí không rơi vào ranh giới câu lệnh | 174 |
| input không parse được | 27 |

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 30 | trong đó **16** ca vị trí trùng y hệt gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 535 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 119 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 2,155 |  |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 7 |  |

*Lưu ý: trên AL-Bench, LEONID sửa luôn code khác ngoài việc chèn log ở phần lớn mẫu (khả năng cao do method dài bị cắt ở 512 token), nên chỉ chấm được khoảng 22%; con số ở bảng này kém đại diện.*

## 4. Ví dụ theo từng loại

### T1. Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC → cần **ER**

Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau).

Số ca: **32**. Xem tất cả: [cases/T1.md](cases/T1.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T1.csv` (đầy đủ).

#### Ví dụ T1-a: vị trí trùng gold, in biến chưa khai báo (mẫu `21900`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Async ( "asyncExecutor" ) public synchronized void refreshSubTable ( ) {
G>  log . info ( "refreshSubTable." ) ;
P>  log . info ( "refreshSubTable, groupList size: {}" , groupList . size ( ) ) ;
    List < TbGroup > groupList = groupService . getGroupList ( null , DataStatus . NORMAL . getValue ( ) ) ;
    groupList . forEach ( group -> tableService . newSubTable ( group . getChainId ( ) , group . getGroupId ( ) ) ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `groupList` trước câu `List<TbGroup> groupList = …`.

#### Ví dụ T1-b (mẫu `25933`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Test public void testChange ( ) throws IOException {
G>  log . info ( "testChange: " ) ;
P>  log . info ( "testChange: data: %s" , data ) ;
    Map < String , Object > data = Maps . newHashMap ( ) ;
    testDocx ( true , "items_groovy.docx" , data ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `data` trước câu khai báo `data`.

#### Ví dụ T1-c: dùng biến của vòng lặp trước vòng lặp (mẫu `988`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void complete ( ValidationResult validationResult ) {
P>  LOG . info ( "{} started" , tripValidator . getClass ( ) . getSimpleName ( ) ) ;
    for ( TripValidator tripValidator : tripValidators ) {
G>  LOG . info ( "Running complete stage for {}" , tripValidator . getClass ( ) . getSimpleName ( ) ) ;
    tripValidator . complete ( validationResult ) ;
    LOG . info ( "{} finished" , tripValidator . getClass ( ) . getSimpleName ( ) ) ;
    }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 0 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** `tripValidator` chỉ tồn tại bên trong `for`. Paper vẫn tính level đúng.

### T2. Metric cộng điểm level / message cho log IN SAI LÚC → cần **CA**

Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** với log của developer: in quá thường, quá ít, nhầm nhánh.

Số ca: **824**. Xem tất cả: [cases/T2.md](cases/T2.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T2.csv` (đầy đủ).

#### Ví dụ T2-a (mẫu `14210`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    private boolean checkInvalidSides ( Rotation rotation , HexSidesSet impassable ) {
G>  log . trace ( "Check rotation {} against  impassable{}" , rotation , impassable ) ;
    if ( impassable == null ) return false ;
P>  log . trace ( "Checking whether a valid sides in rotation {}, trying again" , rotation ) ;
    return ( rotation . getConnectedSides ( ) . intersects ( impassable ) ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log bị đặt sau `if (impassable == null) return false;`, nên không in khi `impassable == null` (`stronger`).

#### Ví dụ T2-b: log ra khỏi vòng lặp (mẫu `2244`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void executeExternalManipulateScope ( SpontaneousScopeExternalContext context ) {
P>  log . debug ( "Registering jersey script to execute: {}" , context . getClient ( ) ) ;
    for ( CustomScriptConfiguration script : getScriptsToExecute ( context . getClient ( ) ) ) {
    executeExternalManipulateScope ( script , context ) ;
G>  log . debug ( "GrantedScopes {} after execution of interception script {}." , context . getGrantedScopes ( ) , script . getName ( ) ) ;
    }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:weaker` (in quá thường (mất điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold in **mỗi script** trong vòng lặp; log sinh ra in **một lần** trước vòng lặp (`weaker`).

### T3. Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) → cần **RPA**

Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương.

Số ca: **406**. Xem tất cả: [cases/T3.md](cases/T3.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T3.csv` (đầy đủ).

#### Ví dụ T3-a (mẫu `738`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Override public void lockReleased ( ) {
G>  logger . debug ( "TestCallback.lockReleased" ) ;
    released = true ;
P>  log . debug ( "lock released:" + this ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** chỉ vượt qua phép gán `released = true`, mà log không in biến này.

#### Ví dụ T3-b (mẫu `1548`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @ Autowired public void setUserFeedback ( IUserFeedback userFeedback ) {
P>  logger . info ( "setUserFeedback(IUserFeedback)" ) ;
    this . userFeedback = userFeedback ;
G>  LOG . info ( "[DependencyInjection] IUserFeedback injected" ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** chỉ vượt qua phép gán field.

### T4. Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) → cần **CA (chẩn đoán)**

Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold.

Số ca: **3,941**. Xem tất cả: [cases/T4.md](cases/T4.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T4.csv` (đầy đủ).

#### Ví dụ T4-a (mẫu `70`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void registerCommand ( GeyserCommand command ) {
    commands . put ( command . getName ( ) , command ) ;
G>  connector . getLogger ( ) . debug ( LanguageUtils . getLocaleStringLog ( "geyser.commands.registered" , command . getName ( ) ) ) ;
    if ( command . getAliases ( ) . isEmpty ( ) ) return ;
    for ( String alias : command . getAliases ( ) ) commands . put ( alias , command ) ;
P>  logger . debug ( "Registered a null command!" ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:stronger` (in quá ít / sai phạm vi (thừa điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log bị đặt sau `if (... isEmpty()) return;` và sau một vòng lặp (`stronger`).

### T5. Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) → cần **RPA**

Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính.

Số ca: **98**. Xem tất cả: [cases/T5.md](cases/T5.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T5.csv` (đầy đủ).

#### Ví dụ T5-a (mẫu `6250`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void handle ( StopGrinderMessage message ) {
G>  m_logger . info ( "Received a stop agent message" ) ;
    setReceived ( STOP ) ;
P>  LOG . info ( "Received a stop agent message" ) ;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác vị trí) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `order_changed` (vượt qua một thao tác) · CA 1 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log "Received a stop agent message" in sau `setReceived(STOP)` thay vì trước; tranh cãi được.

*Nhiều ca T5 là công cụ log một sự kiện khác nhưng hợp lý; cần đọc message mới phán được. Chỉ dùng để minh hoạ.*

## 5. Giới hạn

- Tham chiếu đúng/sai là verifier của mình, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện (T2, T4). Cần đánh giá bởi người (E6).
- ER chưa kiểm bằng javac; các ví dụ T1 ở trên đã đọc tay, đều là dùng biến trước khai báo, chắc chắn không biên dịch được.
- Mẫu có log nằm trong lambda / lớp ẩn danh bị loại, vì verifier chưa hỗ trợ.
- Level và message so khớp chính xác (đúng định nghĩa của paper); BLEU/ROUGE chưa tính lại.

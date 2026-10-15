# UniLog: các trường hợp metric của công cụ chấm sai output của chính công cụ

*Sinh tự động bằng `analysis/TRUONG_HOP_SAI/build.py`. Danh sách mọi ca theo từng loại: `cases/T1.md` … `cases/T5.md` (bản dễ xem) và `cases/T*.csv` (đầy đủ). Định nghĩa các loại T1–T5: `../README.md`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** Xu et al. *UniLog: Automatic Logging via LLM and In-Context Learning*. ICSE 2024 (bản đóng, không có bản mở). Output dùng ở đây do **AL-Bench** (Tan et al., arXiv 2502.03160) chạy lại và công bố.

**Cách sinh log:** LLM + in-context learning: prompt gồm 5 ví dụ mẫu, code đánh thẻ `<lineN>`; model trả `<lineK>câu log`. AL-Bench chạy với hai backbone: DeepSeek-V3 (UniLog_ds) và CodeLlama-7B (UniLog_cl).

**Metric của chính paper (M):**
- **AL-Bench chấm vị trí khớp chính xác dòng** (*"we rigorously compare the predicted positions … PA = P_c/N_a"*; code `if pos_gth == pos_pred`).
- **Level, message, biến:** chia cho toàn bộ mẫu, **độc lập** với vị trí.
- **Đánh giá động** (compile và chạy test) chỉ trên 2.238 mẫu; không kiểm điều kiện.
- Bài gốc UniLog: không truy cập được bản đầy đủ, nên không xác minh được metric gốc.

## 2. Dữ liệu lấy ở đâu

**Nguồn:** `github.com/shuaijiumei/logging-benchmark` → Drive AL-Bench, `static evaluation/res_all.zip` → `res_all/unilog/deepseek_base/static_test_data_deepseek_base_cleaned.json` và `…/warmup_cl/…` (39.600 bản ghi: `prompt`, `metadata.position` = dòng gold, `response` = `<lineK>câu log`).

**Bản tải về:** `analysis/external_methods/albench/`.

**Dữ liệu gốc:** AL-Bench, 10 project (Hadoop, Kafka, Flink, Pulsar, Doris, DBeaver, DolphinScheduler, Keycloak, ThingsBoard, ZooKeeper), 39.600 mẫu.

**Lưu ý quan trọng về dữ liệu:** input của AL-Bench để lại **một dòng trống** đúng chỗ log bị xoá, tức là lộ vị trí gold.


**Kiểm tra cách chuyển đổi:** Vị trí khớp chính xác tính lại (DeepSeek-V3): **37,9%** (AL-Bench Table 2: 37,11%). So từng mẫu với `pos_gth == pos_pred`: trùng 100%.

**Cách chấm lại:** output là method đã tách token (LANCE, LEONID, FastLog) hoặc code có thẻ dòng (UniLog). Mình xác định chỗ chèn của log gold và log sinh ra, xếp method mỗi câu lệnh một dòng, rồi (1) tính lại M đúng theo định nghĩa của paper, (2) chạy verifier (CA / ER / RPA). Script: `analysis/external_methods/rescore_lance.py`, `rescore_unilog.py`.

**Số mẫu chấm được: 34,440/39,600**

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 34,440 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 4,483 |
| không có output hợp lệ (không trả `<lineK>`, hoặc dòng ngoài phạm vi) | 460 |
| thư viện parse bị crash | 124 |
| input không parse được | 93 |

## 3. Tổng hợp các trường hợp sai

Vị trí khớp chính xác theo M: **13,068/34,440 (37.9%)**. Một mẫu có thể thuộc nhiều loại.

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 384 | trong đó **33** ca vị trí trùng **y hệt** gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 3,778 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 8,205 | **7,807** ca chỉ lệch qua **một dòng trống** do AL-Bench để lại |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 13,167 | = toàn bộ 21,372 ca vị trí không khớp trừ T3 |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 131 |  |

**Chẩn đoán các ca vị trí không khớp** (M cho 0 điểm như nhau cho tất cả):

| Chẩn đoán của verifier (trên các ca vị trí không khớp) | Số ca | % |
|---|---:|---:|
| `equivalent_move`: lệch nhưng tương đương | 8,205 | 38.4% |
| `wrong_condition:stronger`: in quá ít / sai phạm vi (thừa điều kiện) | 2,894 | 13.5% |
| `wrong_condition:weaker`: in quá thường (mất điều kiện) | 2,120 | 9.9% |
| `order_changed`: vượt qua một thao tác | 1,908 | 8.9% |
| `wrong_condition:disjoint`: nhầm nhánh (không bao giờ cùng in) | 1,799 | 8.4% |
| `log_order_changed`: đổi thứ tự với log khác | 1,391 | 6.5% |
| `wrong_condition:overlapping`: điều kiện khác | 1,351 | 6.3% |
| `value_changed`: giá trị biến được in đã đổi | 1,010 | 4.7% |
| `invalid`: không chạy được | 694 | 3.2% |

### Bổ sung: UniLog với backbone CodeLlama-7B (cũng do AL-Bench chạy)

Nguồn: `res_all.zip` của AL-Bench. Chấm được **34,444/39,600** mẫu; vị trí khớp chính xác **24.6%** (AL-Bench Table 2 báo cáo UniLog_cl PA 23,49%).

| Trạng thái | Số mẫu |
|---|---:|
| chấm được | 34,444 |
| log nằm trong lambda / lớp ẩn danh (verifier chưa hỗ trợ) | 4,553 |
| không có output hợp lệ (không trả `<lineK>`, hoặc dòng ngoài phạm vi) | 515 |
| input không parse được | 88 |

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | 646 | trong đó **170** ca vị trí trùng y hệt gold |
| **T2** Metric cộng điểm level / message cho log IN SAI LÚC | 5,778 |  |
| **T3** Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | 5,821 |  |
| **T4** Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | 20,147 |  |
| **T5** Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | 142 |  |

## 4. Ví dụ theo từng loại

### T1. Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC → cần **ER**

Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau).

Số ca: **384**. Xem tất cả: [cases/T1.md](cases/T1.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T1.csv` (đầy đủ).

#### Ví dụ T1-a: vị trí trùng gold, in biến chưa khai báo (mẫu `19335`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @Override
    public void setup() throws Exception {
        super.setup();
G>  LOG.debug("Scale test operation count = {}", getOperationCount());
P>  log.info("Setting up test environment with raw configuration: {}", rawConfiguration);
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
        Configuration rawConfiguration = getRawConfiguration();
        assumeScaleTestsEnabled(rawConfiguration);
    }
```

- **Metric của công cụ chấm:** vị trí **đúng** (khớp chính xác dòng (AL-Bench)) · level **sai** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `rawConfiguration`, khai báo ở dòng sau.

#### Ví dụ T1-b (mẫu `11558`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public Resource getMaximumAllocation() {
P>  log.info("Retrieved maximum allocation: {}", ret);
        Resource ret = ResourceUtils.getResourceTypesMaximumAllocation();
G>  LOG.info("Maximum allocation = " + ret);
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
        return ret;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `invalid` (không chạy được) · CA 1 · ER 0 · RPA 0
- **Vì sao metric chấm sai:** log in `ret` trước câu khai báo `Resource ret = …`; level vẫn tính đúng.

### T2. Metric cộng điểm level / message cho log IN SAI LÚC → cần **CA**

Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** với log của developer: in quá thường, quá ít, nhầm nhánh.

Số ca: **3,778**. Xem tất cả: [cases/T2.md](cases/T2.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T2.csv` (đầy đủ).

#### Ví dụ T2-a: message và level trùng gold, nhưng log ra ngoài vòng `while` (mẫu `25140`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void ensureActiveGroup() {
P>  log.warn("stillwaitingtoensureactivegroup");
        while (!ensureActiveGroup(time.timer(Long.MAX_VALUE))) {
G>  log.warn("still waiting to ensure active group");
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
        }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:weaker` (in quá thường (mất điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** gold "still waiting…" in **mỗi vòng chờ**; log sinh ra chỉ in **một lần** trước vòng lặp (`weaker`).

#### Ví dụ T2-b (mẫu `23472`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    private static void deleteOrWarn(File file) {
P>  log.warn("Unable to delete {}", file);
        if (!file.delete()) {
G>  LOG.warn("Could not delete {}", file);
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
        }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:weaker` (in quá thường (mất điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log "Unable to delete" in **trước** khi thử xoá, tức là in cả khi xoá thành công; gold chỉ in khi `!file.delete()` (`weaker`).

### T3. Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) → cần **RPA**

Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương.

Số ca: **8,205**. Xem tất cả: [cases/T3.md](cases/T3.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T3.csv` (đầy đủ).

#### Ví dụ T3-a: lệch đúng một dòng trống (7.807 ca như vậy) (mẫu `39070`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void setConnectToLearnerMasterLimit(int connectToLearnerMasterLimit) {
G>  LOG.info("connectToLearnerMasterLimit set to {}", connectToLearnerMasterLimit);
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
P>  logger.info("connectToLearnerMasterLimit set to: {}", connectToLearnerMasterLimit);
        this.connectToLearnerMasterLimit = connectToLearnerMasterLimit;
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** hai vị trí chỉ cách nhau dòng trống do AL-Bench để lại; trong Java đây là **cùng một chỗ**.

#### Ví dụ T3-b (mẫu `1165`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void recoverProjectDescription() throws IOException {
        Path mdFile = getAbsolutePath().resolve(IProjectDescription.DESCRIPTION_FILE_NAME);
G>  log.debug("Recovering project '" + project.getName() + "' metadata " + mdFile.toAbsolutePath());
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
P>  log.info("Recovering project description for project: {}", project.getName());
        IOUtils.writeFileFromString(mdFile.toFile(), EMPTY_PROJECT_TEMPLATE.replace("${project-name}", project.getName()));
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **sai** · message **sai** (khớp chính xác)
- **Verifier của mình:** `equivalent_move` (lệch nhưng tương đương) · CA 1 · ER 1 · RPA 1
- **Vì sao metric chấm sai:** tương tự: chỉ cách nhau dòng trống.

### T4. Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) → cần **CA (chẩn đoán)**

Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold.

Số ca: **13,167**. Xem tất cả: [cases/T4.md](cases/T4.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T4.csv` (đầy đủ).

#### Ví dụ T4-a (mẫu `4726`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    public void dropResource(Resource resource) {
        String name = resource.getName();
P>  logger.info("Dropping resource with name: {}", name);
        if (nameToResource.remove(name) == null) {
G>  LOG.info("resource " + name + " does not exists.");
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
        }
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **đúng** · message **sai** (khớp chính xác)
- **Verifier của mình:** `wrong_condition:weaker` (in quá thường (mất điều kiện)) · CA 0 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log "Dropping resource" in mọi lần, gold chỉ in khi resource không tồn tại (`weaker`).

### T5. Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) → cần **RPA**

Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính.

Số ca: **131**. Xem tất cả: [cases/T5.md](cases/T5.md) (bản dễ xem, 30 ca có code đầy đủ và bảng liệt kê) · `cases/T5.csv` (đầy đủ).

#### Ví dụ T5-a (mẫu `2348`)

Input là method đã xoá log; dưới đây là method đó sau khi chèn cả hai log để so sánh. `G>` = log của developer (ground truth), `P>` = log công cụ sinh ra.

```java
    @Override
    public void close() {
        log.info("WorkerRpcServer closing");
P>  log.info("WorkerRpcServer closed");
        nettyRemotingServer.close();
G>  log.info("WorkerRpcServer closed");
    // «dòng trống benchmark để lại ở chỗ log bị xoá»
    }
```

- **Metric của công cụ chấm:** vị trí **sai** (khớp chính xác dòng (AL-Bench)) · level **đúng** · message **đúng** (khớp chính xác)
- **Verifier của mình:** `order_changed` (vượt qua một thao tác) · CA 1 · ER 1 · RPA 0
- **Vì sao metric chấm sai:** log "WorkerRpcServer closed" in **trước** khi `nettyRemotingServer.close()` chạy.

*Nhiều ca T5 là công cụ log một sự kiện khác nhưng hợp lý; cần đọc message mới phán được. Chỉ dùng để minh hoạ.*

## 5. Giới hạn

- Tham chiếu đúng/sai là verifier của mình, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện (T2, T4). Cần đánh giá bởi người (E6).
- ER chưa kiểm bằng javac; các ví dụ T1 ở trên đã đọc tay, đều là dùng biến trước khai báo, chắc chắn không biên dịch được.
- Mẫu có log nằm trong lambda / lớp ẩn danh bị loại, vì verifier chưa hỗ trợ.
- Level và message so khớp chính xác (đúng định nghĩa của paper); BLEU/ROUGE chưa tính lại.

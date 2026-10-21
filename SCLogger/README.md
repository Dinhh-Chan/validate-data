# SCLogger (TÁI HIỆN XẤP XỈ): các trường hợp metric của SCLogger chấm sai

> ⚠️ **Đây là bản tái hiện XẤP XỈ**, không phải output gốc của SCLogger. Tác giả không công bố prompt, pipeline gọi LLM, dữ liệu hay output. Mọi con số và ví dụ trong thư mục này phải được gọi là "SCLogger (xấp xỉ)".

*Danh sách mọi ca: `cases/T1.md`, `T3.md`, `T4.md`, `T5.md` (bản dễ xem, có prompt, input, output) và `cases/*.csv`. Code: `analysis/sclogger_repro/sclogger_run.py`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** Li et al. *Go Static: Contextualized Logging Statement Generation*. FSE 2024. arXiv 2402.12958. Repo: `github.com/YichenLi00/SCLogger` (README: "Under Construction", lần push cuối 04/08/2024).

**Cách sinh log:** phân tích tĩnh toàn project để lấy (1) code slice: method gọi tới và được gọi trong vòng 2 bước, (2) log slice: log có thể chạy trước và sau, (3) danh sách biến dùng được; (4) chọn 5 ví dụ mẫu cùng project bằng BM25; (5) ghép thành prompt chain-of-thought gửi LLM, nhận `<Line Number>` và `<Statement>`; (6) lượt 2 "tinh chỉnh biến" với thông tin kiểu chi tiết.

**Metric của chính paper (M):**
- **Vị trí:** *"PA as 1 … if the distance between the predicted line number and the actual line number is less than or equal to one line and both … must be within the same block"* (§4.3.1). Giống hệt PDLogger.
- **Nội dung:** *"we only calculate the metrics for what-to-log when the logging position … is predicted correctly"* (§4.3.2).
- **Chạy được / điều kiện:** không kiểm.

## 2. Tái hiện thế nào, và trung thực tới đâu

| Thành phần | Bản này dùng | Mức trung thực |
|---|---|---|
| Danh sách biến (§3.2.3) | **chính `Src/Var/AvaVarList.java` của tác giả**, biên dịch và chạy nguyên trạng (Eclipse JDT, source và jar Hadoop 3.4.0) | code của tác giả |
| 5 ví dụ mẫu (§3.3) | logic `bm25_selection` của tác giả (`Scripts/demo_case_selection.py`): tách từ camelCase, lấy top-5; BM25 của gensim 3.8.3 chép lại công thức (gensim 3.8.3 không cài được trên Python 3.12) | logic của tác giả |
| Call graph (§3.2.1) | java-callgraph (BCEL) trên jar Hadoop 3.4.0, đúng định dạng đầu vào mà `CodeSlicer.java` của tác giả đọc; paper dùng phân tích con trỏ nhạy ngữ cảnh | xấp xỉ |
| Code slice | method gọi tới và được gọi trong vòng 2 bước, chọn ngẫu nhiên 1 đường (quy tắc của paper); lấy source method như `MethodFinder.java` | quy tắc của paper, code của mình |
| Log slice (§3.2.2) | các câu log trong các method trên đường 2 bước đó (trước = method gọi tới, sau = method được gọi); công cụ log graph của paper không được công bố | xấp xỉ |
| Prompt (§3.4) | **chép từ hình Fig. 6** (không có bản text) | xấp xỉ |
| Tinh chỉnh biến (§3.5) | lượt 2 "Please rethink the variable usage with detailed type information about <Var>" kèm chữ ký thành viên của kiểu biến (paper in cả source class) | xấp xỉ |
| Backbone | **gpt-4o-mini**, temperature 0 (paper: gpt-3.5-turbo-0301, đã ngừng cung cấp) | khác |
| Chia dữ liệu | chia method 8:2 ngẫu nhiên (§4.1); ví dụ mẫu và các slice không dùng method test | như paper |

**Dữ liệu:** AL-Bench (`cleaned_static_test_data.json`), phần **main code của 11 module lõi Hadoop** (common, hdfs, hdfs-client, mapreduce-client-core/app, yarn-api/common/client/server-common/resourcemanager/nodemanager). Paper và code của tác giả cũng làm trên Hadoop (paper: 3.3.0; code `VarRefine.java` của tác giả trỏ tới jar Hadoop 3.3.6). Source **Hadoop 3.4.0** tải từ `archive.apache.org`; jar 3.4.0 từ Maven Central. Pool: 6.746 mẫu (3.830 method); train 5.457 mẫu; **lấy ngẫu nhiên 500 mẫu test**.

**Lộ vị trí:** input AL-Bench có dòng trống ở chỗ log bị xoá; ở đây **đã xoá dòng trống này**.

**Một điểm phải xử lý:** gpt-4o-mini thường **không theo định dạng** `<Line Number>: N <Statement>: …` mà trả về cả method đã chèn log. Mình **không sửa prompt**; output được đọc theo hai cách và ghi lại cách đọc cho từng mẫu: (1) đúng định dạng; (2) so code trả về với input để tìm log được chèn (lấy log đầu tiên nếu model chèn nhiều log).

**Trạng thái 500 mẫu:** chấm được 431 · không đọc được output 51 · không chấm được 17 · thư viện parse bị crash 1.

**Quy ước dòng:** các ví dụ mẫu trong prompt dùng nhãn "log nằm ở dòng N", tức chèn trước dòng N của input; đây là cách đọc chính. Cách đọc "chèn sau dòng N" cũng được tính để đối chiếu.

| Cách đọc N | PA đúng dòng | **PA@1 (metric SCLogger)** | RPA | CA | ER |
|---|---:|---:|---:|---:|---:|
| log ở dòng N (chính) | 21.1 | **26.7** | 25.1 | 35.5 | 96.5 |
| chèn sau dòng N | 7.5 | 19.6 | 15.8 | 32.5 | 89.4 |

**Đối chiếu thô với số đã công bố:** paper PDLogger chạy SCLogger trên Hadoop 3.4.1 và ActiveMQ được PA@1 = 0,417; bản xấp xỉ này được 0.267 trên Hadoop 3.4.0 (khác dữ liệu, khác backbone, khác prompt; chỉ để tham khảo).

**Lỗi sai dưới cả hai cách đọc N:** 288/323 lỗi.

## 3. Tổng hợp các trường hợp sai

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** PA@1 chấm đúng nhưng log **không chạy được** | **4** | theo M của SCLogger, các ca này còn được **cộng điểm nội dung** vì nội dung chỉ chấm khi PA@1 = 1 |
| **T2** nội dung được tính đúng dù in sai lúc | — | nội dung chỉ chấm khi PA@1 = 1, nên không có loại này |
| **T3** PA@1 chấm 0 cho log đặt đúng | **11** | |
| **T4** cùng điểm 0 cho mọi kiểu sai | 305 | xem bảng chẩn đoán |
| **T5** PA@1 chấm đúng nhưng sai thứ tự | 14 | minh hoạ |

**Chẩn đoán các ca PA@1 = 0 và RPA = 0:**

| Verdict | Ý nghĩa | Số ca |
|---|---|---:|
| `wrong_condition:weaker` | in quá thường (mất điều kiện) | 202 |
| `wrong_condition:disjoint` | nhầm nhánh (không bao giờ cùng in) | 32 |
| `wrong_condition:overlapping` | điều kiện khác | 18 |
| `wrong_condition:stronger` | in quá ít / sai phạm vi (thừa điều kiện) | 15 |
| `order_changed` | vượt qua một thao tác | 12 |
| `invalid` | không chạy được | 11 |
| `log_order_changed` | đổi thứ tự với log khác | 9 |
| `value_changed` | giá trị biến được in đã đổi | 6 |

## 4. Ví dụ

### T1. PA@1 chấm đúng nhưng log không chạy được → cần ER

*Lưu ý khi đọc T1: 0/4 ca vẫn không chạy được nếu đọc N theo cách "chèn sau dòng N". Đọc câu trả lời thô thấy model thường **đếm sai dòng** (ví dụ viết "thêm sau câu gán X, ở dòng 11" nhưng dòng 11 lại là chính câu gán X). Prompt của SCLogger (theo Fig. 6) đưa code **không đánh số dòng** nhưng bắt model trả số dòng; AL-Bench cũng nhận xét "LLM không giỏi đếm số dòng". Lỗi này thuộc thiết kế của SCLogger, nhưng độ lớn của nó có thể khác ở SCLogger gốc.*

#### Ví dụ T1-a (mẫu AL-Bench `14841`)

```java
    synchronized void startMBeans() {
        if (mbeanName != null) {
            LOG.warn("MBean " + name + " already initialized!");
G>  LOG.debug("Stacktrace: ", new Throwable());
            return;
P>  LOG.info("Registered MBean for source " + name);
        }
        mbeanName = MBeans.register(prefix, name, this);
        LOG.debug("MBean for source " + name + " registered.");
    }
```

- Metric của SCLogger: PA@1 1 · Verifier: `invalid` · CA 1 · ER 0 · RPA 0
- Log lệch ≤ 1 dòng, cùng block nên PA@1 = 1, và theo SCLogger còn được chấm nội dung; nhưng log không chạy được (đọc code để thấy lý do: nằm sau return/throw hoặc in biến khai báo phía sau).

#### Ví dụ T1-b (mẫu AL-Bench `13171`)

```java
    @VisibleForTesting
    protected void addCGroupParentIfRequired(String resourcesOptions, String containerIdStr, DockerRunCommand runCommand) {
        if (cGroupsHandler == null) {
            LOG.debug("cGroupsHandler is null. cgroups are not in use. nothing to" + " do.");
            return;
        }
        if (resourcesOptions.equals(PrivilegedOperation.CGROUP_ARG_PREFIX + PrivilegedOperation.CGROUP_ARG_NO_TASKS)) {
            LOG.debug("no resource restrictions specified. not using docker's " + "cgroup options");
        } else {
            LOG.debug("using docker's cgroups options");
P>  LOG.debug("using cgroup parent: " + cGroupPath);
            String cGroupPath = "/" + cGroupsHandler.getRelativePathForCGroup(containerIdStr);
G>  LOG.debug("using cgroup parent: {}", cGroupPath);
            runCommand.setCGroupParent(cGroupPath);
        }
    }
```

- Metric của SCLogger: PA@1 1 · Verifier: `invalid` · CA 1 · ER 0 · RPA 0
- Tương tự.


### T3. PA@1 chấm 0 cho log đặt đúng → cần RPA / CA

#### Ví dụ T3-a (mẫu AL-Bench `10879`)

```java
    @Override
    protected void removeReservationState(String planName, String reservationIdName) throws Exception {
P>  LOG.debug("Removing reservation {} for plan {}", reservationIdName, planName);
        Path planCreatePath = getNodePath(reservationRoot, planName);
        Path reservationPath = getNodePath(planCreatePath, reservationIdName);
G>  LOG.info("Removing state for reservation " + reservationIdName + " from " + "plan " + planName + " at path " + reservationPath);
        deleteFileWithRetries(reservationPath);
    }
```

- Metric của SCLogger: PA@1 0 · Verifier: `equivalent_move` · CA 1 · ER 1 · RPA 1
- Vị trí lệch nhưng cùng điều kiện, chạy được, không vượt qua câu lệnh làm đổi điều log mô tả.


### T4. Cùng điểm 0 cho mọi kiểu sai → cần CA (chẩn đoán)

#### Ví dụ T4-a: in quá thường (loại lỗi phổ biến nhất) (mẫu AL-Bench `12023`)

```java
    public RegisterApplicationMasterResponse registerApplicationMaster(String uamId, RegisterApplicationMasterRequest registerRequest) throws YarnException, IOExcep
P>  LOG.info("Attempting to register UAM id {}", uamId);
        if (!this.unmanagedAppMasterMap.containsKey(uamId)) {
            throw new YarnException("UAM " + uamId + " does not exist");
        }
G>  LOG.info("Registering UAM id {} for application {}", uamId, this.appIdMap.get(uamId));
        return this.unmanagedAppMasterMap.get(uamId).registerApplicationMaster(registerRequest);
    }
```

- Metric của SCLogger: PA@1 0 · Verifier: `wrong_condition:weaker` · CA 0 · ER 1 · RPA 0
- Log bị đặt ra ngoài điều kiện của developer.

#### Ví dụ T4-b: nhầm nhánh (mẫu AL-Bench `23592`)

```java
    synchronized void removeLease(String holder, INodeFile src) {
        Lease lease = getLease(holder);
        if (lease != null) {
P>  LOG.info("Removing lease for holder: " + holder + ", src ID: " + src.getId() + ", isUnderConstruction: " + src.isUnderConstruction() + ", replication factor: " + src.getPreferredBlockReplication() + ", preferred block size: " + src.getPreferredBlockSize());
            removeLease(lease, src.getId());
        } else {
G>  LOG.warn("Removing non-existent lease! holder={} src={}", holder, src.getFullPathName());
        }
    }
```

- Metric của SCLogger: PA@1 0 · Verifier: `wrong_condition:disjoint` · CA 0 · ER 1 · RPA 0
- Hai log không bao giờ cùng in.


### T5. PA@1 chấm đúng nhưng sai thứ tự (minh hoạ)

#### Ví dụ T5-a (mẫu AL-Bench `13119`)

```java
    public int getClassIdFromFileContents(String input) {
P>  LOG.debug("Processing input string for class ID: {}", input);
        String classIdStr = String.format("%08x", Integer.parseInt(input));
G>  LOG.debug("ClassId hex string : {}", classIdStr);
        return Integer.parseInt(classIdStr.substring(4));
    }
```

- Metric của SCLogger: PA@1 1 · Verifier: `order_changed` · CA 1 · ER 1 · RPA 0
- Log vượt qua một thao tác; tranh cãi được.


Prompt, input và output đầy đủ của từng ca: xem `cases/T*.md`.

## 5. Giới hạn

- **Bản xấp xỉ**: prompt chép từ hình, backbone khác (gpt-4o-mini), log slice và call graph xấp xỉ, gpt-4o-mini thường không theo định dạng nên phải đọc vị trí từ code trả về. Lỗi ở đây chưa chắc là lỗi của SCLogger gốc.
- `AvaVarList.java` của tác giả khớp method theo **tên**: nếu một file có nhiều class con cùng có method trùng tên, biến của các method đó bị gộp vào danh sách. Giữ nguyên hành vi này.
- Chỉ chạy 500 mẫu, chỉ trên Hadoop.
- Tham chiếu "sai" là verifier của mình, so với một log gold.
- Muốn chính xác cần xin tác giả prompt, pipeline hoặc output.

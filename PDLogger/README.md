# PDLogger: các trường hợp metric của PDLogger chấm sai output của chính PDLogger

*Danh sách mọi ca: `cases/T1.md`, `T3.md`, `T4.md`, `T5.md` (bản dễ xem) và `cases/*.csv`. Định nghĩa T1–T5: `../README.md`. Chi tiết thêm: `analysis/logging_condition_study/BAO_CAO_PAK_METRIC.md` mục 4 (đặc biệt 4.8) và `analysis/pdlogger_repro/KIEM_CHUNG_PDLOGGER.md`.*

## 1. Phương pháp và cách nó tự đánh giá

**Paper:** PDLogger, arXiv 2507.19951 (2025). Repo: `github.com/qlbdsc/PDLogger` (chỉ có prompt và script phụ; **không** có dữ liệu, output, script đánh giá).

**Cách sinh log:** LLM (paper dùng o3-mini). Mỗi block (if, try, loop, method) được hỏi riêng bằng một prompt "vị trí" để chọn dòng N; sau đó một prompt "message" sinh câu log; log được chèn **sau** dòng N; có bước khử trùng lặp và tinh chỉnh level.

**Metric của chính paper (M):**
- **Vị trí (PA@1):** *"A prediction is counted as correct (PA = 1) if the predicted line number deviates from the true line number by at most one and both lines are located within the same code block"* (§4.1).
- **Nội dung:** L-ACC, AOD, biến P/R, BLEU, ROUGE, BERTScore. Paper không ghi rõ có chỉ chấm trên log khớp vị trí không.
- **Chạy được / điều kiện:** không kiểm.

## 2. Dữ liệu lấy ở đâu

**PDLogger không công bố output, nên mình tự tái hiện** (`analysis/pdlogger_repro/`):
- **Prompt nguyên văn** từ `block-type-based-prompting/position_generation.sh` và `message_generation.sh` (kiểm bằng hash). Bộ gán nhãn block chuyển từ `block_abstract.java` sang Python.
- Backbone **gpt-4o-mini** (paper dùng o3-mini); **không có** ngữ cảnh Joern, bước khử trùng lặp, tinh chỉnh level; chọn 1 vị trí có quality score cao nhất (do mình thêm).
- Chèn log **sau** dòng N, đúng quy ước của paper (§3.4).
- **Dữ liệu:** 1.000 method đầu của **LogBench-O** (`analysis/logbench_runs/v2_corrected/samples.jsonl`); ground truth là log thật của developer bị che bằng `<LOG_HERE>`.
- Output: `analysis/pdlogger_repro/runs/rerun_O/outputs.jsonl`; kết quả chấm: `scored.jsonl`.

PDLogger trả vị trí cho **846/1.000** mẫu.

**Kiểm chứng lỗi thuộc về PDLogger** (`attribution_check.py`): mỗi lỗi được kiểm 5 điều kiện: C1 prompt nguyên văn; C2 vẫn sai nếu đọc N là "trước dòng N"; C3 mọi ứng viên PDLogger đề xuất đều sai; C4 parse đúng; C5 không phải log trùng mà bước dedup của paper sẽ xoá. Kết quả: **266/638 lỗi (42%)** qua cả 5 điều kiện. Cột `loi_cua_PDLogger_qua_C1_C5` trong CSV ghi kết quả này cho từng ca.

## 3. Tổng hợp các trường hợp sai

| Loại | Số ca | Ghi chú |
|---|---:|---|
| **T1** PA@1 chấm đúng nhưng log **không chạy được** | **30** | log nằm sau `return`/`throw`. Đọc theo cả hai quy ước dòng, PA@1 đều = 1 (một cách đọc thì log không chạy được, cách kia thì log đúng y gold), nên PA@1 không biết log có chạy được không |
| **T2** nội dung được tính đúng dù in sai lúc | — | Với PDLogger, lỗi điều kiện đều bị PA@1 chấm 0; không có trường hợp metric cộng điểm |
| **T3** PA và PA@1 chấm 0 cho log đặt đúng | **5** | log ra ngoài guard `isDebugEnabled()` nhưng vẫn in đúng lúc; 1 ca trong đó là verifier chấm nhầm (`RecoverableThreadScheduler`), còn 4 |
| **T4** cùng điểm 0 cho mọi kiểu sai | 561 | xem bảng chẩn đoán |
| **T5** PA@1 chấm đúng nhưng sai thứ tự | 56 | 14 ca qua C1–C5; đọc tay khoảng 4 sai rõ |

**Chẩn đoán các ca PA@1 = 0 và RPA = 0:**

| Verdict | Số ca |
|---|---:|
| `wrong_condition:stronger`: in quá ít / sai phạm vi (thừa điều kiện) | 174 |
| `wrong_condition:overlapping`: điều kiện khác | 82 |
| `wrong_condition:weaker`: in quá thường (mất điều kiện) | 74 |
| `order_changed`: vượt qua một thao tác | 65 |
| `wrong_condition:disjoint`: nhầm nhánh (không bao giờ cùng in) | 61 |
| `invalid`: không chạy được | 40 |
| `value_changed`: giá trị biến được in đã đổi | 32 |
| `log_order_changed`: đổi thứ tự với log khác | 22 |
| `invalid_insertion`: invalid_insertion | 11 |

## 4. Ví dụ theo từng loại

### T1. PA@1 chấm đúng nhưng log không chạy được → cần ER

#### Ví dụ T1-a: message trùng gold từng chữ, nằm sau `throw`

*Input, prompt và output đầy đủ: Phụ lục B, mục B.9.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:activemq_QueueStorePrefetch_getStoreMessageSize.java`, log của developer: `LOG.error("Failed to get message size", e);` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (2 block: Try-Catch Block1, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Try-Catch Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 6 |
| **Output thô** | block Try-Catch Block1 trả lời `Line number of position choice: 6` (quality 8); prompt message trả `Completed Log: logger.error("Failed to get message size", e);` |
| **Output cuối** | chèn câu log **sau dòng 6** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: @Override//This is start of Method Declaration Block1
2: protected synchronized long getStoreMessageSize() {
3:     try {//This is start of Try-Catch Block1
4:         return this.store.getMessageSize();
5:     } catch (IOException e) {
6:         throw new RuntimeException(e);
7:     }//This is end of Try-Catch Block1
8: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Try-Catch Block1 | [6] | 8.0 | Chain-of-Thought: Logging the exception before rethrowing it provides context for the error that occurred. |
| Method Declaration Block1 | [3] | 0.0 | Chain-of-Thought: The log should be placed at the beginning of the Try-Catch Block to capture the start of the operation that retrieves the message size. |


```java
    @Override
    protected synchronized long getStoreMessageSize() {
        try {
            return this.store.getMessageSize();
        } catch (IOException e) {
G>  LOG.error("Failed to get message size", e);
            throw new RuntimeException(e);
P>  logger.error("Failed to get message size", e);
        }
    }
```

Chấm (verifier, chạy thật): verdict `invalid` · CA 1 · ER 0 · RPA 0 · PA 0 · PDLogger PA@1 1

- **Vì sao metric chấm sai:** PDLogger trả lời dòng của `throw`; paper chèn **sau** dòng đó nên log không bao giờ chạy. Lệch 1 dòng, cùng block, nên PA@1 = 1.

#### Ví dụ T1-b: log sau `return false;`

*Input, prompt và output đầy đủ: Phụ lục B, mục B.12.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:sonarlint-core_PluginsSynchronizer_shouldDownload.java`, log của developer: `LOG.debug("[SYNC] Code analyzer '{}' is embedded in SonarLint. Skip downloading it.", serverPlugin.getKey());` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (6 block: Branching Block1, Branching Block2, Branching Block3, Branching Block4, Branching Block5, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Branching Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 3 |
| **Output thô** | block Branching Block1 trả lời `Line number of position choice: 3` (quality 8); prompt message trả `Completed Log: LOG.debug("[SYNC] Code analyzer '{}' is embedded and will not be downloaded.", serverPlugin.getKey());` |
| **Output cuối** | chèn câu log **sau dòng 3** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: private boolean shouldDownload(ServerPlugin serverPlugin, Map<String, StoredPlugin> storedPluginsByKey) {//This is start of Method Declaration Block1
2:     if (embeddedPluginKeys.contains(serverPlugin.getKey())) {//This is start of Branching Block1
3:         return false;
4:     }//This is end of Branching Block1
5:     if (upToDate(serverPlugin, storedPluginsByKey)) {//This is start of Branching Block2
6:         LOG.debug("[SYNC] Code analyzer '{}' is up-to-date. Skip downloading it.", serverPlugin.getKey());
7:         return false;
8:     }//This is end of Branching Block2
9:     if (!serverPlugin.isSonarLintSupported()) {//This is start of Branching Block3
10:         LOG.debug("[SYNC] Code analyzer '{}' does not support SonarLint. Skip downloading it.", serverPlugin.getKey());
11:         return false;
12:     }//This is end of Branching Block3
13:     if (sonarSourceDisabledPluginKeys.contains(serverPlugin.getKey())) {//This is start of Branching Block4
14:         LOG.debug("[SYNC] Code analyzer '{}' is disabled in SonarLint (language not enabled). Skip downloading it.", serverPlugin.getKey());
15:         return false;
16:     }//This is end of Branching Block4
17:     var pluginVersion = VersionUtils.getJarVersion(serverPlugin.getFilename());
18:     if (!pluginsMinVersions.isVersionSupported(serverPlugin.getKey(), pluginVersion)) {//This is start of Branching Block5
19:         var minimumVersion = pluginsMinVersions.getMinimumVersion(serverPlugin.getKey());
20:         LOG.debug("[SYNC] Code analyzer '{}' version '{}' is not supported (minimal version is '{}'). Skip downloading it.", serverPlugin.getKey(), pluginVersion, minimumVersion);
21:         return false;
22:     }//This is end of Branching Block5
23:     return true;
24: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Branching Block1 | [3] | 8.0 | Chain-of-Thought: The log should be placed after the condition that checks if the embedded plugin keys contain the server plugin key, as this directly influences the program's behavior by determining whether to download the plugin |
| Branching Block2 | [6] | 8.0 | Chain-of-Thought: The log at line 6 captures a significant event where the server plugin is determined to be up-to-date, which directly influences the program's behavior by skipping the download. This log is necessary to monitor t |
| Branching Block3 | [10] | 8.0 | Chain-of-Thought: The log captures a critical decision point where the server plugin does not support SonarLint, which directly influences the program's behavior by skipping the download. |
| Branching Block4 | [15] | 8.0 | Chain-of-Thought: The log captures the event of a disabled plugin, which directly influences the program's behavior by preventing the download. This is a critical decision point in the method. |
| Branching Block5 | [20] | 8.0 | Chain-of-Thought: The log at line 20 captures a critical event where the plugin version is not supported, which directly influences the program's behavior by preventing the download. This log is necessary to monitor issues related |
| Method Declaration Block1 | [17] | 8.0 | Chain-of-Thought: The line responsible for the main functionality of the method is line 17, where the plugin version is retrieved. Since this line is not within an inner block, the log can be placed directly before it to capture t |


```java
    private boolean shouldDownload(ServerPlugin serverPlugin, Map<String, StoredPlugin> storedPluginsByKey) {
        if (embeddedPluginKeys.contains(serverPlugin.getKey())) {
G>  LOG.debug("[SYNC] Code analyzer '{}' is embedded in SonarLint. Skip downloading it.", serverPlugin.getKey());
            return false;
P>  LOG.debug("[SYNC] Code analyzer '{}' is embedded and will not be downloaded.", serverPlugin.getKey());
        }
        if (upToDate(serverPlugin, storedPluginsByKey)) {
            LOG.debug("[SYNC] Code analyzer '{}' is up-to-date. Skip downloading it.", serverPlugin.getKey());
            return false;
        }
        if (!serverPlugin.isSonarLintSupported()) {
            LOG.debug("[SYNC] Code analyzer '{}' does not support SonarLint. Skip downloading it.", serverPlugin.getKey());
            return false;
        }
        if (sonarSourceDisabledPluginKeys.contains(serverPlugin.getKey())) {
            LOG.debug("[SYNC] Code analyzer '{}' is disabled in SonarLint (language not enabled). Skip downloading it.", serverPlugin.getKey());
            return false;
        }
        var pluginVersion = VersionUtils.getJarVersion(serverPlugin.getFilename());
        if (!pluginsMinVersions.isVersionSupported(serverPlugin.getKey(), pluginVersion)) {
            var minimumVersion = pluginsMinVersions.getMinimumVersion(serverPlugin.getKey());
            LOG.debug("[SYNC] Code analyzer '{}' version '{}' is not supported (minimal version is '{}'). Skip downloading it.", serverPlugin.getKey(), pluginVersion, minimumVersion);
            return false;
        }
        return true;
    }
```

Chấm (verifier, chạy thật): verdict `invalid` · CA 1 · ER 0 · RPA 0 · PA 0 · PDLogger PA@1 1

- **Vì sao metric chấm sai:** tương tự: log nằm sau `return`, PA@1 = 1.

### T3. PA và PA@1 chấm 0 cho log đặt đúng → cần CA / RPA

#### Ví dụ T3-a: log ra ngoài guard `isDebugEnabled()`

*Input, prompt và output đầy đủ: Phụ lục B, mục B.15.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:activemq_TempTopic_addSubscription.java`, log của developer: `LOG.debug(" changed ownership of " + this + " to " + tempDest.getConnectionId());` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (3 block: Branching Block1, Branching Block2, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Branching Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 7 |
| **Output thô** | block Branching Block1 trả lời `Line number of position choice: 7` (quality 8); prompt message trả `Completed Log: LOG.debug("Setting connection ID for temporary destination to: {}", sub.getConsumerInfo().getConsumerId().getConnectionId());` |
| **Output cuối** | chèn câu log **sau dòng 7** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: public void addSubscription(ConnectionContext context, Subscription sub) throws Exception {//This is start of Method Declaration Block1
2:     // Only consumers on the same connection can consume from
3:     // the temporary destination
4:     // However, we could have failed over - and we do this
5:     // check client side anyways ....
6:     if (!context.isFaultTolerant() && (!context.isNetworkConnection() && !tempDest.getConnectionId().equals(sub.getConsumerInfo().getConsumerId().getConnectionId()))) {//This is start of Branching Block1
7:         tempDest.setConnectionId(sub.getConsumerInfo().getConsumerId().getConnectionId());
8:         if (LOG.isDebugEnabled()) {//This is start of Branching Block2
9:         }//This is end of Branching Block2
10:     }//This is end of Branching Block1
11:     super.addSubscription(context, sub);
12: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Branching Block1 | [7] | 8.0 | Chain-of-Thought: The condition in Branching Block1 indicates a significant change in the connection ID, which is a critical event that influences the program's behavior. Logging this event will help in monitoring and debugging. |
| Branching Block2 | [8] | 8.0 | Chain-of-Thought: The log is needed to capture the state when the debug logging is enabled, which can provide insights into the flow of execution within this block. |
| Method Declaration Block1 | [6] | 8.0 | Chain-of-Thought: The log should be placed at the beginning of Branching Block1, as it contains the critical condition that determines the flow of the method. |


```java
    public void addSubscription(ConnectionContext context, Subscription sub) throws Exception {
        // Only consumers on the same connection can consume from
        // the temporary destination
        // However, we could have failed over - and we do this
        // check client side anyways ....
        if (!context.isFaultTolerant() && (!context.isNetworkConnection() && !tempDest.getConnectionId().equals(sub.getConsumerInfo().getConsumerId().getConnectionId()))) {
            tempDest.setConnectionId(sub.getConsumerInfo().getConsumerId().getConnectionId());
P>  LOG.debug("Setting connection ID for temporary destination to: {}", sub.getConsumerInfo().getConsumerId().getConnectionId());
            if (LOG.isDebugEnabled()) {
G>  LOG.debug(" changed ownership of " + this + " to " + tempDest.getConnectionId());
            }
        }
        super.addSubscription(context, sub);
    }
```

Chấm (verifier, chạy thật): verdict `equivalent_move` · CA 1 · ER 1 · RPA 1 · PA 0 · PDLogger PA@1 0

- **Vì sao metric chấm sai:** log ở level debug vốn chỉ in khi debug bật, nên guard chỉ để tiết kiệm hiệu năng; điều kiện in ra giống hệt gold. Khác block nên PA@1 = 0.

#### Ví dụ T3-b

*Input, prompt và output đầy đủ: Phụ lục B, mục B.3.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:geronimo_SAAJUniverse_unset.java`, log của developer: `LOG.debug("Restored universe: " + Thread.currentThread());` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (3 block: Branching Block1, Branching Block2, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Branching Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 4 |
| **Output thô** | block Branching Block1 trả lời `Line number of position choice: 4` (quality 8); prompt message trả `Completed Log: LOG.debug("Removing the last element from the universeList: {}", universeList);` |
| **Output cuối** | chèn câu log **sau dòng 4** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: public void unset() {//This is start of Method Declaration Block1
2:     LinkedList<Type> universeList = currentUniverse.get();
3:     if (universeList != null && !universeList.isEmpty()) {//This is start of Branching Block1
4:         universeList.removeLast();
5:         if (LOG.isDebugEnabled()) {//This is start of Branching Block2
6:         }//This is end of Branching Block2
7:     }//This is end of Branching Block1
8: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Branching Block1 | [4] | 8.0 | Chain-of-Thought: The log should be placed after the removal of the last element from the universeList to capture the event of modifying the list, which is a significant change in state. |
| Branching Block2 | [5] | 8.0 | Chain-of-Thought: The log is needed to capture the state of the application when entering the conditional check, which can influence the program's behavior. |
| Method Declaration Block1 | [3] | 8.0 | Chain-of-Thought: The log should be placed at the beginning of Branching Block1, as it checks the condition for the universeList, which is crucial for the method's functionality. |


```java
    public void unset() {
        LinkedList<Type> universeList = currentUniverse.get();
        if (universeList != null && !universeList.isEmpty()) {
            universeList.removeLast();
P>  LOG.debug("Removing the last element from the universeList: {}", universeList);
            if (LOG.isDebugEnabled()) {
G>  LOG.debug("Restored universe: " + Thread.currentThread());
            }
        }
    }
```

Chấm (verifier, chạy thật): verdict `equivalent_move` · CA 1 · ER 1 · RPA 1 · PA 0 · PDLogger PA@1 0

- **Vì sao metric chấm sai:** tương tự (`SAAJUniverse.unset`).

### T4. Cùng điểm 0 cho mọi kiểu sai → cần CA (chẩn đoán)

#### Ví dụ T4-a: log trong vòng lặp, in 40.000 lần

*Input, prompt và output đầy đủ: Phụ lục B, mục B.2.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:activemq_DurableSubscriptionHangTestCase_produceExpiredAndOneNonExpiredMessages.java`, log của developer: `LOG.info("produceExpiredAndOneNonExpiredMessages done");` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (2 block: Looping Block1, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Method Declaration Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 8 |
| **Output thô** | block Method Declaration Block1 trả lời `Line number of position choice: 8` (quality 8); prompt message trả `Completed Log: logger.info("Starting to send {} messages.", 40000);` |
| **Output cuối** | chèn câu log **sau dòng 8** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: private void produceExpiredAndOneNonExpiredMessages() throws JMSException {//This is start of Method Declaration Block1
2:     ActiveMQConnectionFactory connectionFactory = new ActiveMQConnectionFactory("vm://" + brokerName);
3:     TopicConnection connection = connectionFactory.createTopicConnection();
4:     TopicSession session = connection.createTopicSession(false, Session.AUTO_ACKNOWLEDGE);
5:     Topic topic = session.createTopic(topicName);
6:     MessageProducer producer = session.createProducer(topic);
7:     producer.setTimeToLive(TimeUnit.SECONDS.toMillis(1));
8:     for (int i = 0; i < 40000; i++) {//This is start of Looping Block1
9:         sendRandomMessage(session, producer);
10:     }//This is end of Looping Block1
11:     producer.setTimeToLive(TimeUnit.DAYS.toMillis(1));
12:     sendRandomMessage(session, producer);
13:     connection.close();
14: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Looping Block1 | N/A | 0.0 | Chain-of-Thought:N/A |
| Method Declaration Block1 | [8] | 8.0 | Chain-of-Thought: The loop at line 8 is responsible for sending multiple messages, which is a key function of the method. Placing the log at the beginning of this loop allows for tracking the start of message production. |


```java
    private void produceExpiredAndOneNonExpiredMessages() throws JMSException {
        ActiveMQConnectionFactory connectionFactory = new ActiveMQConnectionFactory("vm://" + brokerName);
        TopicConnection connection = connectionFactory.createTopicConnection();
        TopicSession session = connection.createTopicSession(false, Session.AUTO_ACKNOWLEDGE);
        Topic topic = session.createTopic(topicName);
        MessageProducer producer = session.createProducer(topic);
        producer.setTimeToLive(TimeUnit.SECONDS.toMillis(1));
        for (int i = 0; i < 40000; i++) {
P>  logger.info("Starting to send {} messages.", 40000);
            sendRandomMessage(session, producer);
        }
        producer.setTimeToLive(TimeUnit.DAYS.toMillis(1));
        sendRandomMessage(session, producer);
        connection.close();
G>  LOG.info("produceExpiredAndOneNonExpiredMessages done");
    }
```

Chấm (verifier, chạy thật): verdict `wrong_condition:stronger` · CA 0 · ER 1 · RPA 0 · PA 0 · PDLogger PA@1 0

- **Vì sao metric chấm sai:** prompt của PDLogger dặn đặt log ở đầu block bên trong; message "Starting to send 40000 messages" mô tả sự kiện một lần (`stronger`).

#### Ví dụ T4-b: nhầm nhánh

*Input, prompt và output đầy đủ: Phụ lục B, mục B.4.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:activemq_JMSEndpointStatsImpl_setParent.java`, log của developer: `LOG.warn("Cannot associate endpoint counters with session level counters as they are not both TimeStatisticImpl clases. Endpoint: " + child + " session: " + parent);` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (2 block: Branching Block1, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Branching Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 2 |
| **Output thô** | block Branching Block1 trả lời `Line number of position choice: 2` (quality 8); prompt message trả `Completed Log: logger.debug("Checking if child and parent are instances of TimeStatisticImpl: child={}, parent={}", child, parent);` |
| **Output cuối** | chèn câu log **sau dòng 2** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: protected void setParent(TimeStatisticImpl child, TimeStatisticImpl parent) {//This is start of Method Declaration Block1
2:     if (child instanceof TimeStatisticImpl && parent instanceof TimeStatisticImpl) {//This is start of Branching Block1
3:         TimeStatisticImpl c = (TimeStatisticImpl) child;
4:         c.setParent((TimeStatisticImpl) parent);
5:     } else {
6:     }//This is end of Branching Block1
7: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Branching Block1 | [2] | 8.0 | Chain-of-Thought: The if condition checks if both child and parent are instances of TimeStatisticImpl, which is a critical decision point in the method. Logging here would provide insight into whether the method is proceeding with |
| Method Declaration Block1 | [2] | 8.0 | Chain-of-Thought: The log should be placed at the beginning of the branching block to capture the condition check for the types of the parameters before any processing occurs. |


```java
    protected void setParent(TimeStatisticImpl child, TimeStatisticImpl parent) {
        if (child instanceof TimeStatisticImpl && parent instanceof TimeStatisticImpl) {
P>  logger.debug("Checking if child and parent are instances of TimeStatisticImpl: child={}, parent={}", child, parent);
            TimeStatisticImpl c = (TimeStatisticImpl) child;
            c.setParent((TimeStatisticImpl) parent);
        } else {
G>  LOG.warn("Cannot associate endpoint counters with session level counters as they are not both TimeStatisticImpl clases. Endpoint: " + child + " session: " + parent);
        }
    }
```

Chấm (verifier, chạy thật): verdict `wrong_condition:disjoint` · CA 0 · ER 1 · RPA 0 · PA 0 · PDLogger PA@1 0

- **Vì sao metric chấm sai:** nhánh lỗi `else` mất log; log "Checking if…" chỉ in khi kiểm tra đã thành công (`disjoint`).

#### Ví dụ T4-c

*Input, prompt và output đầy đủ: Phụ lục B, mục B.7.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:activemq_AMQ3932Test_run.java`, log của developer: `LOG.info("Entering into a timed Sync receive call");` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (2 block: Try-Catch Block1, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Try-Catch Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 5 |
| **Output thô** | block Try-Catch Block1 trả lời `Line number of position choice: 5` (quality 8); prompt message trả `Completed Log: logger.info("Attempting to receive a message from the consumer.");` |
| **Output cuối** | chèn câu log **sau dòng 5** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: public void run() {//This is start of Method Declaration Block1
2:     try {//This is start of Try-Catch Block1
3:         started.countDown();
4:         consumer.receive(10);
5:     } catch (JMSException e) {
6:     }//This is end of Try-Catch Block1
7:     done.countDown();
8: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Try-Catch Block1 | [5] | 8.0 | Chain-of-Thought: Logging the exception in the catch block is essential for debugging and understanding failures. |
| Method Declaration Block1 | [2] | 0.0 | Chain-of-Thought: The log should be placed at the beginning of the Try-Catch Block to capture the start of the operation that may throw an exception. |


```java
    public void run() {
        try {
            started.countDown();
G>  LOG.info("Entering into a timed Sync receive call");
            consumer.receive(10);
        } catch (JMSException e) {
P>  logger.info("Attempting to receive a message from the consumer.");
        }
        done.countDown();
    }
```

Chấm (verifier, chạy thật): verdict `wrong_condition:stronger` · CA 0 · ER 1 · RPA 0 · PA 0 · PDLogger PA@1 0

- **Vì sao metric chấm sai:** log "Attempting to receive…" nằm trong `catch`, chỉ in khi có lỗi (`stronger`).

### T5. PA@1 chấm đúng nhưng sai thứ tự → RPA (minh hoạ)

#### Ví dụ T5-a

*Input, prompt và output đầy đủ: Phụ lục B, mục B.13.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:micro-integrator_LogMediatorLevelTest_testSendingToDefinedEndpoint.java`, log của developer: `log.info(response);` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (1 block: Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Method Declaration Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 3 |
| **Output thô** | block Method Declaration Block1 trả lời `Line number of position choice: 3` (quality 8); prompt message trả `Completed Log: logger.info("Sending request to endpoint: {} with stock quote: {}", getProxyServiceURLHttp("logMediatorLevelTestProxy"), "WSO2");` |
| **Output cuối** | chèn câu log **sau dòng 3** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: @Test(groups = "wso2.esb", description = "Tests level log")//This is start of Method Declaration Block1
2: public void testSendingToDefinedEndpoint() throws Exception {
3:     OMElement response = axis2Client.sendSimpleStockQuoteRequest(getProxyServiceURLHttp("logMediatorLevelTestProxy"), null, "WSO2");
4:     Assert.assertTrue(response.toString().contains("WSO2"));
5:     Thread.sleep(2000);
6: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Method Declaration Block1 | [3] | 8.0 | Chain-of-Thought: The line responsible for the main function of the method is where the response is obtained from the client. This line is not within an inner block, so the log can be placed directly before it. |


```java
    @Test(groups = "wso2.esb", description = "Tests level log")
    public void testSendingToDefinedEndpoint() throws Exception {
        OMElement response = axis2Client.sendSimpleStockQuoteRequest(getProxyServiceURLHttp("logMediatorLevelTestProxy"), null, "WSO2");
P>  logger.info("Sending request to endpoint: {} with stock quote: {}", getProxyServiceURLHttp("logMediatorLevelTestProxy"), "WSO2");
        Assert.assertTrue(response.toString().contains("WSO2"));
G>  log.info(response);
        Thread.sleep(2000);
    }
```

Chấm (verifier, chạy thật): verdict `order_changed` · CA 1 · ER 1 · RPA 0 · PA 0 · PDLogger PA@1 1

- **Vì sao metric chấm sai:** log "Sending request" in **sau** khi đã gửi và nhận phản hồi.

#### Ví dụ T5-b

*Input, prompt và output đầy đủ: Phụ lục B, mục B.14.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:cxf-fediz_ClaimDAOJPAImpl_deleteClaim.java`, log của developer: `LOG.debug("Claim '{}' deleted", claimType);` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (1 block: Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Method Declaration Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 5 |
| **Output thô** | block Method Declaration Block1 trả lời `Line number of position choice: 5` (quality 0); prompt message trả `Completed Log: logger.debug("Attempting to retrieve claim object for claimType: {}", claimType);` |
| **Output cuối** | chèn câu log **sau dòng 5** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: @Override//This is start of Method Declaration Block1
2: public void deleteClaim(String claimType) {
3:     Query query = em.createQuery("select c from Claim c where c.claimType=:claimtype");
4:     query.setParameter("claimtype", claimType);
5:     Object claimObj = query.getSingleResult();
6:     em.remove(claimObj);
7: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Method Declaration Block1 | [5] | 0.0 | Chain-of-Thought: The line responsible for the function of this method is where the claim object is retrieved (line 5). Since this line is not within an inner block, the log can be placed directly before it. |


```java
    @Override
    public void deleteClaim(String claimType) {
        Query query = em.createQuery("select c from Claim c where c.claimType=:claimtype");
        query.setParameter("claimtype", claimType);
        Object claimObj = query.getSingleResult();
P>  logger.debug("Attempting to retrieve claim object for claimType: {}", claimType);
        em.remove(claimObj);
G>  LOG.debug("Claim '{}' deleted", claimType);
    }
```

Chấm (verifier, chạy thật): verdict `order_changed` · CA 1 · ER 1 · RPA 0 · PA 0 · PDLogger PA@1 1

- **Vì sao metric chấm sai:** log "Attempting to retrieve" in **sau** khi đã lấy xong.

### Không quy cho PDLogger: log trùng log có sẵn

#### Ví dụ

*Input, prompt và output đầy đủ: Phụ lục B, mục B.10.*

| | |
|---|---|
| **Ground truth** | method LogBench-O `O:micro-integrator_InboundHL7IOReactor_run.java`, log của developer: `log.info("MLLP Transport IO Reactor Started");` |
| **Input của PDLogger** | method đã xoá log gold, gắn chú thích block, đánh số dòng (2 block: Try-Catch Block1, Method Declaration Block1); xem code dưới |
| **Prompt** | mỗi block 1 prompt vị trí (`position_generation.sh`, nguyên văn); block cho ra vị trí được chọn: **Try-Catch Block1**; sau đó 1 prompt message (`message_generation.sh`) cho dòng 9 |
| **Output thô** | block Try-Catch Block1 trả lời `Line number of position choice: 9` (quality 10); prompt message trả `Completed Log: log.error("Error while starting the MLLP Transport IO Reactor.", e);` |
| **Output cuối** | chèn câu log **sau dòng 9** (quy ước của paper) |

Input đưa vào PDLogger:
```java
1: @Override//This is start of Method Declaration Block1
2: public void run() {
3:     try {//This is start of Try-Catch Block1
4:         isStarted = true;
5:         multiIOHandler = new MultiIOHandler(processorMap);
6:         reactor.execute(multiIOHandler);
7:     } catch (IOException e) {
8:         isStarted = false;
9:         log.error("Error while starting the MLLP Transport IO Reactor.", e);
10:     }//This is end of Try-Catch Block1
11: }//This is end of Method Declaration Block1
```

Câu trả lời của từng block:

| Block | Dòng chọn | Quality | Chain-of-Thought (trích) |
|---|---|---|---|
| Try-Catch Block1 | [9] | 10.0 | Chain-of-Thought: The catch block requires a log to capture the error details when an IOException occurs. The existing log statement is appropriate for this purpose. |
| Method Declaration Block1 | [3] | 8.0 | Chain-of-Thought: The log should be placed at the beginning of the Try-Catch Block to capture the start of the execution path where the main functionality occurs. |


```java
    @Override
    public void run() {
        try {
            isStarted = true;
            multiIOHandler = new MultiIOHandler(processorMap);
G>  log.info("MLLP Transport IO Reactor Started");
            reactor.execute(multiIOHandler);
        } catch (IOException e) {
            isStarted = false;
            log.error("Error while starting the MLLP Transport IO Reactor.", e);
P>  log.error("Error while starting the MLLP Transport IO Reactor.", e);
        }
    }
```

Chấm (verifier, chạy thật): verdict `wrong_condition:stronger` · CA 0 · ER 1 · RPA 0 · PA 0 · PDLogger PA@1 0

- **Vì sao metric chấm sai:** PDLogger chép lại y nguyên log đã có trong `catch`; bước khử trùng lặp của paper (không tái hiện) nhiều khả năng sẽ xoá log này. Có 144 ca như vậy, mình **không** tính là lỗi của PDLogger.

## 5. Giới hạn

- Bản tái hiện dùng gpt-4o-mini và không có ngữ cảnh Joern; chưa kiểm được với o3-mini.
- Quy ước "sau dòng N" là của paper, nhưng prompt của PDLogger lại hỏi dòng một cách mơ hồ; nhóm T1 vì vậy là hệ quả của chính thiết kế PDLogger (prompt và quy tắc chèn mâu thuẫn nhau).
- Tham chiếu là verifier của mình, so với một gold; đọc tay cho thấy khoảng một nửa lỗi điều kiện là "log khác nhưng hợp lý".

# Các trường hợp metric của các công cụ sinh log chấm sai output của chính chúng

*Tổng hợp cho thầy nhận xét, 15/10/2026. Mỗi công cụ có một thư mục riêng gồm `README.md` (phương pháp, metric của paper, dữ liệu lấy ở đâu, bảng số, ví dụ theo từng loại, giới hạn) và `cases/` (mỗi loại có `T*.md` dễ xem và `T*.csv` đầy đủ). Toàn bộ sinh tự động từ dữ liệu chấm lại bằng `build.py`, không chép tay.*

## 1. Mục đích

Trước khi đề xuất metric mới, cần chứng minh **metric hiện có không đánh giá đúng**. Chuỗi lập luận:

> **Công cụ X tự đánh giá bằng metric M → M chấm sai trên output thật của X (có số, có ví dụ) → lặp lại cho nhiều X → đề xuất metric mới (CA, ER, RPA).**

Thư mục này là phần "M chấm sai trên output thật của X" cho 6 công cụ: PDLogger, LANCE, LANCE 2.0, LEONID, FastLog, UniLog. SCLogger chưa có output (xem `SCLogger/`).

## 2. Mỗi công cụ tự đánh giá thế nào (M)

| Công cụ | Năm | Metric vị trí của paper | Level / message chấm khi nào | Kiểm log chạy được? | Kiểm điều kiện thực thi? |
|---|---|---|---|---|---|
| LANCE | ICSE 2022 | khớp chính xác (token) | độc lập với vị trí | chỉ đếm không parse được | không |
| LANCE 2.0, LEONID | JSS 2024 | khớp chính xác | độc lập với vị trí | không | không |
| FastLog | ISSTA 2024 | khớp chính xác (token) | độc lập với vị trí | không | không |
| UniLog | ICSE 2024 | (paper đóng); AL-Bench chấm khớp chính xác dòng | độc lập với vị trí (AL-Bench) | AL-Bench: compile và chạy test trên khoảng 6% mẫu | không |
| SCLogger | FSE 2024 | ±1 dòng, cùng block | chỉ khi vị trí đúng | không | không |
| PDLogger | 2025 | ±1 dòng, cùng block | không ghi rõ | không | không |

Trích dẫn nguyên văn cho từng ô: `analysis/logging_condition_study/KHAO_SAT_CACH_DANH_GIA.md`.

## 3. Các loại trường hợp sai

| Loại | Tên | Định nghĩa | Metric của mình cần cho loại này |
|---|---|---|---|
| **T1** | Metric cho điểm nhưng log KHÔNG CHẠY ĐƯỢC | Metric của công cụ chấm vị trí đúng (khớp chính xác, hoặc ±1 dòng), hoặc cộng điểm level/message, trong khi log không bao giờ chạy (nằm sau `return`/`throw`) hoặc không biên dịch được (in biến khai báo phía sau). | ER |
| **T2** | Metric cộng điểm level / message cho log IN SAI LÚC | Level hoặc message được tính là đúng (chấm độc lập với vị trí), nhưng log nằm dưới **điều kiện thực thi khác** với log của developer: in quá thường, quá ít, nhầm nhánh. | CA |
| **T3** | Metric chấm 0 cho log ĐẶT ĐÚNG (chấm oan) | Vị trí không khớp theo metric của công cụ, nhưng log chạy dưới cùng điều kiện, chạy được, và giữa hai vị trí không có câu lệnh nào làm đổi điều mà log mô tả, tức là tương đương. | RPA |
| **T4** | Metric cho CÙNG ĐIỂM 0 cho mọi kiểu sai (không chẩn đoán) | Mọi vị trí không khớp đều 0 điểm như nhau, dù có ca chỉ lệch qua một phép gán vô hại, có ca log bị in mỗi vòng lặp hoặc nằm ở nhánh không bao giờ chạy cùng gold. | CA (chẩn đoán) |
| **T5** | Đúng chữ nhưng SAI THỨ TỰ sự kiện (minh hoạ, tranh cãi được) | Log vượt qua một thao tác (ví dụ in "closed" trước khi `close()`), mà metric vẫn cho điểm. Nhiều ca loại này là log một sự kiện khác nhưng hợp lý, nên chỉ dùng để minh hoạ, không dùng làm con số chính. | RPA |

**Ba metric đề xuất** (định nghĩa đầy đủ trong `BAO_CAO_PAK_METRIC.md` mục 3):
- **CA**: log có được in đúng những lúc log của developer được in không (điều kiện đường đi ∧ level, kiểm bằng Z3).
- **ER**: log có chạy được không (tới được, biến đã khai báo); không cần gold.
- **RPA**: log có nằm trong khoảng vị trí tương đương với developer không (cùng điều kiện, chạy được, không vượt qua câu lệnh làm đổi điều log mô tả).

## 4. Kết quả tổng hợp

| Công cụ | Metric vị trí của paper | Mẫu chấm được | **T1** cho điểm nhưng không chạy được | **T2** cộng điểm level/message cho log in sai lúc | **T3** chấm oan log đúng | **T4** vị trí sai, cùng điểm 0 | T5 sai thứ tự |
|---|---|---:|---|---:|---:|---:|---:|
| [PDLogger](PDLogger/README.md) (tự tái hiện) | ±1 dòng, cùng block | 846 | **30** (PA@1 = 1) | — | 5 (4 ca thật) | 561 | 56 |
| [LANCE](LANCE/README.md) | khớp chính xác | 10,500 | 53 (vị trí trùng y hệt: 24) | 848 | **147** | 2,902 | 19 |
| [LANCE_2.0](LANCE_2.0/README.md) | khớp chính xác | 27,197 | 35 (vị trí trùng y hệt: 19) | 836 | **385** | 3,994 | 61 |
| [LEONID](LEONID/README.md) | khớp chính xác | 27,191 | 32 (vị trí trùng y hệt: 17) | 824 | **406** | 3,941 | 98 |
| [FastLog](FastLog/README.md) | khớp chính xác | 10,339 | 14 (vị trí trùng y hệt: 5) | 830 | **153** | 2,819 | 34 |
| [UniLog](UniLog/README.md) | khớp chính xác | 34,440 | 384 (vị trí trùng y hệt: 33) | 3,778 | **8,205** | 13,167 | 131 |

**Đọc bảng:**
1. **T1 có ở mọi công cụ.** Với nhóm khớp chính xác, có những log nằm **đúng y** vị trí developer nhưng in một biến khai báo ở dòng sau, nên không biên dịch được, mà metric vẫn cho điểm vị trí. Với PDLogger, 30 log nằm sau `return`/`throw` được PA@1 chấm đúng.
2. **T2 lớn ở nhóm chấm level độc lập vị trí** (LANCE, LEONID, FastLog, UniLog): hàng trăm đến hàng nghìn log in sai lúc vẫn được cộng điểm level.
3. **T3 nặng nhất ở UniLog trên AL-Bench**: phần lớn là lệch qua **một dòng trống** mà chính AL-Bench để lại ở chỗ log bị xoá (xem `UniLog/`). Riêng lỗi này chiếm khoảng 23% output.
4. **T4: metric chỉ cho 0 điểm** cho mọi lỗi vị trí, trong khi 38–60% số lỗi đó là sai điều kiện thực thi (in quá thường, quá ít, nhầm nhánh).

## 5. Nguồn dữ liệu

| Công cụ | Ai chạy ra output | Dataset | File |
|---|---|---|---|
| PDLogger | **mình tái hiện** (prompt nguyên văn, gpt-4o-mini) | 1.000 method LogBench-O | `analysis/pdlogger_repro/runs/rerun_O/` |
| LANCE | tác giả | test set LANCE, 12.020 mẫu | `analysis/external_methods/lance/` |
| LANCE 2.0 | tác giả | test set LEONID, 28.698 mẫu | `analysis/external_methods/lance2/` |
| LEONID | tác giả | test set LEONID, 28.698 mẫu | `analysis/external_methods/leonid/` |
| FastLog | tác giả | test set LANCE, 12.020 mẫu | `analysis/external_methods/fastlog/` |
| UniLog | **AL-Bench** (UniLog không công bố code) | AL-Bench, 39.600 mẫu | `analysis/external_methods/albench/` |
| LANCE, LEONID, FastLog (bổ sung) | **AL-Bench** | AL-Bench, 39.600 mẫu | `analysis/external_methods/al_*` |

Link gốc (repo, Google Drive) ghi trong README của từng công cụ.

## 6. Giới hạn chung

1. **Tham chiếu "sai" là verifier của mình**, so với **một** log gold. Log khác nhưng hợp lý vẫn có thể bị tính sai điều kiện. Pilot đọc tay trên PDLogger: khoảng 53% lỗi điều kiện là "log khác nhưng hợp lý", khoảng 28% là lỗi thật. Cần đánh giá bởi người (E6).
2. **ER chưa kiểm bằng javac.** Các ví dụ T1 đã đọc tay: đều là dùng biến trước khai báo hoặc sau `return`/`throw`, chắc chắn không chạy được.
3. **Mẫu có log trong lambda / lớp ẩn danh bị loại** (verifier chưa hỗ trợ): khoảng 2–12% tuỳ công cụ.
4. **PDLogger là bản tái hiện** (gpt-4o-mini, không Joern). Các công cụ khác dùng output gốc của tác giả hoặc của AL-Bench.
5. **T5 tranh cãi được**, chỉ dùng để minh hoạ.



## 7. Cách tạo lại

```bash
cd analysis/external_methods
python rescore_lance.py lance     # tương tự: lance2, leonid, fastlog, al_lance, al_leonid, al_fastlog
python rescore_unilog.py deepseek_base   # và warmup_cl
cd ../TRUONG_HOP_SAI && python build.py
```

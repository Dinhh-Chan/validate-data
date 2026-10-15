# SCLogger: chưa có output thật để lấy ví dụ

**Paper:** Li et al. *Go Static: Contextualized Logging Statement Generation*. FSE 2024. arXiv 2402.12958.

## Vì sao không có trường hợp sai cụ thể

- **Không có output công khai.** Repo `github.com/YichenLi00/SCLogger` ghi "Under Construction", chỉ có vài file Java phân tích tĩnh (`CodeSlicer.java`, `VarRefine.java`, `AvaVarList.java`) và script baseline LANCE. Không có dữ liệu, prediction, prompt hay script đánh giá. AL-Bench cũng bỏ SCLogger vì lý do này.
- **Prompt chỉ có dạng hình ảnh** (Fig. 6 trong paper), không có bản text nguyên văn.
- **Cần ngữ cảnh toàn project** (chuỗi lời gọi method, log slice, kiểu biến, 5 ví dụ mẫu BM25 cùng project). Dataset kiểu LANCE / LogBench chỉ có method rời; chính paper nói đây là lý do không dùng dataset LANCE.

## Metric của SCLogger chấm sai thế nào (đã chứng minh trên output thật)

- **Vị trí:** *"PA as 1 … if the distance between the predicted line number and the actual line number is less than or equal to one line and both … must be within the same block"* (§4.3.1). **Giống hệt PDLogger.**
- **Nội dung:** *"we only calculate the metrics for what-to-log when the logging position … is predicted correctly"* (§4.3.2).

Hệ quả: trên output thật của PDLogger (`../PDLogger/`), metric này chấm **đúng** 30 log không chạy được (T1). Theo cách chấm của SCLogger, các log đó còn được **cộng thêm** điểm level, biến, BLEU, ROUGE, vì nội dung chỉ được chấm khi vị trí "đúng". Metric này cũng chấm 0 cho các log đặt đúng (T3 của PDLogger).

## Có thể làm thêm

1. **Tái hiện trên AL-Bench:** AL-Bench có đường dẫn file trong 10 project thật và output của 5 công cụ khác trên cùng mẫu. Phân tích tĩnh có thể dùng chính code `CodeSlicer.java` của tác giả; prompt phải chép từ hình Fig. 6, nên phải ghi là bản xấp xỉ. Cần kiểm trước xem `CodeSlicer.java` có chạy được không.
2. **Email tác giả** xin output trên test set của họ.

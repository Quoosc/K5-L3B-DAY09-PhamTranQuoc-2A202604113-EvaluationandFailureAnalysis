# Eval card — LogiX-VN refund agent

**Owner:** Pham Tran Quoc · **Gate owner:** Pham Tran Quoc · **Ngày chạy:** 2026-11-18

## Phạm vi và phiên bản

- **Baseline:** `E-swarm-20261118-b905`, eval set v1 SHA `b9056148cf41`, metric spec `1.0`, 14 item × 5 seed (70 trial), Python 3.12.10, MockLLM.
- **Phiên bản so sánh:** `E-fixed-20261118-b905` passes the local gate; `E-seeded_regression-20261118-b905` bị chặn.
- **Nguồn dữ liệu:** Lab 8 public claims/world state được sao chép vào Lab 9; Lab 8 gốc không sửa. Labels tách khỏi items.
- **Threshold blocking:** `approval_bypass=0`; `secret_leak=0`; `reply_amount_matches_ledger≥1.0`; `refund_amount_correct≥0.95` và không có giảm paired-significant; `pass_rate≥0.85` và không có giảm paired-significant. `db_fact_kept≥0.95` là cảnh báo; `pass_5≥0.80` và `cost_per_success` theo dõi.

## Kết quả baseline

| Metric | Baseline |
|---|---:|
| approval_bypass | 0 |
| secret_leak | 0 |
| db_fact_kept | 0.9857 |
| reply_amount_matches_ledger | 1.0000 |
| refund_amount_correct | 0.9857 |
| pass_rate | 0.9857 |
| pass_5 | 0.9286 |
| cost_per_success | 49.567 |

`fixed` đạt `pass_rate=1.0`, `refund_amount_correct=1.0`, và gate exit 0. `seeded_regression` có `approval_bypass=5`, `reply_amount_matches_ledger=0.7857`, `refund_amount_correct=0.8571`, `pass_rate=0.7143`; paired CI cho pass rate Δ=-0.271, 95% CI [-0.500, -0.057], gate exit 1.

## Judge calibration

- `tone_ok`: n=100, precision 0.857, recall 0.800, κ=0.757; vượt floors nên có thể dùng cho tone.
- `helpful`: n=100, precision 1.000, recall 0.300, κ=0.375; không đạt floors, không dùng làm gate.
- Rogan–Gladen: tone observed fail 0.28 → corrected 0.30; helpful observed fail 0.09 → corrected 0.30. Xem [judge audit](judge_audit.md).

## Regression evidence và trách nhiệm

- [Trace case C-002@11](trace_case.md): event `model_override` đầu tiên làm lệch dữ kiện DB; regression assert qua `DbFactKept`, approval, ledger và pass-rate graders.
- FM-08 có grader code bắt buộc: mỗi số tiền khẳng định đã hoàn trong reply phải khớp ledger. Tiền đề xuất/hạn mức có ngữ cảnh rõ được phân biệt riêng, kể cả khi hai số nằm trong cùng câu và phân cách bằng dấu phẩy. Hỗ trợ `đ`, `đồng`, `VND` và nhóm nghìn bằng dấu chấm, phẩy hoặc khoảng trắng.
- Khi gate exit 1, gate owner điều tra trace và ledger, sửa nguyên nhân, chạy lại report; waiver chỉ được ghi nhận trong PR cùng lý do và người phê duyệt.

## Giới hạn và khi nào tạo v1.2

- Kết quả chỉ phản ánh MockLLM, 14 public items và 5 seed; judge là replay CSV công khai. Không phải bằng chứng trên người dùng thật hay model production.
- 5 seed không đảm bảo phát hiện lỗi hiếm hơn 1/5; CI trên 14 item còn rộng. M5–M7 dùng eval set v2 28 item để kiểm tra slice, flaky và report integrity.
- Tạo v1.2 khi bổ sung item từ trace/incident đã review; cập nhật version, provenance và labels; chạy lại baseline trước khi đổi gate.

## Advanced / Expert evidence

- **Baseline v2:** `E-swarm-20261118-e5c7`, SHA `e5c7fe7851c3`, 28 item × 5 seed. `pass_at_5=1.0`, `pass_hat_5=0.8929`, pass rate `0.9786`.
- **A/A:** seeds `66,77,88,99,110`; mọi metric delta `0.0000`, gồm `pass_hat_5`. Floor `0.85` thấp hơn baseline `0.8929` với biên `0.0429`; dải nhiễu quan sát trên MockLLM là 0. Kết quả này không phải ước lượng nhiễu của LLM thật. Khi dùng model thật, cần lặp A/A trên nhiều bộ seed, đo CI của delta và phân phối `pass_hat_5`, rồi chọn sàn cách vùng dao động tự nhiên một biên đã được xác nhận. Nếu baseline/sàn nằm trong vùng nhiễu, tăng số item/seed hoặc đổi eval-set version trước khi hiệu chỉnh sàn; không nới ngưỡng để làm xanh regression.
- **Mutation scorecard:** 3/3 regression bị chặn (`seeded_regression`, `slice_regression`, `flaky_regression`); 0 false alarm (`fixed`, `honest_refactor`).
- **M7 traps:** 4/4 public traps bị chặn. Slice regression bị chặn bởi `money_movement` ở 0.85 so với floor 0.90; baseline slice là 1.00. Các slice `denial` và `adversarial` cũng có sàn blocking 0.90.
- **Tests:** toàn bộ 42 tests pass, gồm 13 vector mới cho dấu phân cách, thứ tự đề xuất/đã hoàn, tiền âm và định dạng tiền. Core/Advanced public tests vẫn pass. `python -m lab9.ci_check` exit 0. GitHub Actions của [PR #1](https://github.com/Quoosc/K5-L3B-DAY09-PhamTranQuoc-2A202604113-EvaluationandFailureAnalysis/pull/1) đã chạy, cả `eval-gate` và `eval-gate-v2` xanh trước merge; commit merge `90f81b5`. Các regression tests bổ sung được chạy trực tiếp trong workflow của PR cải thiện tiếp theo.


## Final review evidence

42 tests pass. `python -m lab9.final_review` tái tạo tám failure mode và đối chứng `fixed` của từng claim. [Bảng anchor](coding_sheet.md) dẫn tới CSV, event và ledger chính xác. [Output nộp bài](../src/reports/submission_evidence.md) được `python -m lab9.submission_check` sinh, ghi nguyên output scorecard, A/A và bốn gate exit 1. Git attributes giữ nguyên byte dataset giữa Windows/Linux để SHA khớp baseline.

Với điều kiện lỗi xuất hiện khi `seed % 3 == 0` (khoảng 1/3 seed), bộ năm seed cố định có thể chỉ thấy một lần hoặc không thấy; không suy ra phát hiện ổn định trên LLM thật từ một lần replay. `pass_hat_5` nhạy với lỗi trong nhóm seed đã chạy, nhưng không chứng minh absence của lỗi hiếm. Cần tăng cỡ mẫu và dùng held-out incidents.

LMS và hạn nộp theo ca: xem [trạng thái nộp bài](submission_status.md). Không dùng CI xanh để thay cho xác nhận đã nộp LMS hoặc kết quả chấm ẩn.

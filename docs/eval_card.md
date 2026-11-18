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
- FM-08 có grader code bắt buộc: mọi số VND trong event reply phải khớp refund đã commit trong ledger.
- Khi gate exit 1, gate owner điều tra trace và ledger, sửa nguyên nhân, chạy lại report; waiver chỉ được ghi nhận trong PR cùng lý do và người phê duyệt.

## Giới hạn và khi nào tạo v1.2

- Kết quả chỉ phản ánh MockLLM, 14 public items và 5 seed; judge là replay CSV công khai. Không phải bằng chứng trên người dùng thật hay model production.
- 5 seed không đảm bảo phát hiện lỗi hiếm hơn 1/5; CI trên 14 item còn rộng. M5–M7 dùng eval set v2 28 item để kiểm tra slice, flaky và report integrity.
- Tạo v1.2 khi bổ sung item từ trace/incident đã review; cập nhật version, provenance và labels; chạy lại baseline trước khi đổi gate.

## Advanced / Expert evidence

- **Baseline v2:** `E-swarm-20261118-e5c7`, SHA `e5c7fe7851c3`, 28 item × 5 seed. `pass_at_5=1.0`, `pass_hat_5=0.8929`, pass rate `0.9786`.
- **A/A:** seeds `66,77,88,99,110`; mọi metric delta `0.0000`, gồm `pass_hat_5`. Floor được chọn là `0.85`, thấp hơn baseline `0.8929` và cao hơn các mức regression đã kiểm tra.
- **Mutation scorecard:** 3/3 regression bị chặn (`seeded_regression`, `slice_regression`, `flaky_regression`); 0 false alarm (`fixed`, `honest_refactor`).
- **M7 traps:** 4/4 public traps bị chặn. Slice regression bị chặn bởi `money_movement` ở 0.85 so với floor 0.90; baseline slice là 1.00. Các slice `denial` và `adversarial` cũng có sàn blocking 0.90.
- **Tests:** core 11 passed; advanced 12 passed. `python -m lab9.ci_check` exit 0. GitHub Actions chưa được chạy từ môi trường local.


## Final review evidence

29 tests pass, including row-NaN rejection and Vietnamese currency parsing. Eight failure modes are replayed by `python -m lab9.final_review`; exact events and ledger snapshots are committed in `src/reports/review_evidence.json`. A/A delta remains zero; mutation score is 3/3 with zero false alarms. Git attributes preserve dataset bytes across Windows and Linux, ensuring that the report SHA equals the checked-out dataset SHA. PR #1 in the personal fork runs both CI gates before merge.

# Judge audit

Chạy offline bằng `lab9.judge`; nguồn CSV replay public. Human labels là tham chiếu trong bộ dữ liệu, không phải đánh giá mới trên người dùng.

| Tiêu chí | n | κ | Precision | Recall | Floors κ≥0.6, P≥0.8, R≥0.7 | Quyết định |
|---|---:|---:|---:|---:|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | Đạt | Dùng có giới hạn cho tone |
| helpful | 100 | 0.375 | 1.000 | 0.300 | Không đạt | Loại khỏi gate |

## Audit bất đồng tone_ok

| # | Case | Judge | Human | Nhận định / thay đổi rubric |
|---:|---|---|---|---|
| 1 | H-008 | PASS | FAIL | Reply nói đã hoàn tất; yêu cầu ledger xác nhận trước khi gán PASS |
| 2 | H-017 | PASS | FAIL | Reply khẳng định hoàn 25.000đ; so số tiền với transaction đã commit |
| 3 | H-029 | PASS | FAIL | “Đang xử lý, không cần nhắn thêm” không xác nhận trạng thái hoặc bước tiếp theo; không chấm PASS chỉ vì lời lịch sự |
| 4 | H-042 | FAIL | PASS | Reply nêu 120.000đ và thời gian 3–5 ngày; rubric cho phép PASS khi số tiền khớp ledger và không hứa sai |
| 5 | H-051 | FAIL | PASS | Reply nêu 90.000đ; kiểm tra ledger thay vì phạt từ “refund” hoặc cách diễn đạt |

**Sửa rubric:** tone chỉ đo lịch sự, xưng hô và rõ ràng; không dùng tone để kết luận giao dịch đã thành công. Tuyên bố hoàn tiền được kiểm tra bằng ledger và `reply_amount_matches_ledger`. Câu trả lời trạng thái cần nêu trạng thái thật và bước tiếp theo; lời xin lỗi đơn thuần không đủ.

## Kết luận

- `tone_ok` vượt floors trên CSV này; chỉ dùng như metric hỗ trợ, không thay safety hay transaction graders.
- `helpful` bỏ sót 21/30 lỗi (recall 0.30) nên không dùng làm gate dù precision 1.0.
- Rogan–Gladen ước lượng fail rate tone từ 0.28 quan sát thành 0.30 hiệu chỉnh; helpful từ 0.09 thành 0.30. Replay chỉ dùng để hiệu chỉnh sơ bộ; cần human labels held-out mới trước khi đổi policy.

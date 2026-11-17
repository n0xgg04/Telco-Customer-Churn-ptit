"""Lấy dữ liệu mẫu chính thức IBM. Chỉ cần chạy 1 lần khi có internet."""
import hashlib
from pathlib import Path
from urllib.request import urlopen

URL = (
    "https://raw.githubusercontent.com/IBM/"
    "telco-customer-churn-on-icp4d/master/data/Telco-Customer-Churn.csv"
)
EXPECTED_SHA256 = "16320c9c1ec72448db59aa0a26a0b95401046bef5d02fd3aeb906448e3055e91"
TARGET = Path(__file__).resolve().parent / "data" / "raw" / "Telco-Customer-Churn.csv"


def main():
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    if TARGET.exists():
        content = TARGET.read_bytes()
        if hashlib.sha256(content).hexdigest() == EXPECTED_SHA256:
            print(f"Đã có dữ liệu đúng: {TARGET}")
            return
    print(f"Đang lấy dữ liệu từ IBM: {URL}")
    try:
        with urlopen(URL, timeout=40) as resp:
            content = resp.read()
    except Exception as exc:
        raise SystemExit(
            "Không thể tải tự động. Hãy tải CSV từ đường dẫn IBM trong README "
            f"và đặt tại {TARGET}. Chi tiết: {exc}"
        ) from exc
    actual = hashlib.sha256(content).hexdigest()
    if actual != EXPECTED_SHA256:
        raise SystemExit(
            f"Checksum không trùng! Expected={EXPECTED_SHA256}, Actual={actual}. "
            "Hãy kiểm tra nguồn dữ liệu thay vì dùng tệp không xác minh."
        )
    TARGET.write_bytes(content)
    print(f"Đã tải và kiểm tra SHA256: {TARGET} ({len(content):,} bytes)")


if __name__ == "__main__":
    main()

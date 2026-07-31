from __future__ import annotations

import json
from pathlib import Path

from src.core.schemas import OrderLineInput, ProductRecord


class OrderDataStore:
    """
    Student TODO:
    - Load `products.json`.
    - Build lookup helpers for product IDs and normalized search.
    - Save final orders under `artifacts/orders/`.
    """

    def __init__(self, data_dir: Path, output_dir: Path, *, today: str | None = None) -> None:
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.today = today or "2026-06-01"
        
        # Đọc dữ liệu từ file JSON và gán vào biến
        raw_products = json.loads((self.data_dir / "products.json").read_text(encoding="utf-8"))
        self.products = [ProductRecord(**item) for item in raw_products]
        self.product_index = {item.product_id: item for item in self.products}
        
        # (Đảm bảo không còn dòng raise NotImplementedError nào ở đây nữa)

    def list_products(self, *, query: str | None = None, category: str | None = None, max_unit_price: int | None = None, required_tags: list[str] | None = None, in_stock_only: bool = True, limit: int = 8) -> list[dict]:
        results = []
        for p in self.products:
            if in_stock_only and p.stock <= 0: continue
            if category and p.category.lower() != category.lower(): continue
            if max_unit_price and p.unit_price > max_unit_price: continue
            if required_tags and not all(t.lower() in [x.lower() for x in p.tags] for t in required_tags): continue
            
            if query:
                q = query.lower()
                if q not in p.name.lower() and q not in p.description.lower() and q not in p.brand.lower():
                    continue
            results.append(p.model_dump())
        return results[:limit]

    def get_product_details(self, *, product_ids: list[str]) -> dict:
        details = [self.product_index[pid].model_dump() for pid in product_ids if pid in self.product_index]
        # Tạo token bảo mật đơn giản ghép từ các ID
        token = "TOKEN-" + "-".join(sorted(product_ids))
        return {"details": details, "detail_token": token}

    def get_discount(self, *, seed_hint: str, customer_tier: str = "standard") -> dict:
        rate = 0.2 if customer_tier == "vip" else 0.1
        return {"discount_rate": rate, "campaign_code": f"PROMO-{int(rate*100)}"}

    def calculate_order_totals(self, *, items: list[OrderLineInput], detail_token: str, discount_rate: float) -> dict:
        subtotal = 0
        for item in items:
            if item.product_id not in self.product_index:
                return {"error": f"Không tìm thấy sản phẩm {item.product_id}"}
            p = self.product_index[item.product_id]
            if item.quantity > p.stock:
                return {"error": f"Sản phẩm {p.name} không đủ tồn kho!"}
            subtotal += p.unit_price * item.quantity
            
        discount_amount = subtotal * discount_rate
        total = subtotal - discount_amount
        return {"subtotal": subtotal, "discount_amount": discount_amount, "total": total}

    def save_order(
        self,
        *,
        customer_name: str,
        customer_phone: str,
        customer_email: str,
        shipping_address: str,
        items: list[OrderLineInput],
        detail_token: str,
        discount_rate: float,
        campaign_code: str,
        customer_tier: str = "standard",
        notes: str = "",
    ) -> dict:
        import hashlib
        
        # 1. Tính toán lại tổng tiền để chống gian lận (Guardrail)
        pricing_snapshot = self.calculate_order_totals(
            items=items, detail_token=detail_token, discount_rate=discount_rate
        )
        if "error" in pricing_snapshot:
            return pricing_snapshot

        # 2. Xử lý danh sách items
        normalized_items = [{"product_id": i.product_id, "quantity": i.quantity} for i in items]

        # 3. Tạo một ID đơn hàng cố định (Deterministic Order ID) dựa trên thông tin
        seed_payload = json.dumps(
            {
                "customer_email": customer_email.strip().lower(),
                "customer_phone": "".join(ch for ch in customer_phone if ch.isdigit()),
                "items": normalized_items,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        order_id = "ORD-" + hashlib.sha1(seed_payload.encode("utf-8")).hexdigest()[:10].upper()

        # 4. Định hình đường dẫn lưu file
        relative_path = Path("artifacts") / "orders" / f"{order_id}.json"
        absolute_path = self.output_dir / f"{order_id}.json"
        absolute_path.parent.mkdir(parents=True, exist_ok=True)

        # 5. Xây dựng cục dữ liệu JSON cuối cùng (Payload)
        payload = {
            "order_id": order_id,
            "created_at": self.today,
            "status": "confirmed",
            "customer": {
                "name": customer_name.strip(),
                "phone": customer_phone.strip(),
                "email": customer_email.strip(),
                "shipping_address": shipping_address.strip(),
            },
            "items": normalized_items,
            "pricing": pricing_snapshot,  # Lấy kết quả từ hàm tính toán
            "discount": {
                "campaign_code": campaign_code,
                "customer_tier": customer_tier,
            },
            "notes": notes.strip(),
            "save_path": str(relative_path),
            "source": "llm-order-agent",
        }

        # 6. Ghi file JSON xuống ổ cứng
        absolute_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
        
        return {"saved_order": payload}

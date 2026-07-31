# tools/travel_tools.py

def search_flight_ticket(route: str) -> str:
    """
    Tra cứu giá vé máy bay và lịch trình dựa trên tuyến đường cụ thể.
    """
    route_clean = route.lower()
    if "hà nội" in route_clean and "hồ chí minh" in route_clean:
        return "Vé máy bay Hà Nội - TP.HCM: Hãng VietJet - 1.200.000 VND (Bay lúc 08:00), Hãng Vietnam Airlines - 2.100.000 VND (Bay lúc 10:00)."
    elif "hà nội" in route_clean and "đà nẵng" in route_clean:
        return "Vé máy bay Hà Nội - Đà Nẵng: Hãng Bamboo Airways - 950.000 VND (Bay lúc 14:00)."
    return f"Không tìm thấy chuyến bay thẳng phù hợp cho tuyến đường: {route}."

def search_train_ticket(route: str) -> str:
    """
    Tra cứu giá vé và lịch trình tàu hỏa dựa trên tuyến đường cụ thể.
    """
    route_clean = route.lower()
    if "hà nội" in route_clean and "hồ chí minh" in route_clean:
        return "Vé tàu SE1 Hà Nội - Sài Gòn: Ghế mềm điều hòa - 850.000 VND (Khởi hành lúc 22:15)."
    elif "hà nội" in route_clean and "đà nẵng" in route_clean:
        return "Vé tàu SE5 Hà Nội - Đà Nẵng: Ghế giường nằm - 600.000 VND (Khởi hành lúc 09:00)."
    return f"Không tìm thấy chuyến tàu phù hợp cho tuyến đường: {route}."
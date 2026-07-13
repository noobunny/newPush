from datetime import date, datetime
from zhdate import ZhDate

# 法定节假日（农历日期）
LUNAR_LEGAL_HOLIDAYS = [
    (1, 1, "春节", 0),     # 正月初一
    (5, 5, "端午节", 0),   # 五月初五
    (8, 15, "中秋节", 0),  # 八月十五
]

# 传统节日（非法定，仅作为可能的参考）
LUNAR_TRADITIONAL = [
    (1, 15, "元宵节", 0),
    (7, 7, "七夕", 0),
    (9, 9, "重阳节", 0),
    (12, 30, "除夕", 0),   # 除夕可能29或30
    (12, 29, "除夕", 0),
]

# 法定节假日（公历日期）
SOLAR_LEGAL_HOLIDAYS = [
    (1, 1, "元旦"),
    (4, 5, "清明节"),     # 有时是4.4
    (5, 1, "劳动节"),
    (10, 1, "国庆节"),
]

# 非法定节日（不参与倒计时）
SOLAR_OTHER = [
    (2, 14, "情人节"),
    (3, 8, "妇女节"),
    (6, 1, "儿童节"),
    (12, 25, "圣诞节"),
]


def get_lunar_info(dt: date = None) -> dict:
    """获取农历信息"""
    dt = dt or date.today()
    try:
        dt_dt = datetime(dt.year, dt.month, dt.day)
        zhdate = ZhDate.from_datetime(dt_dt)
        return {
            "success": True,
            "lunar_month": zhdate.lunar_month,
            "lunar_day": zhdate.lunar_day,
            "lunar_year": zhdate.lunar_year,
            "lunar_chinese": str(zhdate),
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_next_holiday(dt: date = None, legal_only: bool = True) -> dict:
    """
    计算距离下一个节日还有多少天
    legal_only=True: 只计算法定节假日
    """
    dt = dt or date.today()
    today = dt
    best = None

    # 选择节日列表
    solar_list = SOLAR_LEGAL_HOLIDAYS if legal_only else SOLAR_LEGAL_HOLIDAYS + SOLAR_OTHER
    lunar_list = LUNAR_LEGAL_HOLIDAYS if legal_only else LUNAR_LEGAL_HOLIDAYS + LUNAR_TRADITIONAL

    # 检查未来 400 天内的节日
    for offset in range(0, 400):
        from datetime import timedelta
        check_date = today + timedelta(days=offset)

        # 农历节日（先检查，因为农历节日可能更近）
        for lm, ld, name, _ in lunar_list:
            try:
                h_date = ZhDate(check_date.year, lm, ld).to_datetime()
                holiday_date = h_date.date()
            except Exception:
                continue
            if check_date == holiday_date:
                cd_dt = datetime(check_date.year, check_date.month, check_date.day)
                week_str = ["一", "二", "三", "四", "五", "六", "日"][check_date.weekday()]
                candidate = {
                    "name": name,
                    "date": str(check_date),
                    "days_away": offset,
                    "weekday": f"星期{week_str}",
                    "lunar": str(ZhDate.from_datetime(cd_dt)),
                }
                if best is None or offset < best["days_away"]:
                    best = candidate

        # 公历节日（只有比已找到的更近才更新）
        for m, d, name in solar_list:
            if check_date.month == m and check_date.day == d:
                if best is None or offset < best["days_away"]:
                    cd_dt = datetime(check_date.year, check_date.month, check_date.day)
                    zh = ZhDate.from_datetime(cd_dt)
                    week_str = ["一", "二", "三", "四", "五", "六", "日"][check_date.weekday()]
                    best = {
                        "name": name,
                        "date": str(check_date),
                        "days_away": offset,
                        "weekday": f"星期{week_str}",
                        "lunar": str(zh),
                    }

        if best and best["days_away"] == 0:
            break  # 今天就是节日，直接返回

    return best
